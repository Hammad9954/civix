import streamlit as st
import ollama


MODEL = "llama3.2:3b"


SYSTEM_PROMPT = """

You are CivicSense AI, a general-purpose
AI assistant inside the CivicSense application.

You can answer normal questions and
civic-related questions.

IMPORTANT:

- Answer the user's CURRENT question directly.
- Do not assume they are reporting a pothole.
- Do not mention potholes unless the user asks.
- Do not invent what the user wants.
- If the user says hello, simply greet them.
- If the user asks a general question,
  answer it normally.
- If the user asks about civic issues,
  provide helpful civic guidance.
- Keep answers concise and natural.

"""


def civic_chatbot():

    st.title(
        "🤖 CivicSense AI"
    )

    st.caption(
        "Your local AI civic assistant"
    )

    if (
        "chat_history"
        not in st.session_state
    ):

        st.session_state.chat_history = []

    if st.button(
        "🗑️ Clear Chat"
    ):

        st.session_state.chat_history = []

        st.rerun()

    for message in (
        st.session_state.chat_history
    ):

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    prompt = st.chat_input(
        "Message CivicSense AI..."
    )

    if prompt:

        with st.chat_message(
            "user"
        ):

            st.markdown(
                prompt
            )

        st.session_state.chat_history.append({

            "role":
                "user",

            "content":
                prompt

        })

        with st.chat_message(
            "assistant"
        ):

            response_placeholder = (
                st.empty()
            )

            full_response = ""

            try:

                messages = [

                    {
                        "role":
                            "system",

                        "content":
                            SYSTEM_PROMPT
                    }

                ]

                messages.extend(
                    st.session_state.chat_history
                )

                stream = ollama.chat(

                    model=MODEL,

                    messages=messages,

                    stream=True

                )

                for chunk in stream:

                    token = (
                        chunk[
                            "message"
                        ][
                            "content"
                        ]
                    )

                    full_response += token

                    response_placeholder.markdown(
                        full_response + "▌"
                    )

                response_placeholder.markdown(
                    full_response
                )

            except Exception:

                full_response = (
                    "⚠️ I couldn't connect "
                    "to CivicSense AI. "
                    "Please make sure "
                    "Ollama is running."
                )

                response_placeholder.error(
                    full_response
                )

        st.session_state.chat_history.append({

            "role":
                "assistant",

            "content":
                full_response

        })