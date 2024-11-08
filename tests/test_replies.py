import unittest
from unittest.mock import patch, MagicMock, call
from blueskysocial.replies import get_reply_refs, RPC_SLUG
import requests


class TestGetReplyRefs(unittest.TestCase):
    @patch("blueskysocial.replies.requests.get")
    def test_get_reply_refs_top_level_post(self, mock_get):
        parent_uri = "at://example.com:repo/collection/rkey"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "uri": parent_uri,
            "cid": "parent_cid",
            "value": {},
        }
        mock_get.return_value = mock_response

        result = get_reply_refs(parent_uri)
        self.assertEqual(result["root"]["uri"], parent_uri)
        self.assertEqual(result["root"]["cid"], "parent_cid")
        self.assertEqual(result["parent"]["uri"], parent_uri)
        self.assertEqual(result["parent"]["cid"], "parent_cid")
        mock_get.assert_called_once_with(
            f"{RPC_SLUG}com.atproto.repo.getRecord",
            params={
                "repo": "example.com:repo",
                "collection": "collection",
                "rkey": "rkey",
            },
            timeout=10,
        )

    @patch("blueskysocial.replies.requests.get")
    def test_get_reply_refs_reply_post(self, mock_get):
        parent_uri = "at://example.com:repo/collection/rkey"
        root_uri = "at://example.com:repo/collection/root_rkey"
        mock_response_parent = MagicMock()
        mock_response_parent.json.return_value = {
            "uri": parent_uri,
            "cid": "parent_cid",
            "value": {"reply": {"root": {"uri": root_uri}}},
        }
        mock_response_root = MagicMock()
        mock_response_root.json.return_value = {"uri": root_uri, "cid": "root_cid"}
        mock_get.side_effect = [mock_response_parent, mock_response_root]

        result = get_reply_refs(parent_uri)
        self.assertEqual(result["root"]["uri"], root_uri)
        self.assertEqual(result["root"]["cid"], "root_cid")
        self.assertEqual(result["parent"]["uri"], parent_uri)
        self.assertEqual(result["parent"]["cid"], "parent_cid")
        mock_get.assert_has_calls(
            [
                call(
                    f"{RPC_SLUG}com.atproto.repo.getRecord",
                    params={
                        "repo": "example.com:repo",
                        "collection": "collection",
                        "rkey": "rkey",
                    },
                    timeout=10,
                ),
                call(
                    f"{RPC_SLUG}com.atproto.repo.getRecord",
                    params={
                        "repo": "example.com:repo",
                        "collection": "collection",
                        "rkey": "root_rkey",
                    },
                    timeout=10,
                ),
            ]
        )

    @patch("blueskysocial.replies.requests.get")
    def test_get_reply_refs_http_error(self, mock_get):
        parent_uri = "at://example.com/repo/collection/rkey"
        mock_get.side_effect = requests.exceptions.HTTPError

        with self.assertRaises(requests.exceptions.HTTPError):
            get_reply_refs(parent_uri)


if __name__ == "__main__":
    unittest.main()
