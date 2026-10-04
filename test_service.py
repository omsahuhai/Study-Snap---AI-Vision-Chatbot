"""
Unit tests for StudySnap Gemini Service Interactions API logic.
Tests components offline using mocks to verify API contract & input preparation.
"""

import unittest
import base64
from unittest.mock import MagicMock, patch
from gemini_service import (
    GeminiService,
    StudySnapChatSession,
    get_api_key,
    extract_text_from_interaction
)
from prompts import STUDYSNAP_SYSTEM_INSTRUCTION, DEFAULT_IMAGE_PROMPT


def create_mock_interaction(interaction_id: str, text: str):
    """Helper to build a mock Interaction object with model_output step."""
    mock_step = MagicMock()
    mock_step.type = "model_output"
    mock_content = MagicMock()
    mock_content.text = text
    mock_step.content = [mock_content]

    mock_interaction = MagicMock()
    mock_interaction.id = interaction_id
    mock_interaction.status = "completed"
    mock_interaction.steps = [mock_step]
    return mock_interaction


class TestStudySnapInteractionsCore(unittest.TestCase):

    def test_api_key_resolution(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-123"}):
            self.assertEqual(get_api_key(), "test-key-123")
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_api_key("param-key"), "param-key")

    def test_extract_text_from_interaction(self):
        interaction = create_mock_interaction("id-1", "Explanation of mitosis.")
        self.assertEqual(extract_text_from_interaction(interaction), "Explanation of mitosis.")

    def test_empty_message_error(self):
        mock_client = MagicMock()
        session = StudySnapChatSession(client=mock_client)
        with self.assertRaises(ValueError):
            session.send_message(text=None, image_bytes=None)

    def test_text_only_message(self):
        mock_client = MagicMock()
        mock_client.interactions.create.return_value = create_mock_interaction(
            "int-1", "Newton's second law is F = ma."
        )

        session = StudySnapChatSession(client=mock_client, model="gemini-3.8-flash")
        reply = session.send_message(text="What is Newton's second law?")

        self.assertEqual(reply, "Newton's second law is F = ma.")
        self.assertEqual(session.last_interaction_id, "int-1")
        mock_client.interactions.create.assert_called_once_with(
            model="gemini-3.8-flash",
            input="What is Newton's second law?",
            system_instruction=STUDYSNAP_SYSTEM_INSTRUCTION
        )

    def test_follow_up_uses_previous_interaction_id(self):
        mock_client = MagicMock()
        mock_client.interactions.create.side_effect = [
            create_mock_interaction("int-1", "Photosynthesis produces glucose and oxygen."),
            create_mock_interaction("int-2", "The main output gas is oxygen.")
        ]

        session = StudySnapChatSession(client=mock_client, model="gemini-3.8-flash")
        r1 = session.send_message(text="Explain photosynthesis.")
        r2 = session.send_message(text="What is the byproduct gas?")

        self.assertEqual(r1, "Photosynthesis produces glucose and oxygen.")
        self.assertEqual(r2, "The main output gas is oxygen.")
        self.assertEqual(session.last_interaction_id, "int-2")

        # Second call must pass previous_interaction_id
        second_call_kwargs = mock_client.interactions.create.call_args_list[1][1]
        self.assertEqual(second_call_kwargs["previous_interaction_id"], "int-1")
        self.assertEqual(second_call_kwargs["input"], "What is the byproduct gas?")

    def test_image_and_text_message(self):
        mock_client = MagicMock()
        mock_client.interactions.create.return_value = create_mock_interaction(
            "int-img-1", "This diagram illustrates cell mitosis."
        )

        session = StudySnapChatSession(client=mock_client)
        fake_bytes = b"\xff\xd8\xff\xe0fake_jpeg_bytes"
        reply = session.send_message(
            text="Explain this diagram",
            image_bytes=fake_bytes,
            mime_type="image/jpeg"
        )

        self.assertEqual(reply, "This diagram illustrates cell mitosis.")
        call_kwargs = mock_client.interactions.create.call_args[1]
        payload = call_kwargs["input"]
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0]["type"], "image")
        self.assertEqual(payload[0]["mime_type"], "image/jpeg")
        self.assertEqual(payload[0]["data"], base64.b64encode(fake_bytes).decode("utf-8"))
        self.assertEqual(payload[1]["type"], "text")
        self.assertEqual(payload[1]["text"], "Explain this diagram")

    def test_image_only_message_uses_default_prompt(self):
        mock_client = MagicMock()
        mock_client.interactions.create.return_value = create_mock_interaction(
            "int-img-2", "Analysis of the study note."
        )

        session = StudySnapChatSession(client=mock_client)
        fake_bytes = b"fake_png_bytes"
        reply = session.send_message(
            text=None,
            image_bytes=fake_bytes,
            mime_type="image/png"
        )

        self.assertEqual(reply, "Analysis of the study note.")
        call_kwargs = mock_client.interactions.create.call_args[1]
        payload = call_kwargs["input"]
        self.assertEqual(payload[1]["text"], DEFAULT_IMAGE_PROMPT)


if __name__ == "__main__":
    unittest.main()
