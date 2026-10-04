"""
Gemini Service layer for StudySnap.
Powered by the official Google GenAI Interactions API.
"""

import os
import base64
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google import genai
from prompts import STUDYSNAP_SYSTEM_INSTRUCTION, DEFAULT_IMAGE_PROMPT

# Default reliable multimodal model for conversational study assistance on Google GenAI Interactions API.
# (Can be overridden via GEMINI_MODEL env var, e.g. 'gemini-3.8-flash' when quota is available).
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


def get_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """
    Resolves the Gemini API key from explicit parameter, environment variables,
    or Streamlit secrets if available.
    """
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    # Environment variable check
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    # Streamlit secrets check
    secrets_path = Path(".streamlit/secrets.toml")
    if secrets_path.exists():
        try:
            import tomllib  # Python 3.11+
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
                key = secrets.get("GEMINI_API_KEY")
                if key and key.strip() and key != "your-gemini-api-key-here":
                    return key.strip()
        except Exception:
            pass

    return None


def extract_text_from_interaction(interaction: Any) -> str:
    """Extracts text content from interaction model_output steps."""
    texts: List[str] = []
    steps = getattr(interaction, "steps", None) or []
    for step in steps:
        step_type = getattr(step, "type", None)
        if step_type == "model_output":
            content_items = getattr(step, "content", None) or []
            for item in content_items:
                if hasattr(item, "text") and item.text:
                    texts.append(item.text)
                elif isinstance(item, dict) and item.get("text"):
                    texts.append(item["text"])
    return "\n\n".join(texts).strip()


class StudySnapChatSession:
    """
    Manages an ongoing multi-turn conversation session using Google GenAI Interactions API.
    Retains chat context via previous_interaction_id, supports text and multimodal (image) inputs.
    """

    def __init__(
        self,
        client: genai.Client,
        model: str = DEFAULT_MODEL,
        system_instruction: str = STUDYSNAP_SYSTEM_INSTRUCTION
    ):
        self.client = client
        self.model = model
        self.system_instruction = system_instruction
        self.last_interaction_id: Optional[str] = None
        self.history: List[Dict[str, Any]] = []

    def send_message(
        self,
        text: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = "image/jpeg"
    ) -> str:
        """
        Sends a message to the interaction session and returns the AI text response.
        Supports:
        1. Text-only message
        2. Image + text message
        3. Image-only message (defaults to DEFAULT_IMAGE_PROMPT)
        4. Follow-up questions (retains context via previous_interaction_id)
        """
        prompt_text = text.strip() if text and text.strip() else None

        if image_bytes:
            # Fall back to default prompt if no text provided for image
            if not prompt_text:
                prompt_text = DEFAULT_IMAGE_PROMPT

            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            input_payload = [
                {
                    "type": "image",
                    "data": b64_image,
                    "mime_type": mime_type or "image/jpeg"
                },
                {
                    "type": "text",
                    "text": prompt_text
                }
            ]
        elif prompt_text:
            input_payload = prompt_text
        else:
            raise ValueError("Cannot send an empty message. Provide text, an image, or both.")

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "input": input_payload,
        }

        if self.last_interaction_id:
            request_kwargs["previous_interaction_id"] = self.last_interaction_id
        else:
            request_kwargs["system_instruction"] = self.system_instruction

        interaction = self.client.interactions.create(**request_kwargs)

        # Update conversational state pointer
        self.last_interaction_id = getattr(interaction, "id", None)
        response_text = extract_text_from_interaction(interaction)

        # Store in local history for UI inspection
        self.history.append({
            "role": "user",
            "text": prompt_text,
            "has_image": bool(image_bytes),
            "interaction_id": self.last_interaction_id
        })
        self.history.append({
            "role": "model",
            "text": response_text,
            "interaction_id": self.last_interaction_id
        })

        return response_text

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the conversation history list."""
        return list(self.history)


class GeminiService:
    """
    Core reusable service managing the Gemini API client lifecycle.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = get_api_key(api_key)
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Please set the GEMINI_API_KEY environment variable "
                "or provide it in .streamlit/secrets.toml / .env."
            )
        self.model = model
        # Initialize the official GenAI client once
        self.client = genai.Client(api_key=self.api_key)
        # Avoid long hanging retries on quota exhaustion
        if hasattr(self.client, "interactions") and hasattr(self.client.interactions, "sdk_configuration"):
            self.client.interactions.sdk_configuration.retry_config = None

    def create_chat_session(
        self,
        system_instruction: str = STUDYSNAP_SYSTEM_INSTRUCTION
    ) -> StudySnapChatSession:
        """Creates and returns a new multi-turn conversational chat session."""
        return StudySnapChatSession(
            client=self.client,
            model=self.model,
            system_instruction=system_instruction
        )
