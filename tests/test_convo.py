import unittest
from unittest.mock import patch, MagicMock
import datetime as dt
import requests
from blueskysocial.convos.convo import Convo
from blueskysocial.convos.message import DirectMessage


class TestConvo(unittest.TestCase):
    def setUp(self):
        # Create a mock session and raw conversation data
        self.mock_session = {"accessJwt": "mock_token", "handle": "user.bsky.social"}
        self.mock_raw_json = {
            "id": "mock_convo_id",
            "members": [
                {"handle": "user.bsky.social"},
                {"handle": "other.bsky.social"},
            ],
            "unreadCount": 5,
            "opened": True,
            "lastMessage": {
                "text": "Hello world!",
                "sentAt": "2023-01-01T12:00:00.000Z",
            },
        }
        self.convo = Convo(self.mock_raw_json, self.mock_session)

    def _generate_messages(self, count: int, start_idx: int = 0, cursor: str = None):
        # Helper to generate a list of mock messages
        data = {
            "messages": [
                {
                    "cid": f"cid_{i+start_idx}",
                    "text": f"message {i+start_idx}",
                    "createdAt": f"2023-01-01T00:00:{i+start_idx:02d}Z",
                }
                for i in range(count)
            ]
        }
        if cursor is not None:
            data["cursor"] = cursor
        return data

    # Test properties
    def test_participant_property(self):
        self.assertEqual(self.convo.participant, "other.bsky.social")

    def test_participant_property_multiple_members(self):
        # Test with multiple members (should return first non-self)
        multi_member_json = {
            "id": "group_convo",
            "members": [
                {"handle": "user.bsky.social"},
                {"handle": "alice.bsky.social"},
                {"handle": "bob.bsky.social"},
            ],
            "unreadCount": 0,
            "opened": True,
            "lastMessage": {"text": "test", "sentAt": "2023-01-01T12:00:00.000Z"},
        }
        group_convo = Convo(multi_member_json, self.mock_session)
        self.assertEqual(group_convo.participant, "alice.bsky.social")

    def test_unread_count_property(self):
        self.assertEqual(self.convo.unread_count, 5)

    def test_opened_property(self):
        self.assertTrue(self.convo.opened)

    def test_opened_property_false(self):
        unopened_json = self.mock_raw_json.copy()
        unopened_json["opened"] = False
        unopened_convo = Convo(unopened_json, self.mock_session)
        self.assertFalse(unopened_convo.opened)

    def test_convo_id_property(self):
        self.assertEqual(self.convo.convo_id, "mock_convo_id")

    def test_last_message_property(self):
        self.assertEqual(self.convo.last_message, "Hello world!")

    def test_last_message_time_property(self):
        expected_time = dt.datetime(2023, 1, 1, 12, 0, 0)
        self.assertEqual(self.convo.last_message_time, expected_time)

    # Test _raw_get_messages method
    @patch("requests.get")
    def test_raw_get_messages_without_cursor(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = self._generate_messages(3)
        mock_get.return_value = mock_response

        result = self.convo._raw_get_messages(limit=3)

        self.assertEqual(len(result["messages"]), 3)
        self.assertEqual(result["messages"][0]["text"], "message 0")
        mock_get.assert_called_once()
        # Verify URL construction
        args, kwargs = mock_get.call_args
        self.assertIn("convoId=mock_convo_id", args[0])
        self.assertIn("limit=3", args[0])
        self.assertNotIn("cursor=", args[0])

    @patch("requests.get")
    def test_raw_get_messages_with_cursor(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = self._generate_messages(3)
        mock_get.return_value = mock_response

        result = self.convo._raw_get_messages(limit=3, cursor="test_cursor")

        self.assertEqual(len(result["messages"]), 3)
        mock_get.assert_called_once()
        # Verify URL construction with cursor
        args, kwargs = mock_get.call_args
        self.assertIn("cursor=test_cursor", args[0])

    @patch("requests.get")
    def test_raw_get_messages_limit_capping(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = self._generate_messages(100)
        mock_get.return_value = mock_response

        # Test that limit is capped at 100
        self.convo._raw_get_messages(limit=150)

        args, kwargs = mock_get.call_args
        self.assertIn("limit=100", args[0])

    @patch("requests.get")
    def test_raw_get_messages_http_error(self, mock_get):
        mock_get.side_effect = requests.HTTPError("API Error")

        with self.assertRaises(requests.HTTPError):
            self.convo._raw_get_messages()

    # Test _raw_get_messages_paginated method
    @patch("blueskysocial.convos.convo.Convo._raw_get_messages")
    def test_raw_get_messages_paginated_single_page(self, mock_raw):
        # Test single page (no cursor in response)
        mock_raw.return_value = self._generate_messages(50)

        result = self.convo._raw_get_messages_paginated(limit=50)

        self.assertEqual(len(result), 50)
        mock_raw.assert_called_once_with(limit=50, cursor=None)

    @patch("blueskysocial.convos.convo.Convo._raw_get_messages")
    def test_raw_get_messages_paginated_multiple_pages(self, mock_raw):
        # Test multiple pages with recursion
        mock_raw.side_effect = [
            self._generate_messages(100, 0, "cursor1"),
            self._generate_messages(50, 100),  # No cursor in final response
        ]

        result = self.convo._raw_get_messages_paginated(limit=150)

        self.assertEqual(len(result), 150)
        self.assertEqual(mock_raw.call_count, 2)
        mock_raw.assert_any_call(limit=100, cursor=None)
        mock_raw.assert_any_call(limit=50, cursor="cursor1")

    @patch("blueskysocial.convos.convo.Convo._raw_get_messages")
    def test_raw_get_messages_paginated_exact_limit(self, mock_raw):
        # Test when we get exactly the limit requested
        mock_raw.side_effect = [
            self._generate_messages(100, 0, "cursor1"),
            self._generate_messages(100, 100),  # Exactly 200 total
        ]

        result = self.convo._raw_get_messages_paginated(limit=200)

        self.assertEqual(len(result), 200)
        self.assertEqual(mock_raw.call_count, 2)

    @patch("blueskysocial.convos.convo.Convo._raw_get_messages")
    def test_raw_get_messages_paginated_zero_limit(self, mock_raw):
        # Test zero limit
        result = self.convo._raw_get_messages_paginated(limit=0)

        self.assertEqual(len(result), 0)
        mock_raw.assert_not_called()

    @patch("blueskysocial.convos.convo.Convo._raw_get_messages")
    def test_raw_get_messages_paginated_negative_limit(self, mock_raw):
        # Test negative limit
        result = self.convo._raw_get_messages_paginated(limit=-10)

        self.assertEqual(len(result), 0)
        mock_raw.assert_not_called()

    @patch("blueskysocial.convos.convo.Convo._raw_get_messages")
    def test_raw_get_messages_paginated_partial_final_page(self, mock_raw):
        # Test when final page has fewer messages than batch limit
        mock_raw.side_effect = [
            self._generate_messages(100, 0, "cursor1"),
            self._generate_messages(30, 100),  # Final page with only 30 messages
        ]

        result = self.convo._raw_get_messages_paginated(limit=150)

        self.assertEqual(len(result), 130)  # 100 + 30
        self.assertEqual(mock_raw.call_count, 2)

    # Test get_messages method
    @patch("blueskysocial.convos.convo.Convo._raw_get_messages_paginated")
    def test_get_messages_no_filter(self, mock_paginated):
        mock_paginated.return_value = [
            {"text": "message 1", "sentAt": "2023-01-01T12:00:00.000Z"},
            {"text": "message 2", "sentAt": "2023-01-01T12:01:00.000Z"},
        ]

        messages = self.convo.get_messages(limit=50)

        self.assertEqual(len(messages), 2)
        self.assertIsInstance(messages[0], DirectMessage)
        mock_paginated.assert_called_once_with(limit=50)

    @patch("blueskysocial.convos.convo.Convo._raw_get_messages_paginated")
    def test_get_messages_with_filter(self, mock_paginated):
        mock_paginated.return_value = [
            {"text": "hello", "sentAt": "2023-01-01T12:00:00.000Z"},
            {"text": "world", "sentAt": "2023-01-01T12:01:00.000Z"},
            {"text": "hello again", "sentAt": "2023-01-01T12:02:00.000Z"},
        ]

        # Create a simple custom filter class for testing
        class HelloFilter:
            def __call__(self, msg):
                return "hello" in msg.text

        hello_filter = HelloFilter()
        messages = self.convo.get_messages(msg_filter=hello_filter, limit=50)

        self.assertEqual(len(messages), 2)
        self.assertIn("hello", messages[0].text)
        self.assertIn("hello", messages[1].text)

    @patch("blueskysocial.convos.convo.Convo._raw_get_messages_paginated")
    def test_get_messages_custom_limit(self, mock_paginated):
        mock_paginated.return_value = []

        self.convo.get_messages(limit=25)

        mock_paginated.assert_called_once_with(limit=25)

    # Test send_message method
    @patch("requests.post")
    def test_send_message_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "text": "Hello there!",
            "sentAt": "2023-01-01T12:30:00.000Z",
            "id": "msg_123",
        }
        mock_post.return_value = mock_response

        message = self.convo.send_message("Hello there!")

        self.assertIsInstance(message, DirectMessage)
        mock_post.assert_called_once()

        # Verify the request
        args, kwargs = mock_post.call_args
        self.assertIn("json", kwargs)
        self.assertEqual(kwargs["json"]["convoId"], "mock_convo_id")
        self.assertEqual(kwargs["json"]["message"]["text"], "Hello there!")

    @patch("requests.post")
    def test_send_message_http_error(self, mock_post):
        mock_post.side_effect = requests.HTTPError("Send failed")

        with self.assertRaises(requests.HTTPError):
            self.convo.send_message("Hello there!")

    @patch("requests.post")
    def test_send_message_with_auth_header(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "text": "test",
            "sentAt": "2023-01-01T12:00:00.000Z",
        }
        mock_post.return_value = mock_response

        self.convo.send_message("test message")

        # Verify auth header is included
        args, kwargs = mock_post.call_args
        self.assertIn("headers", kwargs)
        self.assertIn("Authorization", kwargs["headers"])

    # Edge cases and error handling
    def test_participant_no_other_members(self):
        # Edge case: only current user in members (shouldn't happen in practice)
        single_member_json = {
            "id": "solo_convo",
            "members": [{"handle": "user.bsky.social"}],
            "unreadCount": 0,
            "opened": True,
            "lastMessage": {"text": "test", "sentAt": "2023-01-01T12:00:00.000Z"},
        }
        solo_convo = Convo(single_member_json, self.mock_session)

        with self.assertRaises(StopIteration):
            _ = solo_convo.participant

    def test_last_message_time_invalid_format(self):
        invalid_time_json = self.mock_raw_json.copy()
        invalid_time_json["lastMessage"]["sentAt"] = "invalid-date-format"
        invalid_convo = Convo(invalid_time_json, self.mock_session)

        with self.assertRaises(ValueError):
            _ = invalid_convo.last_message_time


if __name__ == "__main__":
    unittest.main()
