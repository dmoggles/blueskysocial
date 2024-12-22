import unittest
from datetime import datetime
from blueskysocial.convos.message import DirectMessage
from unittest.mock import MagicMock


class TestDirectMessage(unittest.TestCase):
    def setUp(self):
        self.raw_json = {"text": "Hello, World!", "sentAt": "2023-10-01T12:34:56.789Z"}
        self.convo = MagicMock()
        self.message = DirectMessage(self.raw_json, self.convo)

    def test_text(self):
        self.assertEqual(self.message.text, "Hello, World!")

    def test_sent_at(self):
        expected_datetime = datetime.strptime(
            "2023-10-01T12:34:56.789Z", "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        self.assertEqual(self.message.sent_at, expected_datetime)

    def test_convo(self):
        self.assertEqual(self.message.convo, self.convo)


if __name__ == "__main__":

    unittest.main()
