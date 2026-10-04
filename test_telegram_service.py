"""
Unit tests for Telegram Service.
Tests configuration resolution, security redaction, and API interactions with mocks.
"""

import unittest
from unittest.mock import patch, MagicMock
from telegram_service import (
    get_telegram_config,
    is_telegram_configured,
    sanitize_telegram_error,
    send_telegram_message,
    PLACEHOLDER_TOKEN,
    PLACEHOLDER_CHAT_ID
)


class TestTelegramService(unittest.TestCase):

    def test_unconfigured_defaults(self):
        with patch("pathlib.Path.exists", return_value=False), \
             patch.dict("os.environ", {}, clear=True):
            token, chat_id = get_telegram_config()
            self.assertIsNone(token)
            self.assertIsNone(chat_id)
            self.assertFalse(is_telegram_configured())

    def test_ignores_placeholders(self):
        fake_secrets = {
            "TELEGRAM_BOT_TOKEN": PLACEHOLDER_TOKEN,
            "TELEGRAM_CHAT_ID": PLACEHOLDER_CHAT_ID
        }
        with patch("pathlib.Path.exists", return_value=True), \
             patch("tomllib.load", return_value=fake_secrets), \
             patch("builtins.open", unittest.mock.mock_open()):
            self.assertFalse(is_telegram_configured())

    def test_reads_valid_secrets(self):
        valid_secrets = {
            "TELEGRAM_BOT_TOKEN": "123456789:ABCdefGHIjklMNOpqr",
            "TELEGRAM_CHAT_ID": "987654321"
        }
        with patch("pathlib.Path.exists", return_value=True), \
             patch("tomllib.load", return_value=valid_secrets), \
             patch("builtins.open", unittest.mock.mock_open()):
            self.assertTrue(is_telegram_configured())
            token, chat_id = get_telegram_config()
            self.assertEqual(token, "123456789:ABCdefGHIjklMNOpqr")
            self.assertEqual(chat_id, "987654321")

    def test_sanitize_telegram_error(self):
        raw_token = "123456:SecretTokenABC"
        raw_error = f"Failed to connect to https://api.telegram.org/bot{raw_token}/sendMessage"
        sanitized = sanitize_telegram_error(raw_error, token=raw_token)
        self.assertNotIn(raw_token, sanitized)
        self.assertIn("[REDACTED_TOKEN]", sanitized)

    def test_send_message_missing_credentials(self):
        with patch("telegram_service.get_telegram_config", return_value=(None, None)):
            success, msg = send_telegram_message("Hello")
            self.assertFalse(success)
            self.assertIn("not configured", msg)

    def test_send_message_empty(self):
        success, msg = send_telegram_message("")
        self.assertFalse(success)
        self.assertIn("Cannot send an empty message", msg)

    @patch("requests.post")
    def test_send_message_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        success, msg = send_telegram_message(
            "Study summary content",
            bot_token="fake_token_123",
            chat_id="fake_chat_456"
        )
        self.assertTrue(success)
        self.assertIn("successfully", msg)
        mock_post.assert_called_once()
        called_json = mock_post.call_args[1]["json"]
        self.assertEqual(called_json["chat_id"], "fake_chat_456")
        self.assertEqual(called_json["text"], "Study summary content")

    @patch("requests.post")
    def test_markdown_fallback_on_parse_error(self, mock_post):
        # First call fails with 400 bad entity parse, second call succeeds
        mock_resp_fail = MagicMock()
        mock_resp_fail.status_code = 400
        mock_resp_fail.text = "Bad Request: can't parse entities in message"

        mock_resp_success = MagicMock()
        mock_resp_success.status_code = 200

        mock_post.side_effect = [mock_resp_fail, mock_resp_success]

        success, msg = send_telegram_message(
            "Summary with unclosed *asterisk",
            bot_token="fake_token_123",
            chat_id="fake_chat_456"
        )
        self.assertTrue(success)
        self.assertEqual(mock_post.call_count, 2)
        # Second call should not have parse_mode
        self.assertNotIn("parse_mode", mock_post.call_args_list[1][1]["json"])


if __name__ == "__main__":
    unittest.main()
