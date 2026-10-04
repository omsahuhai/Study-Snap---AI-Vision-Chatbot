# 🎓 StudySnap — AI Vision Study Assistant

> **Understand anything you're studying.**  
> An intelligent, student-first study assistant powered by Google Gemini Vision & Chat and integrated with Telegram for revision notes.

---

## 📖 Overview

**StudySnap** helps students conquer difficult coursework by turning messy textbook pages, complex formulas, diagrams, and lecture notes into crystal-clear, step-by-step explanations. 

Built with the modern **Google GenAI Interactions API** (`gemini-3.8-flash`) and a custom, distraction-free **Streamlit** user interface, StudySnap supports multimodal multi-turn dialogues and exports structured study summaries directly to a student's **Telegram** chat for spaced revision on the go.

---

## ✨ Features

- **Multimodal Visual Reasoning**: Upload, stage, or drag-and-drop handwritten notes, textbook figures, circuit diagrams, and mathematical equations (PNG, JPG, JPEG, WEBP).
- **Multi-Turn Persistent Context**: Powered by Google's native Interactions API (`previous_interaction_id`), preserving follow-up discussion context seamlessly without bloated token accumulation.
- **Unified Input Composer**: Native file attachment button (`+`), high-contrast text area, and keyboard-first workflow designed to feel like modern AI products (ChatGPT, Claude).
- **One-Click Quick Starters**:
  - 💡 *Explain a concept*: High-level analogies and foundational walkthroughs.
  - 📸 *Solve from a photo*: Inline dropzone for textbook questions and diagrams.
  - 📝 *Help me revise*: Core formulas, key takeaways, and flashcard-style concepts.
- **Automated Telegram Study Summary**: Generates structured, concise takeaways from the current study session and delivers them directly to the student's Telegram device.
- **Zero Distraction UI**: Clean light-mode aesthetic (`#F8F9FC`), high-contrast typography (Inter), responsive design for both desktop and mobile viewports, and hidden platform clutter.

---

## 🛠️ Tech Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Frontend UI** | Streamlit (`>= 1.39.0`) | Interactive web application with custom CSS design system |
| **AI & Vision** | Google GenAI SDK (`google-genai >= 1.0.0`) | Model: `gemini-3.8-flash` via official Interactions API |
| **Image Processing** | Pillow (`PIL >= 10.0.0`) | Image verification and format standardisation |
| **Messaging** | Telegram Bot API | Direct HTTPS message delivery via Python standard library |
| **Configuration** | `python-dotenv` & Streamlit Secrets | Isolated environment and credentials management |
| **Testing** | `unittest` & `unittest.mock` | 100% offline-verifiable unit and integration test suites |

---

## 🏗️ Architecture & Clean Separation

StudySnap follows strict separation of concerns across service boundaries:

```
Study Snap - AI Vision Chatbot/
├── app.py                      # Streamlit frontend & UI session orchestration
├── gemini_service.py           # Google GenAI Interactions API client & chat session
├── telegram_service.py         # Telegram Bot API client & delivery service
├── prompts.py                  # System instruction & prompt templates
├── requirements.txt            # Reproducible, production-ready dependencies
├── test_service.py             # Offline unit tests for Gemini service
├── test_telegram_service.py    # Offline unit tests for Telegram integration
├── .streamlit/
│   ├── config.toml             # Theme & client configuration
│   ├── secrets.toml.example    # Credentials blueprint (safe for VCS)
│   └── secrets.toml            # Local secrets (strictly git-ignored)
├── .gitignore                  # Protection against credential leaks
└── README.md                   # Project documentation
```

