import unittest
from unittest.mock import patch, MagicMock
from blueskysocial.client import Client, Post
import requests


class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_access_token(self):
        self.client._session = {"accessJwt": "access_token"}
        self.assertEqual(self.client.access_token, "access_token")

    def test_did(self):
        self.client._session = {"did": "did"}
        self.assertEqual(self.client.did, "did")

    @patch("requests.post")
    def test_authenticate_success(self, mock_post):
        mock_post.return_value.json.return_value = {
            "accessJwt": "access_token",
            "did": "did",
        }
        self.client.authenticate("username", "password")
        self.assertEqual(self.client._session, {"accessJwt": "access_token", "did": "did"})

    @patch("requests.post")
    def test_authenticate_failure(self, mock_post):
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError("Error")
        with self.assertRaises(requests.HTTPError):
            self.client.authenticate("username", "password")

    @patch("requests.post")
    def test_post_success(self, mock_post):
        self.client._session = {"accessJwt": "access_token", "did": "did"}
        mock_post.return_value.json.return_value = {"response": "success"}
        with patch("blueskysocial.client.Post") as mock:
            mock.return_value = MagicMock()
            result = self.client.post(mock)
        self.assertEqual(result, {"response": "success"})

    def test_post_failure(self):
        with self.assertRaises(Exception):
            self.client.post(Post())


if __name__ == "__main__":
    unittest.main()
