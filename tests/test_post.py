import unittest
from unittest.mock import patch, MagicMock
from blueskysocial.post import Post
from blueskysocial.api_endpoints import MENTION_TYPE, LINK_TYPE


class TestPost(unittest.TestCase):
    def test_init(self):
        content = "This is a test post"
        post = Post(content)
        self.assertEqual(post._post["text"], content)
        self.assertEqual(post._images, [])

    def test_init_with_images(self):
        content = "This is a test post"
        images = [MagicMock(), MagicMock()]
        post = Post(content, images)
        self.assertEqual(post._post["text"], content)
        self.assertEqual(post._images, images)

    def test_init_with_too_many_images(self):
        content = "This is a test post"
        images = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        with self.assertRaises(Exception):
            Post(content, images)

    def test_init_with_long_content(self):
        content = "a" * 301
        with self.assertRaises(Exception):
            Post(content)

    def test_add_languages(self):
        content = "This is a test post"
        languages = ["en", "fr"]
        post = Post(content)
        post.add_languages(languages)
        self.assertEqual(post._post["langs"], languages)

    @patch("requests.get")
    def test_parse_mentions(self, mock_get):
        content = "This is a test post with @mention1.bsky.social and @mention2.bsky.social"
        post = Post(content)
        mentions = post._parse_mentions()
        self.assertEqual(len(mentions), 2)
        self.assertEqual(mentions[0]["start"], 25)
        self.assertEqual(mentions[0]["end"], 25 + 21)
        self.assertEqual(mentions[0]["handle"], "mention1.bsky.social")
        self.assertEqual(mentions[1]["start"], 51)
        self.assertEqual(mentions[1]["end"], 51 + 21)
        self.assertEqual(mentions[1]["handle"], "mention2.bsky.social")

    @patch("requests.get")
    def test_parse_mentions_with_unresolved_handle(self, mock_get):
        content = "This is a test post with @unresolved_handle"
        mock_get.return_value.status_code = 400
        post = Post(content)
        mentions = post._parse_mentions()
        self.assertEqual(len(mentions), 0)

    @patch("requests.get")
    def test_parse_urls(self, mock_get):
        content = "This is a test post with a URL: https://example.com"
        post = Post(content)
        urls = post._parse_urls()
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["start"], 32)
        self.assertEqual(urls[0]["end"], 51)
        self.assertEqual(urls[0]["url"], "https://example.com")

    @patch("requests.get")
    def test_parse_urls_with_invalid_url(self, mock_get):
        content = "This is a test post with an invalid URL: https://example"
        post = Post(content)
        urls = post._parse_urls()
        self.assertEqual(len(urls), 0)

    @patch("requests.get")
    def test_parse_facets(self, mock_get):
        content = "This is a test post with @mention.bsky.social and a URL: https://example.com"
        mock_get.return_value.json.return_value = {"did": "1234567890"}
        post = Post(content)
        facets = post.parse_facets()
        self.assertEqual(len(facets), 2)
        self.assertEqual(facets[0]["index"]["byteStart"], 25)
        self.assertEqual(facets[0]["index"]["byteEnd"], 25 + 20)
        self.assertEqual(facets[0]["features"][0]["$type"], MENTION_TYPE)
        self.assertEqual(facets[0]["features"][0]["did"], "1234567890")
        self.assertEqual(facets[1]["index"]["byteStart"], 57)
        self.assertEqual(facets[1]["index"]["byteEnd"], 57 + 19)
        self.assertEqual(facets[1]["features"][0]["$type"], LINK_TYPE)
        self.assertEqual(facets[1]["features"][0]["uri"], "https://example.com")

    def test_build(self):
        content = "This is a test post"
        session = {"accessJwt": "access_token"}
        post = Post(content)
        built_post = post.build(session)
        self.assertEqual(built_post["text"], content)
        self.assertIn("createdAt", built_post)
        self.assertNotIn("facets", built_post)
        self.assertNotIn("embed", built_post)

    def test_build_with_images(self):
        content = "This is a test post"
        session = {"accessJwt": "access_token"}
        images = [MagicMock(), MagicMock()]
        post = Post(content, images)
        built_post = post.build(session)
        self.assertEqual(built_post["text"], content)
        self.assertIn("createdAt", built_post)
        self.assertNotIn("facets", built_post)
        self.assertIn("embed", built_post)
        self.assertEqual(len(built_post["embed"]["images"]), 2)


if __name__ == "__main__":
    unittest.main()