### Key Modules:
- **`gemini_service.py`**: Encapsulates `GeminiService` and `StudySnapChatSession`. Manages authentication, base64 multimodal payload packaging, state tracking via `interaction.id`, and error propagation.
- **`telegram_service.py`**: Pure utility library using standard library `urllib` to send Markdown-formatted messages, split oversized messages at 4096-character boundaries, and parse credentials from Streamlit Secrets or environment variables.
- **`prompts.py`**: Central repository for `STUDYSNAP_SYSTEM_INSTRUCTION`, `STUDYSNAP_SUMMARY_PROMPT`, and default vision fallbacks.
- **`app.py`**: Thin presentation layer managing UI component state, staged image buffers, error toasts, and responsive rendering.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10, 3.11, or 3.12
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))
- Telegram Bot Token & Chat ID *(Optional, for summary delivery)*

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/your-username/Study-Snap---AI-Vision-Chatbot.git
cd "Study Snap - AI Vision Chatbot"

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

StudySnap reads credentials from `.streamlit/secrets.toml` or environment variables.

Copy the example blueprint:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:
```toml
# Gemini API Key (Required for AI responses)
GEMINI_API_KEY = "your-actual-gemini-api-key"

# Telegram Bot configuration (Required for summary delivery)
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
TELEGRAM_CHAT_ID = "your-telegram-chat-id"
```

> **Security Note:** `.streamlit/secrets.toml` is included in `.gitignore` and must **never** be checked into version control.

---

## 📱 Telegram Bot Setup Guide

To enable the **"📨 Send study summary"** feature:

1. **Create a Bot**:
   - Open Telegram and message [@BotFather](https://t.me/BotFather).
   - Send `/newbot`, choose a name and username (e.g., `MyStudySnapBot`).
   - Copy the HTTP API token provided by BotFather (this is your `TELEGRAM_BOT_TOKEN`).

2. **Obtain your Chat ID**:
   - Start a conversation with your newly created bot by clicking **Start**.
   - Message [@userinfobot](https://t.me/userinfobot) to get your numeric user ID (this is your `TELEGRAM_CHAT_ID`).

3. **Verify Connection**:
   - Add both values to `.streamlit/secrets.toml`.
   - The StudySnap sidebar will automatically display `● Telegram connected`.

---

## 💻 Running Locally

Start the Streamlit application:

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501`.

---

## 🧪 Testing

StudySnap includes a complete offline test suite with mocks, ensuring zero quota consumption during CI/CD or local validation:

```bash
# Test Gemini service & Interactions API state tracking
python3 -m unittest test_service.py

# Test Telegram messaging, token resolution & splitting
python3 -m unittest test_telegram_service.py
```

All 15 offline unit tests run in milliseconds without requiring active credentials or network calls.

---

## ☁️ Deployment Guide

### Deploying to Streamlit Community Cloud

1. **Push your code to GitHub**:
   Ensure `.streamlit/secrets.toml` and `.venv` remain untracked:
   ```bash
   git status
   git commit -am "Prepare StudySnap for deployment"
   git push origin main
   ```

2. **Connect to Streamlit Cloud**:
   - Navigate to [share.streamlit.io](https://share.streamlit.io).
   - Select **New app**, point to your repository, branch (`main`), and file path (`app.py`).

3. **Configure Cloud Secrets**:
   - In the Streamlit Cloud deployment dashboard, go to **Settings > Secrets**.
   - Paste your production credentials:
     ```toml
     GEMINI_API_KEY = "your-real-gemini-api-key"
     TELEGRAM_BOT_TOKEN = "your-real-telegram-bot-token"
     TELEGRAM_CHAT_ID = "your-real-telegram-chat-id"
     ```
   - Click **Save**. Streamlit will deploy automatically.

---

## 🔒 Security & Secrets Isolation

- **Zero Credential Exposure**: Real keys and tokens are never hardcoded or printed to stdout.
- **Fail-Safe Secret Resolution**: Secrets resolve safely through Streamlit Secrets with a fallback to `os.environ`.
- **Git Protection**: Strict ignore rules prevent accidental staging of `.env*`, `.venv/`, and `.streamlit/secrets.toml`.

---

## 📄 License

This project is built for educational and demonstration purposes. All rights reserved.