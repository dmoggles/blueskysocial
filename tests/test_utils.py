import unittest
from unittest.mock import Mock, patch, MagicMock
from blueskysocial.utils import (
    parse_uri,
    bs4_tag_extract_content,
    get_image_aspect_ratio_spec,
    get_video_aspect_ratio_spec,
    provide_aspect_ratio,
)
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from blueskysocial.typedefs import AspectRatioConsumerProtocol
from blueskysocial.errors import UnknownAspectRatioError


class TestParseUri(unittest.TestCase):
    def test_parse_uri_valid(self):
        uri = "at://example.com:repo/collection/rkey"
        expected_result = {
            "repo": "example.com:repo",
            "collection": "collection",
            "rkey": "rkey",
        }
        result = parse_uri(uri)
        self.assertEqual(result, expected_result)

    def test_parse_uri_invalid_format(self):
        uri = "at://example.com:repo/collection"
        with self.assertRaises(ValueError):
            parse_uri(uri)

    def test_parse_uri_empty_string(self):
        uri = ""
        with self.assertRaises(ValueError):
            parse_uri(uri)


class TestBs4TagExtractContent(unittest.TestCase):
    def test_extract_content_with_valid_tag(self):
        """Test extracting content from a valid tag with content attribute."""
        html = '<meta name="description" content="Test content">'
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("meta")

        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "Test content")

    def test_extract_content_with_empty_content(self):
        """Test extracting content from a tag with empty content attribute."""
        html = '<meta name="description" content="">'
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("meta")

        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "")

    def test_extract_content_with_none_tag(self):
        """Test extracting content when tag is None."""
        result = bs4_tag_extract_content(None)
        self.assertEqual(result, "")

    def test_extract_content_without_content_attribute(self):
        """Test extracting content from a tag without content attribute."""
        html = "<div>Some text</div>"
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("div")

        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "")

    def test_extract_content_with_numeric_content(self):
        """Test extracting numeric content from a tag."""
        html = '<meta name="count" content="123">'
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("meta")

        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "123")

    def test_extract_content_with_special_characters(self):
        """Test extracting content with special characters."""
        html = '<meta name="description" content="Test & content with <special> chars">'
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("meta")

        result = bs4_tag_extract_content(tag)
        self.assertEqual(result, "Test & content with <special> chars")


class TestGetImageAspectRatioSpec(unittest.TestCase):
    def _create_test_image(self, width: int, height: int, format: str = "PNG") -> bytes:
        """Helper method to create a test image with specified dimensions."""
        img = Image.new("RGB", (width, height), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format=format)
        return img_bytes.getvalue()

    def test_get_image_aspect_ratio_spec_square_image(self):
        """Test getting aspect ratio for a square image."""
        image_bytes = self._create_test_image(100, 100)
        result = get_image_aspect_ratio_spec(image_bytes)

        expected = {"width": 100, "height": 100}
        self.assertEqual(result, expected)

    def test_get_image_aspect_ratio_spec_landscape_image(self):
        """Test getting aspect ratio for a landscape image."""
        image_bytes = self._create_test_image(200, 100)
        result = get_image_aspect_ratio_spec(image_bytes)

        expected = {"width": 200, "height": 100}
        self.assertEqual(result, expected)

    def test_get_image_aspect_ratio_spec_portrait_image(self):
        """Test getting aspect ratio for a portrait image."""
        image_bytes = self._create_test_image(100, 200)
        result = get_image_aspect_ratio_spec(image_bytes)

        expected = {"width": 100, "height": 200}
        self.assertEqual(result, expected)

    def test_get_image_aspect_ratio_spec_large_image(self):
        """Test getting aspect ratio for a large image."""
        image_bytes = self._create_test_image(1920, 1080)
        result = get_image_aspect_ratio_spec(image_bytes)

        expected = {"width": 1920, "height": 1080}
        self.assertEqual(result, expected)

    def test_get_image_aspect_ratio_spec_jpeg_image(self):
        """Test getting aspect ratio for a JPEG image."""
        image_bytes = self._create_test_image(300, 150, "JPEG")
        result = get_image_aspect_ratio_spec(image_bytes)

        expected = {"width": 300, "height": 150}
        self.assertEqual(result, expected)


