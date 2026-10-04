"""
StudySnap - AI Vision Chatbot
A Streamlit AI study assistant for questions, notes, and diagrams powered by Gemini.
"""

import streamlit as st
from PIL import Image
import io

from gemini_service import GeminiService, get_api_key
from prompts import DEFAULT_IMAGE_PROMPT
from telegram_service import is_telegram_configured, send_telegram_message

# 1. Page Configuration
st.set_page_config(
    page_title="StudySnap - AI Study Assistant",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Custom Styling for a polished, student-friendly interface
st.markdown(
    """
    <style>
    /* Clean student-focused typography and accents */
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.1rem;
    }
    .main-subtitle {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .study-tip {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 0.6rem 0.9rem;
        border-radius: 4px;
        margin-bottom: 0.8rem;
        font-size: 0.9rem;
        color: #334155;
    }
    /* Attachment preview styling */
    .attachment-card {
        background-color: #F1F5F9;
        border: 1px dashed #CBD5E1;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 3. Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "gemini_service" not in st.session_state:
    try:
        st.session_state.gemini_service = GeminiService()
    except Exception as e:
        st.session_state.gemini_service = None
        st.session_state.init_error = str(e)

if "chat_session" not in st.session_state and st.session_state.gemini_service:
    st.session_state.chat_session = st.session_state.gemini_service.create_chat_session()


def reset_conversation():
    """Resets the chat session and conversation history."""
    st.session_state.messages = []
    if st.session_state.gemini_service:
        st.session_state.chat_session = st.session_state.gemini_service.create_chat_session()


# 4. Sidebar: Navigation & Controls
with st.sidebar:
    st.markdown("### 🎓 StudySnap")
    st.caption("AI Study Companion")

    if st.session_state.gemini_service:
        st.success(f"⚡ Model: `{st.session_state.gemini_service.model}`", icon="✅")
    else:
        st.error("⚠️ Gemini API not connected", icon="❌")

    st.markdown("---")
    st.markdown("#### 💡 Study Tips")
    st.markdown(
        """
        <div class="study-tip">
            📸 <b>Snap & Ask:</b> Upload a picture of a textbook problem, diagram, or handwritten notes.
        </div>
        <div class="study-tip">
            💬 <b>Follow-ups:</b> Ask for simpler explanations, real-world examples, or practice problems.
        </div>
        <div class="study-tip">
            🧠 <b>Concept Check:</b> "Explain this concept like I'm 12" works wonders!
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("#### 📱 Telegram Delivery")
    
    telegram_ready = is_telegram_configured()
    if telegram_ready:
        st.caption("✅ Telegram connected")
    else:
        st.caption("ℹ️ Telegram not configured in secrets.toml")

    if st.button(
        "📨 Send Study Summary to Telegram",
        use_container_width=True,
        help="Generate and deliver a structured summary of this study session to your Telegram chat."
    ):
        if not st.session_state.messages:
            st.warning("⚠️ No study session to summarize yet! Ask a question or upload study notes first.")
        elif not telegram_ready:
            st.error("⚠️ Telegram is not configured! Please add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to `.streamlit/secrets.toml`.")
        else:
            with st.spinner("Generating summary and sending to Telegram..."):
                try:
                    summary_text = st.session_state.chat_session.generate_study_summary()
                    success, result_msg = send_telegram_message(summary_text)
                    if success:
                        st.success(f"✅ {result_msg}")
                    else:
                        st.error(f"❌ {result_msg}")
                except Exception as ex:
                    st.error(f"❌ Error generating summary: {ex}")

    st.markdown("---")
    if st.button("🗑️ Start New Session", use_container_width=True, help="Clear history and start fresh"):
        reset_conversation()
        st.rerun()


# 5. Header
st.markdown('<div class="main-title">StudySnap</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Your AI study assistant for questions, notes & diagrams.</div>',
    unsafe_allow_html=True
)

# Check API service availability
if not st.session_state.gemini_service:
    st.error(
        f"**Gemini Service Initialization Failed**\n\n"
        f"{st.session_state.get('init_error', 'Please configure your GEMINI_API_KEY.')}\n\n"
        f"Make sure you have set `GEMINI_API_KEY` in `.streamlit/secrets.toml` or your environment."
    )
    st.stop()


# 6. Image Attachment Section
with st.expander("📸 Attach Study Image / Notes (Optional)", expanded=False):
    uploaded_file = st.file_uploader(
        "Upload a diagram, textbook snippet, or study notes",
        type=["jpg", "jpeg", "png", "webp"],
        key="image_uploader"
    )
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(uploaded_file, caption="Attached Image", width=300)
        with col2:
            st.info("Image is ready! You can type a question below, or click below to analyze immediately.")
            if st.button("🔍 Explain / Solve this image", type="primary", use_container_width=True):
                # Process image-only query with default prompt
                image_bytes = uploaded_file.getvalue()
                mime_type = uploaded_file.type or "image/jpeg"

                st.session_state.messages.append({
                    "role": "user",
                    "text": DEFAULT_IMAGE_PROMPT,
                    "image_bytes": image_bytes
                })

                with st.spinner("StudySnap is analyzing your study material..."):
                    try:
                        ai_response = st.session_state.chat_session.send_message(
                            text=None,
                            image_bytes=image_bytes,
                            mime_type=mime_type
                        )
                        st.session_state.messages.append({
                            "role": "assistant",
                            "text": ai_response,
                            "image_bytes": None
                        })
                    except Exception as err:
                        st.error(f"⚠️ Error getting response: {err}")

                st.rerun()


# 7. Render Conversation History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image_bytes"):
            st.image(msg["image_bytes"], caption="Attached Study Material", width=320)
        if msg.get("text"):
            st.markdown(msg["text"])


# 8. Chat Input & Message Processing
user_prompt = st.chat_input("Ask a question about your study material, notes, or concept...")

if user_prompt:
    # Check if an image is currently uploaded in the expander
    image_bytes = None
    mime_type = None
    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "image/jpeg"

    # Display user turn
    st.session_state.messages.append({
        "role": "user",
        "text": user_prompt,
        "image_bytes": image_bytes
    })

    with st.chat_message("user"):
        if image_bytes:
            st.image(image_bytes, caption="Attached Study Material", width=320)
        st.markdown(user_prompt)

    # Generate assistant turn
    with st.chat_message("assistant"):
        with st.spinner("StudySnap is thinking..."):
            try:
                ai_response = st.session_state.chat_session.send_message(
                    text=user_prompt,
                    image_bytes=image_bytes,
                    mime_type=mime_type
                )
                st.markdown(ai_response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": ai_response,
                    "image_bytes": None
                })
            except Exception as err:
                error_msg = f"⚠️ Could not generate response: {err}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": error_msg,
                    "image_bytes": None
                })
