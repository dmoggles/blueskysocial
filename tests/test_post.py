from io import BytesIO
import unittest
from unittest.mock import patch, MagicMock
from blueskysocial.post import Post
from blueskysocial.errors import (
    PostTooLongError,
    TooManyImagesError,
    InvalidAttachmentsError,
)
from blueskysocial.api_endpoints import MENTION_TYPE, LINK_TYPE, HASHTAG_TYPE
from blueskysocial.image import Image
from blueskysocial.video import Video


class MockImage(Image):
    def build(self, session):
        return "image_blob"

    def _set_image(self, image_src: str | BytesIO) -> bytes:
        return b"mock_image_blob"


class MockVideo(Video):
    def build(self, session):
        return "video_blob"

    def _initialize(self):
        pass


class TestPost(unittest.TestCase):
    def test_init(self):
        content = "This is a test post"
        post = Post(content)
        self.assertEqual(post._post["text"], content)
        self.assertEqual(post.attachments, [])

    def test_init_with_images(self):
        content = "This is a test post"
        images = [MagicMock(spec=Image), MagicMock(spec=Image)]
        post = Post(content, images)
        self.assertEqual(post._post["text"], content)
        self.assertEqual(post.attachments, images)

    def test_init_with_too_many_images(self):
        content = "This is a test post"
        images = [MagicMock(spec=Image) for _ in range(6)]
        with self.assertRaises(TooManyImagesError):
            Post(content, with_attachments=images)

    def test_add_languages(self):
        content = "This is a test post"
        languages = ["en", "fr"]
        post = Post(content)
        post.add_languages(languages)
        self.assertEqual(post._post["langs"], languages)

    @patch("requests.get")
    def test_parse_mentions(self, mock_get):
        content = (
            "This is a test post with @mention1.bsky.social and @mention2.bsky.social"
        )
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

    @patch(
        "blueskysocial.image.get_image_aspect_ratio_spec",
        return_value={"width": 1, "height": 2},
    )
    def test_build_with_images(self, mock_get_image_aspect_ratio):
        content = "This is a test post"
        session = {"accessJwt": "access_token"}
        images = [
            MockImage("image_src1", "alt_text1"),
            MockImage("image_src2", "alt_text2"),
        ]
        post = Post(content, images)
        built_post = post.build(session)
        self.assertEqual(built_post["text"], content)
        self.assertIn("createdAt", built_post)
        self.assertNotIn("facets", built_post)
        self.assertIn("embed", built_post)
        self.assertEqual(len(built_post["embed"]["images"]), 2)
        self.assertEqual(built_post["embed"]["images"][0]["image"], "image_blob")
        self.assertEqual(built_post["embed"]["images"][0]["alt"], "alt_text1")
        self.assertEqual(
            built_post["embed"]["images"][0]["aspectRatio"], {"width": 1, "height": 2}
        )
        mock_get_image_aspect_ratio.assert_called_with(b"mock_image_blob")

    def test_build_with_video(self):
        content = "This is a test post"
        session = {"accessJwt": "access_token"}
        video = MockVideo("path/to/video.mp4")

        post = Post(content, with_attachments=video)
        built_post = post.build(session)
        self.assertEqual(built_post["text"], content)
        self.assertIn("createdAt", built_post)
        self.assertNotIn("facets", built_post)
        self.assertIn("embed", built_post)
        self.assertEqual(built_post["embed"]["video"], "video_blob")

    def test_build_with_images_and_video(self):
        content = "This is a test post"
        images = [MagicMock(spec=Image), MagicMock(spec=Image)]
        video = MagicMock(spec=Video)
        attachments = images + [video]
        with self.assertRaises(InvalidAttachmentsError):
            Post(content, attachments)

    def test_build_too_long_post(self):
        content = "This is a test post" * 1000
        session = {"accessJwt": "access_token"}
        post = Post(content)
        with self.assertRaises(PostTooLongError):
            post.build(session)

    def test_parse_hashtags(self):
        content = "This is a test post with #hashtag1 and #hashtag2"
        post = Post(content)
        hashtags = post._parse_hashtags()
        self.assertEqual(len(hashtags), 2)
        self.assertEqual(hashtags[0]["start"], 25)
        self.assertEqual(hashtags[0]["end"], 34)
        self.assertEqual(hashtags[0]["tag"], "hashtag1")
        self.assertEqual(hashtags[1]["start"], 39)
        self.assertEqual(hashtags[1]["end"], 48)
        self.assertEqual(hashtags[1]["tag"], "hashtag2")

    def test_parse_hashtags_with_special_characters(self):
        content = "This is a test post with #hashtag1! and #hashtag2?"
        post = Post(content)
        hashtags = post._parse_hashtags()
        self.assertEqual(len(hashtags), 2)
        self.assertEqual(hashtags[0]["start"], 25)
        self.assertEqual(hashtags[0]["end"], 34)
        self.assertEqual(hashtags[0]["tag"], "hashtag1")
        self.assertEqual(hashtags[1]["start"], 40)
        self.assertEqual(hashtags[1]["end"], 49)
        self.assertEqual(hashtags[1]["tag"], "hashtag2")

    def test_parse_hashtags_with_no_hashtags(self):
        content = "This is a test post with no hashtags"
        post = Post(content)
        hashtags = post._parse_hashtags()
        self.assertEqual(len(hashtags), 0)

    def test_parse_hashtags_with_only_special_characters(self):
        content = "This is a test post with #!@# and #$%^"
        post = Post(content)
        hashtags = post._parse_hashtags()
        self.assertEqual(len(hashtags), 0)

    def test_fancy_link_with_emoji(self):
        content = "loss 🎤 Site [Chelsea Football Club](https://www.chelseafc.com/en/video/maresca-on-3-1-loss-20-06-2025)"
        post = Post(content)
        facets = post.parse_facets()

        self.assertEqual(post.post["text"], "loss 🎤 Site Chelsea Football Club")
        self.assertEqual(len(facets), 1)
        self.assertEqual(facets[0]["features"][0]["$type"], LINK_TYPE)
        self.assertEqual(
            facets[0]["features"][0]["uri"],
            "https://www.chelseafc.com/en/video/maresca-on-3-1-loss-20-06-2025",
        )
        # The emoji 🎤 takes 4 bytes, so "Chelsea" starts at byte position 16, not 13
        self.assertEqual(facets[0]["index"]["byteStart"], 15)
        self.assertEqual(
            facets[0]["index"]["byteEnd"],
            15 + len("Chelsea Football Club".encode("utf-8")),
        )

    @patch("requests.get")
    def test_parse_mentions_with_emojis(self, mock_get):
        content = "Hello 🎉 @user.bsky.social 🎤 and @test.example.com 🚀"
        mock_get.return_value.json.return_value = {"did": "1234567890"}
        post = Post(content)
        mentions = post._parse_mentions()

        self.assertEqual(len(mentions), 2)
        # First mention should be correctly positioned after emoji
        self.assertEqual(
            post.post["text"], "Hello 🎉 @user.bsky.social 🎤 and @test.example.com 🚀"
        )
        # Check start/end positions for mentions
        self.assertEqual(mentions[0]["start"], 8)  # after 'Hello 🎉 '
        self.assertEqual(mentions[0]["end"], 25)  # end of '@user.bsky.social'
        self.assertEqual(mentions[0]["handle"], "user.bsky.social")
        self.assertEqual(mentions[1]["start"], 32)  # after '🎤 and '
        self.assertEqual(mentions[1]["end"], 49)  # end of '@test.example.com'
        self.assertEqual(mentions[1]["handle"], "test.example.com")

    def test_parse_hashtags_with_emojis(self):
        content = "Great game 🎉 #football 🎤 and #soccer ⚽"
        post = Post(content)
        hashtags = post._parse_hashtags()

        self.assertEqual(len(hashtags), 2)
        # First hashtag should be correctly positioned after emoji
        self.assertEqual(hashtags[0]["start"], 13)
        self.assertEqual(hashtags[0]["end"], 22)
        self.assertEqual(hashtags[0]["tag"], "football")
        # Second hashtag should be correctly positioned after multiple emojis
        self.assertEqual(hashtags[1]["start"], 29)
        self.assertEqual(hashtags[1]["end"], 36)
        self.assertEqual(hashtags[1]["tag"], "soccer")

    def test_parse_urls_with_emojis(self):
        content = "Check this out 🎉 https://example.com 🎤 and https://test.org ⚽"
        post = Post(content)
        urls = post._parse_urls()

        self.assertEqual(len(urls), 2)
        # First URL should be correctly positioned after emoji
        self.assertEqual(urls[0]["start"], 17)
        self.assertEqual(urls[0]["end"], 36)
        self.assertEqual(urls[0]["url"], "https://example.com")
        # Second URL should be correctly positioned after multiple emojis
        self.assertEqual(urls[1]["start"], 43)
        self.assertEqual(urls[1]["end"], 59)
        self.assertEqual(urls[1]["url"], "https://test.org")

    @patch("requests.get")
    def test_parse_facets_with_multiple_emojis_and_elements(self, mock_get):
        content = (
            "🎉 Amazing game! @user.bsky.social 🎤 #football ⚽ https://example.com 🚀"
        )
        mock_get.return_value.json.return_value = {"did": "1234567890"}
        post = Post(content)
        facets = post.parse_facets()

        # Should find mention, hashtag, and URL despite multiple emojis
        self.assertEqual(len(facets), 3)

        # Check mention facet
        mention_facet = next(
            f for f in facets if f["features"][0]["$type"] == MENTION_TYPE
        )
        self.assertEqual(
            mention_facet["index"]["byteStart"], 19
        )  # Position after "🎉 Amazing game! " (emoji is 4 bytes)
        self.assertEqual(
            mention_facet["index"]["byteEnd"], 36
        )  # End of "@user.bsky.social"

        # Check hashtag facet
        hashtag_facet = next(
            f for f in facets if f["features"][0]["$type"] == HASHTAG_TYPE
        )
        self.assertEqual(
            hashtag_facet["index"]["byteStart"], 42
        )  # Position after "@user.bsky.social 🎤 "
        self.assertEqual(hashtag_facet["index"]["byteEnd"], 51)  # End of "#football"

        # Check URL facet
        url_facet = next(f for f in facets if f["features"][0]["$type"] == LINK_TYPE)
        self.assertEqual(
            url_facet["index"]["byteStart"], 56
        )  # Position after "#football ⚽ "
        self.assertEqual(
            url_facet["index"]["byteEnd"], 75
        )  # End of "https://example.com"

    def test_rich_url_with_multiple_emojis(self):
        content = "🎉 Check out [Amazing Site 🎤](https://example.com) 🚀 More text ⚽"
        post = Post(content)
        post.parse_facets()

        # Text should be correctly processed with emojis preserved
        expected_text = "🎉 Check out Amazing Site 🎤 🚀 More text ⚽"
        self.assertEqual(post.post["text"], expected_text)


if __name__ == "__main__":
    unittest.main()
