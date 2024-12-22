import unittest
from unittest.mock import MagicMock
from blueskysocial.convos.convo import Convo
import datetime as dt


class TestConvo(unittest.TestCase):

    def test_participant(self):
        raw_json = {"members": [{"handle": "user1"}, {"handle": "user2"}]}
        session = {"handle": "user1"}
        convo = Convo(raw_json, session)
        self.assertEqual(convo.participant, "user2")

    def test_participant_no_other_user(self):
        raw_json = {"members": [{"handle": "user1"}]}
        session = {"handle": "user1"}
        convo = Convo(raw_json, session)
        with self.assertRaises(StopIteration):
            convo.participant

    def test_participant_multiple_others(self):
        raw_json = {
            "members": [{"handle": "user1"}, {"handle": "user2"}, {"handle": "user3"}]
        }
        session = {"handle": "user1"}
        convo = Convo(raw_json, session)
        self.assertIn(convo.participant, ["user2", "user3"])

    def test_unread_count(self):
        raw_json = {"unreadCount": 5}
        session = {"handle": "user1"}
        convo = Convo(raw_json, session)
        self.assertEqual(convo.unread_count, 5)

    def test_opened(self):
        raw_json = {"opened": True}
        session = {"handle": "user1"}
        convo = Convo(raw_json, session)
        self.assertTrue(convo.opened)

    def test_convo_id(self):
        raw_json = {"id": "12345"}
        session = {"handle": "user1"}
        convo = Convo(raw_json, session)
        self.assertEqual(convo.convo_id, "12345")

    def test_last_message(self):
        raw_json = {"lastMessage": {"text": "Hello"}}
        session = {"handle": "user1"}
        convo = Convo(raw_json, session)
        self.assertEqual(convo.last_message, "Hello")

    def test_last_message_time(self):
        raw_json = {"lastMessage": {"sentAt": "2021-01-01T00:00:00.000Z"}}
        session = {"handle": "user1"}
        convo = Convo(raw_json, session)
        self.assertEqual(convo.last_message_time, dt.datetime(2021, 1, 1, 0, 0, 0, 0))

    def test_get_messages(self):
        raw_json = {
            "id": "12345",
            "members": [{"handle": "user1"}, {"handle": "user2"}],
            "unreadCount": 5,
            "opened": True,
            "lastMessage": {"text": "Hello", "sentAt": "2021-01-01T00:00:00.000Z"},
        }
        session = {"handle": "user1", "accessJwt": "fake_jwt"}
        convo = Convo(raw_json, session)

        messages_json = {
            "messages": [
                {"text": "Hello", "sentAt": "2021-01-01T00:00:00.000Z"},
                {"text": "Hi", "sentAt": "2021-01-01T01:00:00.000Z"},
            ]
        }

        with unittest.mock.patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = messages_json

            messages = convo.get_messages()

            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0].text, "Hello")
            self.assertEqual(messages[1].text, "Hi")

    def test_get_messages_with_filter(self):
        raw_json = {
            "id": "12345",
            "members": [{"handle": "user1"}, {"handle": "user2"}],
            "unreadCount": 5,
            "opened": True,
            "lastMessage": {"text": "Hello", "sentAt": "2021-01-01T00:00:00.000Z"},
        }
        session = {"handle": "user1", "accessJwt": "fake_jwt"}
        convo = Convo(raw_json, session)

        messages_json = {
            "messages": [
                {"text": "Hello", "sentAt": "2021-01-01T00:00:00.000Z"},
                {"text": "Hi", "sentAt": "2021-01-01T01:00:00.000Z"},
            ]
        }

        with unittest.mock.patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = messages_json

            def filter_func(message):
                return message.text == "Hi"

            messages = convo.get_messages(filter=filter_func)

            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].text, "Hi")
            mock_get.assert_called_with(
                "https://api.bsky.chat/xrpc/chat.bsky.convo.getMessages?convoId=12345",
                headers={"Authorization": "Bearer fake_jwt"},
            )

    def test_send_message(self):
        raw_json = {
            "id": "12345",
            "members": [{"handle": "user1"}, {"handle": "user2"}],
            "unreadCount": 5,
            "opened": True,
            "lastMessage": {"text": "Hello", "sentAt": "2021-01-01T00:00:00.000Z"},
        }
        session = {"handle": "user1", "accessJwt": "fake_jwt"}
        convo = Convo(raw_json, session)

        message_text = "New message"
        response_json = {"text": message_text, "sentAt": "2021-01-01T02:00:00.000Z"}

        with unittest.mock.patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = response_json

            message = convo.send_message(message_text)

            self.assertEqual(message.text, message_text)
            self.assertEqual(message.sent_at, dt.datetime(2021, 1, 1, 2, 0, 0, 0))
            mock_post.assert_called_with(
                "https://api.bsky.chat/xrpc/chat.bsky.convo.sendMessage",
                headers={"Authorization": "Bearer fake_jwt"},
                json={"convoId": "12345", "message": {"text": message_text}},
            )
