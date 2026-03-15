import logging
import os
import speech_recognition as sr
import pyttsx3
from logger import setup_logging, get_logger

setup_logging("logs/app.log")
logger = get_logger(__name__)

class Voice:
    def __init__(self):
        try:
            self.tts_engine = pyttsx3.init()
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            logger.info("Voice system initialized (STT + TTS)")
        except Exception as e:
            logger.error(f"Voice init failed: {e}")
            self.tts_engine = self.recognizer = self.microphone = None

    def speak(self, text):
        if self.tts_engine is None:
            print(f"[TTS skipped] {text[:50]}...")
            return
        logger.info(f"TTS: {text[:100]}...")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self, prompt="Speak your goal:"):
        if self.microphone is None:
            return input(prompt + " (text fallback): ")
        print(prompt)
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
            text = self.recognizer.recognize_google(audio)
            logger.info(f"STT recognized: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning("STT: speech not understood")
            return self.listen(prompt)
        except sr.RequestError as e:
            logger.error(f"STT service error: {e}")
            return input(prompt + " (text fallback): ")
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""