class TestGetVideoAspectRatioSpec(unittest.TestCase):
    """Test cases for get_video_aspect_ratio_spec function."""

    @patch("blueskysocial.utils.cv2")
    def test_get_video_aspect_ratio_spec_success(self, mock_cv2):
        """Test successful video aspect ratio extraction."""
        # Mock VideoCapture instance
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: (
            1920.0 if prop == mock_cv2.CAP_PROP_FRAME_WIDTH else 1080.0
        )
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4

        result = get_video_aspect_ratio_spec("test_video.mp4")

        self.assertEqual(result, {"width": 1920, "height": 1080})
        mock_cv2.VideoCapture.assert_called_once_with("test_video.mp4")
        mock_cap.isOpened.assert_called_once()
        mock_cap.release.assert_called_once()

    @patch("blueskysocial.utils.cv2")
    def test_get_video_aspect_ratio_spec_cannot_open(self, mock_cv2):
        """Test video that cannot be opened."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap

        result = get_video_aspect_ratio_spec("nonexistent_video.mp4")

        self.assertIsNone(result)
        mock_cv2.VideoCapture.assert_called_once_with("nonexistent_video.mp4")
        mock_cap.isOpened.assert_called_once()
        # release() should not be called because ValueError is raised before that line
        mock_cap.release.assert_not_called()

    @patch("blueskysocial.utils.cv2")
    def test_get_video_aspect_ratio_spec_exception(self, mock_cv2):
        """Test exception handling during video processing."""
        mock_cv2.VideoCapture.side_effect = Exception("Video processing error")

        result = get_video_aspect_ratio_spec("error_video.mp4")

        self.assertIsNone(result)
        mock_cv2.VideoCapture.assert_called_once_with("error_video.mp4")

    @patch("blueskysocial.utils.cv2")
    def test_get_video_aspect_ratio_spec_square_video(self, mock_cv2):
        """Test square video dimensions."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: 720.0
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4

        result = get_video_aspect_ratio_spec("square_video.mp4")

        self.assertEqual(result, {"width": 720, "height": 720})


class TestProvideAspectRatio(unittest.TestCase):
    """Test cases for provide_aspect_ratio function."""

    def test_provide_aspect_ratio_with_existing_ratio(self):
        """Test when aspect_ratio is already provided."""
        mock_consumer = Mock(spec=AspectRatioConsumerProtocol)
        mock_consumer.aspect_ratio = (1920, 1080)

        result = provide_aspect_ratio(mock_consumer)

        self.assertEqual(result, {"width": 1920, "height": 1080})
        # Should not call aspect_ratio_function when ratio is already provided
        mock_consumer.aspect_ratio_function.assert_not_called()

    def test_provide_aspect_ratio_with_function_success(self):
        """Test when aspect_ratio_function returns valid ratio."""
        mock_consumer = Mock(spec=AspectRatioConsumerProtocol)
        mock_consumer.aspect_ratio = None
        mock_consumer.aspect_ratio_function.return_value = {
            "width": 1280,
            "height": 720,
        }
        mock_consumer.require_aspect_ratio = False
        mock_consumer.data_accessor = b"mock_data"

        result = provide_aspect_ratio(mock_consumer)

        self.assertEqual(result, {"width": 1280, "height": 720})
        mock_consumer.aspect_ratio_function.assert_called_once_with(b"mock_data")

    def test_provide_aspect_ratio_function_returns_none_not_required(self):
        """Test when aspect_ratio_function returns None and ratio is not required."""
        mock_consumer = Mock(spec=AspectRatioConsumerProtocol)
        mock_consumer.aspect_ratio = None
        mock_consumer.aspect_ratio_function.return_value = None
        mock_consumer.require_aspect_ratio = False
        mock_consumer.data_accessor = b"mock_data"

        result = provide_aspect_ratio(mock_consumer)

        self.assertIsNone(result)
        mock_consumer.aspect_ratio_function.assert_called_once_with(b"mock_data")

    def test_provide_aspect_ratio_function_returns_none_required(self):
        """Test when aspect_ratio_function returns None and ratio is required."""
        mock_consumer = Mock(spec=AspectRatioConsumerProtocol)
        mock_consumer.aspect_ratio = None
        mock_consumer.aspect_ratio_function.return_value = None
        mock_consumer.require_aspect_ratio = True
        mock_consumer.data_accessor = b"mock_data"
        mock_consumer.__class__.__name__ = "TestConsumer"

        with self.assertRaises(UnknownAspectRatioError) as context:
            provide_aspect_ratio(mock_consumer)

        self.assertIn("aspect ratio could not be determined", str(context.exception))
        mock_consumer.aspect_ratio_function.assert_called_once_with(b"mock_data")

    def test_provide_aspect_ratio_with_tuple_aspect_ratio(self):
        """Test with different tuple values for aspect ratio."""
        mock_consumer = Mock(spec=AspectRatioConsumerProtocol)
        mock_consumer.aspect_ratio = (800, 600)

        result = provide_aspect_ratio(mock_consumer)

        self.assertEqual(result, {"width": 800, "height": 600})

    def test_provide_aspect_ratio_zero_dimensions(self):
        """Test with aspect ratio containing zero dimensions."""
        mock_consumer = Mock(spec=AspectRatioConsumerProtocol)
        mock_consumer.aspect_ratio = (0, 100)

        result = provide_aspect_ratio(mock_consumer)

        self.assertEqual(result, {"width": 0, "height": 100})


if __name__ == "__main__":
    unittest.main()
