"""
StudySnap - AI Study Assistant
Premium modern AI study assistant frontend powered by Gemini and Telegram.
"""

import streamlit as st
import base64
from typing import Optional, Tuple

from gemini_service import GeminiService
from prompts import DEFAULT_IMAGE_PROMPT
from telegram_service import is_telegram_configured, send_telegram_message

# ── 1. Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudySnap — AI Study Companion",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ── 2. Design System & CSS ────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Google Fonts ─────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global Reset & Base ──────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Force clean modern canvas background */
    .stApp {
        background-color: #F8F9FC !important;
    }

    /* Hide Streamlit header clutter (Deploy button, toolbar actions, decoration, footer) */
    .stAppDeployButton, [data-testid="stAppDeployButton"], .stDeployButton, [data-testid="stToolbarActions"], #MainMenu, [data-testid="stDecoration"], footer {
        display: none !important;
        visibility: hidden !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.5rem !important;
        z-index: 99999 !important;
    }

    /* Ensure sidebar toggle buttons (expand & collapse) are always visible and styled */
    [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        visibility: visible !important;
    }
    [data-testid="stExpandSidebarButton"] button, [data-testid="stSidebarCollapseButton"] button {
        background: #FFFFFF !important;
        border: 1.5px solid #D0D5DD !important;
        border-radius: 8px !important;
        color: #344054 !important;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.08) !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stExpandSidebarButton"] button:hover, [data-testid="stSidebarCollapseButton"] button:hover {
        background: #F4F7FF !important;
        border-color: #3B5BDB !important;
        color: #2D4AC8 !important;
    }

    /* ── Sidebar ──────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #EAECF0 !important;
    }
    [data-testid="stSidebar"] * {
        color: #344054 !important;
    }
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0 16px 0;
        border-bottom: 1px solid #F2F4F7;
        margin-bottom: 16px;
    }
    .sidebar-logo-icon {
        font-size: 1.4rem;
        background: #EEF2FF;
        border-radius: 8px;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .sidebar-logo-text {
        font-size: 1.05rem;
        font-weight: 700;
        color: #101828 !important;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .sidebar-logo-sub {
        font-size: 0.72rem;
        color: #667085 !important;
        font-weight: 400;
    }

    /* Sidebar Primary Button: New Session */
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"],
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #3B5BDB !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        border-radius: 9px !important;
        padding: 0.55rem 1rem !important;
        box-shadow: 0 1px 3px rgba(59, 91, 219, 0.25) !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: #2D4AC8 !important;
        box-shadow: 0 3px 8px rgba(59, 91, 219, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* Sidebar Secondary Buttons */
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] .stButton > button[kind="secondary"],
    [data-testid="stSidebar"] .stButton > button:not([kind]) {
        background: #F9FAFB !important;
        color: #475467 !important;
        border: 1px solid #EAECF0 !important;
        font-size: 0.8rem !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
    [data-testid="stSidebar"] .stButton > button:not([kind]):hover {
        background: #F4F7FF !important;
        border-color: #D1D9F9 !important;
        color: #2D4AC8 !important;
    }

    /* Telegram Section */
    .sidebar-section-divider {
        height: 1px;
        background: #F2F4F7;
        margin: 24px 0 14px 0;
    }
    .sidebar-label {
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #98A2B3 !important;
        margin-bottom: 8px;
    }
    .tg-status {
        display: flex;
        align-items: center;
        gap: 7px;
        font-size: 0.76rem;
        color: #475467 !important;
        margin-bottom: 10px;
        padding: 4px 0;
    }
    .tg-dot {
        font-size: 0.55rem;
    }
    .tg-dot.ok {
        color: #12B76A !important;
    }
    .tg-dot.off {
        color: #98A2B3 !important;
    }

    /* ── Main Content Area ────────────────────────── */
    .block-container {
        padding-top: 1.75rem !important;
        padding-bottom: 6.5rem !important;
        max-width: 760px !important;
    }

    /* ── App Header ───────────────────────────────── */
    .app-header {
        padding: 0 0 0.85rem 0;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid #EAECF0;
    }
    .app-header-row {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .app-title {
        font-size: 1.45rem;
        font-weight: 700;
        color: #101828;
        letter-spacing: -0.025em;
        line-height: 1.2;
    }
    .app-badge {
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #3B5BDB;
        background: #EEF2FF;
        border-radius: 12px;
        padding: 2px 7px;
    }
    .app-subtitle {
        font-size: 0.88rem;
        color: #667085;
        margin-top: 3px;
        font-weight: 400;
    }

    /* ── Empty State ──────────────────────────────── */
    .empty-hero {
        text-align: center;
        padding: 4.5rem 1rem 1.5rem 1rem;
    }
    .empty-hero-icon {
        font-size: 2.2rem;
        margin-bottom: 0.75rem;
        display: inline-block;
    }
    .empty-hero-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #101828;
        letter-spacing: -0.03em;
        line-height: 1.25;
        margin-bottom: 0.5rem;
    }
    .empty-hero-sub {
        font-size: 0.92rem;
        color: #667085;
        line-height: 1.55;
        max-width: 480px;
        margin: 0 auto;
    }

    /* ── Starter Suggestion Pills ─────────────────── */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        height: auto !important;
        min-height: unset !important;
        padding: 0.6rem 1rem !important;
        border-radius: 999px !important;
        border: 1px solid #D0D5DD !important;
        background-color: #FFFFFF !important;
        color: #344054 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        text-align: center !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        box-shadow: 0 1px 2px rgba(16,24,40,0.04) !important;
        transition: all 0.15s ease !important;
        display: block !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"] .stButton > button:hover {
        border-color: #3B5BDB !important;
        background-color: #F4F7FF !important;
        color: #2D4AC8 !important;
        box-shadow: 0 3px 10px rgba(59,91,219,0.12) !important;
        transform: translateY(-1px) !important;
    }

    .starters-hint {
        text-align: center;
        font-size: 0.76rem;
        color: #98A2B3;
        margin-top: 1.25rem;
        letter-spacing: 0.01em;
    }

    /* ── Inline File Uploader Dropzone ────────────── */
    [data-testid="stFileUploader"] section {
        background: #FFFFFF !important;
        border: 1.5px dashed #B2CCFF !important;
        border-radius: 12px !important;
        padding: 0.85rem 1.25rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(16,24,40,0.04) !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: #3B5BDB !important;
        background: #F8FAFF !important;
    }

    /* ── Staged Attachment Chip ───────────────────── */
    .att-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #F4F7FF;
        border: 1px solid #C7D7F8;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 0.8rem;
        color: #344054;
        margin-bottom: 8px;
    }
    .att-chip-name {
        font-weight: 500;
        color: #101828;
        max-width: 260px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .att-chip-badge {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: #3B5BDB;
        color: #FFFFFF;
        padding: 1px 6px;
        border-radius: 4px;
        font-weight: 600;
    }

    /* ── Unified Composer & Bottom Bar ────────────── */
    [data-testid="stBottomBlockContainer"] {
        background: rgba(248, 249, 252, 0.95) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-top: 1px solid rgba(234, 236, 240, 0.8) !important;
        padding-top: 10px !important;
        padding-bottom: 14px !important;
    }

    [data-testid="stChatInput"] {
        background: #FFFFFF !important;
        border: 1.5px solid #D0D5DD !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px -2px rgba(16, 24, 40, 0.08), 0 2px 6px -1px rgba(16, 24, 40, 0.04) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #3B5BDB !important;
        box-shadow: 0 0 0 3px rgba(59, 91, 219, 0.12), 0 6px 24px -2px rgba(16, 24, 40, 0.1) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #101828 !important;
        font-size: 0.92rem !important;
        background: transparent !important;
        font-family: inherit !important;
        line-height: 1.45 !important;
        padding: 10px 12px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #98A2B3 !important;
        font-size: 0.88rem !important;
    }

    /* Composer File Upload Button (+) */
    [data-testid="stChatInputFileUploadButton"] button {
        background: #F2F4F7 !important;
        border: 1px solid #E4E7EC !important;
        border-radius: 8px !important;
        color: #475467 !important;
        padding: 5px !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stChatInputFileUploadButton"] button:hover {
        background: #EEF2FF !important;
        border-color: #C7D7F8 !important;
        color: #3B5BDB !important;
        transform: scale(1.05) !important;
    }

    /* Submit Button (↑) */
    [data-testid="stChatInputSubmitButton"] {
        border-radius: 8px !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stChatInputSubmitButton"]:not(:disabled) {
        background: #3B5BDB !important;
        color: #FFFFFF !important;
    }
    [data-testid="stChatInputSubmitButton"]:not(:disabled):hover {
        background: #2D4AC8 !important;
        transform: scale(1.05) !important;
    }
    [data-testid="stChatInputSubmitButton"]:disabled {
        background: #F2F4F7 !important;
        color: #C0C9D8 !important;
        border: 1px solid #EAECF0 !important;
    }

    /* ── Chat Messages ────────────────────────────── */
    div[data-testid="stChatMessage"] {
        background: transparent !important;
        border-bottom: 1px solid #F2F4F7;
        padding: 16px 0 !important;
    }

    /* ── API Error Banner ─────────────────────────── */
    .api-error-banner {
        background: #FFF3CD;
        border: 1px solid #F59E0B;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        color: #92400E;
        font-size: 0.88rem;
        line-height: 1.5;
        margin-bottom: 1rem;
    }

    /* ── Scrollbar ────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #D0D5DD; border-radius: 20px; }
    ::-webkit-scrollbar-thumb:hover { background: #98A2B3; }

    </style>
    """,
    unsafe_allow_html=True
)

# ── 3. Session State ──────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "attached_image" not in st.session_state:
    st.session_state.attached_image = None  # (bytes, mime_type, filename)

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "gemini_service" not in st.session_state:
    try:
        st.session_state.gemini_service = GeminiService()
    except Exception as e:
        st.session_state.gemini_service = None
        st.session_state.init_error = str(e)

if "chat_session" not in st.session_state and st.session_state.gemini_service:
    st.session_state.chat_session = st.session_state.gemini_service.create_chat_session()


def reset_conversation():
    """Resets the conversation and chat session."""
    st.session_state.messages = []
    st.session_state.attached_image = None
    st.session_state.pending_prompt = None
    if st.session_state.gemini_service:
        st.session_state.chat_session = st.session_state.gemini_service.create_chat_session()


# ── 4. Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="sidebar-logo-icon">🎓</div>
            <div>
                <div class="sidebar-logo-text">StudySnap</div>
                <div class="sidebar-logo-sub">AI Study Companion</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("＋ New Session", use_container_width=True, type="primary"):
        reset_conversation()
        st.rerun()

    # ── Telegram Section ──
    st.markdown('<div class="sidebar-section-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-label">Telegram Sync</div>', unsafe_allow_html=True)

    telegram_ready = is_telegram_configured()
    if telegram_ready:
        st.markdown(
            '<div class="tg-status"><span class="tg-dot ok">●</span> Telegram connected</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="tg-status"><span class="tg-dot off">○</span> Not configured</div>',
            unsafe_allow_html=True
        )

    if st.button("📨 Send study summary", use_container_width=True, type="secondary"):
        if not st.session_state.messages:
            st.warning("No study session to summarize yet.")
        elif not telegram_ready:
            st.error("Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .streamlit/secrets.toml.")
        else:
            with st.spinner("Generating & sending..."):
                try:
                    summary = st.session_state.chat_session.generate_study_summary()
                    success, msg = send_telegram_message(summary)
                    if success:
                        st.success("Delivered to Telegram ✓")
                    else:
                        st.error(f"Failed: {msg}")
                except Exception as ex:
                    st.error(f"Error: {ex}")

    # Clear conversation – only when there is history
    if st.session_state.messages:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Clear conversation", use_container_width=True, type="secondary"):
            reset_conversation()
            st.rerun()


# ── 5. App Header ─────────────────────────────────────────────────────────────
col_title, col_new_session = st.columns([4, 1.2])
with col_title:
    st.markdown(
        """
        <div class="app-header">
            <div class="app-header-row">
                <span class="app-title">StudySnap</span>
                <span class="app-badge">AI</span>
            </div>
            <div class="app-subtitle">Understand anything you're studying.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with col_new_session:
    st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)
    if st.button("＋ New Session", key="hdr_new_session", type="primary", use_container_width=True):
        reset_conversation()
        st.rerun()

# ── API error guard ────────────────────────────────────────────────────────────
if not st.session_state.gemini_service:
    st.markdown(
        f"""
        <div class="api-error-banner">
            <strong>Gemini API not configured</strong><br>
            {st.session_state.get('init_error', 'Please set GEMINI_API_KEY in .streamlit/secrets.toml or your environment.')}
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()


# ── 6. Empty State ─────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-hero">
            <div class="empty-hero-icon">🎓</div>
            <div class="empty-hero-title">What are you studying today?</div>
            <div class="empty-hero-sub">
                Ask a question, upload notes or a textbook photo, and get clear step-by-step explanations.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3 compact pill-style starter suggestions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💡 Explain a concept", key="starter_concept", use_container_width=True):
            st.session_state.pending_prompt = (
                "Explain a complex concept step by step with a clear real-world analogy."
            )
            st.rerun()
    with col2:
        if st.button("📸 Solve from a photo", key="starter_photo", use_container_width=True):
            st.session_state.show_photo_upload = not st.session_state.get("show_photo_upload", False)
            st.rerun()
    with col3:
        if st.button("📝 Help me revise", key="starter_revise", use_container_width=True):
            st.session_state.pending_prompt = (
                "Help me revise. Summarize the key formulas and core concepts I should know."
            )
            st.rerun()

    # Inline photo upload dropzone if activated
    if st.session_state.get("show_photo_upload"):
        st.markdown(
            '<div style="font-size:0.84rem; font-weight:600; color:#2D4AC8; text-align:center; margin: 1.25rem 0 0.5rem 0;">📸 Upload or drag &amp; drop study material, notes, or textbook diagram:</div>',
            unsafe_allow_html=True
        )
        photo_uploader = st.file_uploader(
            "Choose a study image",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
            key="inline_photo_uploader"
        )
        if photo_uploader:
            st.session_state.attached_image = (
                photo_uploader.getvalue(),
                photo_uploader.type or "image/jpeg",
                photo_uploader.name
            )
            st.session_state.show_photo_upload = False
            st.rerun()

    st.markdown(
        '<div class="starters-hint">💡 Tip: Type a question below, or use the <b>+</b> button in the composer to attach a photo or notes</div>',
        unsafe_allow_html=True
    )

# ── 7. Conversation History ────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image_bytes"):
            st.image(msg["image_bytes"], caption="Study Material", width=260)
        if msg.get("text"):
            st.markdown(msg["text"])


# ── 8. Unified Composer Area ──────────────────────────────────────────────────
# Attachment chip – shows when an image is staged
if st.session_state.attached_image:
    img_bytes, mime, filename = st.session_state.attached_image
    c_chip, c_del = st.columns([5, 1])
    with c_chip:
        st.markdown(
            f"""
            <div class="att-chip">
                <span>📎</span>
                <span class="att-chip-name">{filename}</span>
                <span class="att-chip-badge">Ready to send</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c_del:
        if st.button("✕", key="remove_staged_img", help="Remove image"):
            st.session_state.attached_image = None
            st.rerun()

# Unified Chat Input Composer (Streamlit native + button for files)
composer_input = st.chat_input(
    placeholder="Ask a question about your study material (+ to attach photo)...",
    accept_file=True,
    file_type=["png", "jpg", "jpeg", "webp"]
)


# ── 9. Message Processing ──────────────────────────────────────────────────────
incoming_text = None
incoming_image_bytes = None
incoming_mime_type = None

if st.session_state.pending_prompt:
    incoming_text = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
elif composer_input:
    if hasattr(composer_input, "text"):
        incoming_text = composer_input.text.strip() if composer_input.text else None
        if hasattr(composer_input, "files") and composer_input.files:
            file_obj = composer_input.files[0]
            incoming_image_bytes = file_obj.getvalue()
            incoming_mime_type = file_obj.type or "image/jpeg"
    elif isinstance(composer_input, str):
        incoming_text = composer_input.strip()

# Consume staged image
if not incoming_image_bytes and st.session_state.attached_image:
    incoming_image_bytes, incoming_mime_type, _ = st.session_state.attached_image
    st.session_state.attached_image = None

if incoming_text or incoming_image_bytes:
    prompt_for_gemini = incoming_text
    display_user_text = incoming_text or "Please analyse this study material and explain the key concepts."

    st.session_state.messages.append({
        "role": "user",
        "text": display_user_text,
        "image_bytes": incoming_image_bytes
    })

    with st.chat_message("user"):
        if incoming_image_bytes:
            st.image(incoming_image_bytes, caption="Study Material", width=260)
        st.markdown(display_user_text)

    with st.chat_message("assistant"):
        with st.spinner("StudySnap is thinking…"):
            try:
                ai_response = st.session_state.chat_session.send_message(
                    text=prompt_for_gemini,
                    image_bytes=incoming_image_bytes,
                    mime_type=incoming_mime_type
                )
                st.markdown(ai_response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": ai_response,
                    "image_bytes": None
                })
            except Exception as err:
                error_msg = f"⚠️ Could not generate a response: {err}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": error_msg,
                    "image_bytes": None
                })
    st.rerun()
