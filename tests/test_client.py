import unittest
from unittest.mock import patch, MagicMock
from blueskysocial.client import Client, Post
from blueskysocial.errors import SessionNotAuthenticatedError
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
        self.assertEqual(
            self.client._session, {"accessJwt": "access_token", "did": "did"}
        )

    @patch("requests.post")
    def test_authenticate_failure(self, mock_post):
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError(
            "Error"
        )
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

    @patch("requests.post")
    def test_post_reply_success(self, mock_post):
        self.client._session = {"accessJwt": "access_token", "did": "did"}
        mock_post.return_value.json.return_value = {"response": "success"}
        references = {
            "root": {"uri": "root_uri", "cid": "root_cid"},
            "parent": {"uri": "parent_uri", "cid": "parent_cid"},
        }
        with patch("blueskysocial.client.Post") as mock:
            mock.build.return_value = {"text": "content"}
            result = self.client.post_reply(mock, references)
        self.assertEqual(result, {"response": "success"})
        mock.build.assert_called_with(self.client._session)
        mock_post.assert_called_with(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": "Bearer access_token"},
            json={
                "repo": "did",
                "collection": "app.bsky.feed.post",
                "record": {"text": "content", "reply": references},
            },
            timeout=10,
        )

    def test_post_reply_missing_references(self):
        self.client._session = {"accessJwt": "access_token", "did": "did"}
        references = {
            "root": {"uri": "root_uri"},
            "parent": {"uri": "parent_uri"},
        }
        with patch("blueskysocial.client.Post") as mock:
            mock.return_value = MagicMock()
            with self.assertRaises(AssertionError):
                self.client.post_reply(mock, references)

    def test_post_reply_not_authenticated(self):
        references = {
            "root": {"uri": "root_uri", "cid": "root_cid"},
            "parent": {"uri": "parent_uri", "cid": "parent_cid"},
        }
        with patch("blueskysocial.client.Post") as mock:
            mock.return_value = MagicMock()
            with self.assertRaises(SessionNotAuthenticatedError):
                self.client.post_reply(mock, references)

    @patch.object(Client, "post")
    @patch.object(Client, "post_reply")
    @patch("blueskysocial.client.get_reply_refs")
    def test_post_thread_success(self, mock_get_refs, mock_post_reply, mock_post):
        self.client._session = {"accessJwt": "access_token", "did": "did"}
        posts = [MagicMock(), MagicMock()]
        mock_get_refs.return_value = {
            "root": {"uri": "root_uri", "cid": "root_cid"},
            "parent": {"uri": "parent_uri", "cid": "parent_cid"},
        }

        mock_post.return_value = {"uri": "uri1", "cid": "cid1"}
        mock_post_reply.return_value = {"uri": "uri2", "cid": "cid2"}
        result = self.client.post_thread(posts)
        self.assertEqual(
            result, [{"uri": "uri1", "cid": "cid1"}, {"uri": "uri2", "cid": "cid2"}]
        )
        mock_get_refs.assert_called_with(mock_post.return_value["uri"])
        mock_post.assert_called_with(posts[0])
        mock_post_reply.assert_called_with(posts[1], mock_get_refs.return_value)

    def test_post_thread_not_authenticated(self):
        posts = [MagicMock(), MagicMock()]
        with self.assertRaises(SessionNotAuthenticatedError):
            self.client.post_thread(posts)

    def test_post_thread_insufficient_posts(self):
        self.client._session = {"accessJwt": "access_token", "did": "did"}
        posts = [MagicMock()]
        with self.assertRaises(AssertionError):
            self.client.post_thread(posts)


if __name__ == "__main__":
    unittest.main()
