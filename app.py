import streamlit as st
import sys
import io
from pathlib import Path
from dotenv import load_dotenv
from agent import Agent
from logger import setup_logging

load_dotenv()
setup_logging()

st.set_page_config(page_title="Grok Agent", page_icon="🤖")
st.title("🤖 Grok Agent Chat UI")
st.markdown("Autonomous coding agent with powerful tools. Give it goals or coding tasks!")

# Work dir
target_dir = Path.cwd().resolve()
st.sidebar.info(f"**Working directory:** `{target_dir}`")

# Initialize agent
@st.cache_resource
def get_agent():
    return Agent(target_dir=target_dir)

agent = get_agent()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("What should the agent do? (e.g., 'Create a Streamlit app for chat UI')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent working... (tools may be used)"):
            # Capture stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            captured_output = io.StringIO()
            sys.stdout = captured_output
            sys.stderr = captured_output

            try:
                agent.run(prompt, max_steps=100)
                response = captured_output.getvalue()
            except Exception as e:
                response = f"**Error:** {str(e)}"
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        # Display response with some formatting
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar actions
with st.sidebar:
    st.button("🗑️ Clear Chat", on_click=lambda: setattr(st.session_state, 'messages', []))
    st.markdown("---")
    st.info("💡 **Tips:**\n- Agent uses tools like `run_shell`, `write_file`\n- Runs up to 100 steps\n- Output shows tool calls & final result")
