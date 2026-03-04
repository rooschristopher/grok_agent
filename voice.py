import asyncio
import json
import os
import base64
import logging
import numpy as np
import sounddevice as sd
import websockets
import dotenv
from pynput import keyboard
from logger import setup_logging, get_logger

# Load environment variables
setup_logging("app.log")
logger = get_logger(__name__)

dotenv.load_dotenv()
XAI_API_KEY = os.getenv("VOICE_TESTING_KEY")
WS_URL = "wss://api.x.ai/v1/realtime"
logger.info("Voice module initialized. WS_URL=%s", WS_URL)

# --- Audio Configuration ---
MIC_RATE = 16000
XAI_RATE = 24000
CHANNELS = 1
GAIN = 10.0

# --- State ---
is_talking = False
active_keys = set()
PTT_COMBINATION = {keyboard.Key.ctrl_l, keyboard.Key.enter}
ws_connection = None

input_queue = asyncio.Queue()
playback_buffer = bytearray()

# ---------------------------------------------------------
# Helper: Force Server to Respond
# ---------------------------------------------------------
async def trigger_response():
    """Forces the server to stop waiting and generate a response."""
    global ws_connection
    if ws_connection:
        try:
            await ws_connection.send(json.dumps({"type": "response.create"}))
        except Exception as e:
            print(f"Trigger Error: {e}")

# ---------------------------------------------------------
# Keyboard Listener (Push-to-Talk)
# ---------------------------------------------------------
def on_press(key):
    global is_talking
    active_keys.add(key)
    if all(k in active_keys for k in PTT_COMBINATION):
        if not is_talking:
            is_talking = True
            print("\n\033[91m● RECORDING...\033[0m")

def on_release(key):
    global is_talking
    if key in active_keys:
        active_keys.remove(key)

    if any(k not in active_keys for k in PTT_COMBINATION):
        if is_talking:
            is_talking = False
            print("\r\033[90m○ Muted - Requesting AI Response...\033[0m", end="")
            # Signal the async loop to send a response.create event
            asyncio.run_coroutine_threadsafe(trigger_response(), loop)

# Start keyboard listener
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

# ---------------------------------------------------------
# Audio Callbacks
# ---------------------------------------------------------
def input_callback(indata, frames, time, status):
    if is_talking:
        loop.call_soon_threadsafe(input_queue.put_nowait, indata.copy())

def output_callback(outdata, frames, time, status):
    global playback_buffer
    bytes_needed = frames * 4 * CHANNELS
    if len(playback_buffer) >= bytes_needed:
        data_to_play = playback_buffer[:bytes_needed]
        playback_buffer = playback_buffer[bytes_needed:]
        outdata[:] = np.frombuffer(data_to_play, dtype=np.float32).reshape(outdata.shape)
    else:
        outdata.fill(0)

# ---------------------------------------------------------
# Tasks
# ---------------------------------------------------------
async def send_audio(ws):
    while True:
        chunk = await input_queue.get()
        # Gain + Resample
        boosted = (chunk * GAIN).clip(-1, 1)
        original_indices = np.arange(len(boosted))
        new_indices = np.linspace(0, len(boosted) - 1, int(len(boosted) * XAI_RATE / MIC_RATE))
        resampled = np.interp(new_indices, original_indices, boosted.flatten())

        pcm_int16 = (resampled * 32767).astype(np.int16)
        b64 = base64.b64encode(pcm_int16.tobytes()).decode('utf-8')
        await ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": b64}))

async def handle_events(ws):
    global playback_buffer
    while True:
        try:
            msg = await ws.recv()
            data = json.loads(msg)
            etype = data.get("type")

            if etype == "response.output_audio.delta":
                audio_bytes = base64.b64decode(data["delta"])
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32767.0
                playback_buffer.extend(audio_array.tobytes())

            elif etype == "conversation.item.input_audio_transcription.completed":
                print(f"\n\033[94m[You]:\033[0m {data.get('transcript')}")

            elif etype == "response.output_audio_transcript.delta":
                print(f"\033[95m[AI]:\033[0m {data.get('delta')}", end="", flush=True)

            elif etype == "response.done":
                print("\n\033[90m--- Turn Finished ---\033[0m")

            elif etype == "error":
                print(f"\n\033[91m[Error]:\033[0m {data.get('error')}")

        except websockets.exceptions.ConnectionClosed:
            break

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
async def main():
    global loop, ws_connection
    loop = asyncio.get_running_loop()
    headers = {"Authorization": f"Bearer {XAI_API_KEY}"}

    in_stream = sd.InputStream(samplerate=MIC_RATE, channels=CHANNELS, callback=input_callback)
    out_stream = sd.OutputStream(samplerate=XAI_RATE, channels=CHANNELS, callback=output_callback)

    with in_stream, out_stream:
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            ws_connection = ws  # Store globally for trigger_response
            print("\n\033[92m● SYSTEM ONLINE\033[0m - Hold \033[1mCtrl + Enter\033[0m to speak.")

            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "voice": "Ara",
                    "instructions": "You are a helpful assistant.",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {"type": "server_vad"},
                    "audio": {
                        "input": {"format": {"type": "audio/pcm", "rate": XAI_RATE}},
                        "output": {"format": {"type": "audio/pcm", "rate": XAI_RATE}}
                    }
                }
            }))

            await asyncio.gather(send_audio(ws), handle_events(ws))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        listener.stop()
        print("\n\033[93mSession Stopped.\033[0m")