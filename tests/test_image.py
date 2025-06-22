import unittest
from unittest.mock import patch, MagicMock, mock_open
from blueskysocial.api_endpoints import (
    RPC_SLUG,
    UPLOAD_BLOB,
)
from blueskysocial.image import Image, IMAGE_MIMETYPE
from io import BytesIO


class TestImage(unittest.TestCase):
    @patch("requests.get")
    def test_init_from_url(self, mock_get):
        url = "https://example.com/image.jpg"
        alt_text = "Example Image"
        image = Image(url, alt_text)

        self.assertEqual(image._alt_text, alt_text)
        self.assertIsNotNone(image._image)
        mock_get.assert_called_once_with(url)
        self.assertEqual(image._image, mock_get.return_value.content)

    @patch("builtins.open", new_callable=mock_open, read_data=b"example image data")
    def test_init_from_file(self, mock_open):
        file_path = "/path/to/image.jpg"
        alt_text = "Example Image"
        image = Image(file_path, alt_text)

        self.assertEqual(image._alt_text, alt_text)
        self.assertIsNotNone(image._image)
        mock_open.assert_called_once_with(file_path, "rb")
        self.assertEqual(image._image, b"example image data")

    def test_init_from_file_handle(self):
        file_handle = BytesIO(b"example image data")
        alt_text = "Example Image"
        image = Image(file_handle, alt_text)

        self.assertEqual(image._alt_text, alt_text)
        self.assertIsNotNone(image._image)
        self.assertEqual(image._image, b"example image data")

    @patch("requests.get")
    def test_get_image_from_url(self, mock_get):
        url = "https://example.com/image.jpg"
        image_data = b"example image data"
        mock_get.return_value.content = image_data
        image = Image(url, "alt text")

        mock_get.assert_called_once_with(url)
        self.assertEqual(image._image, image_data)

    @patch("builtins.open", new_callable=mock_open, read_data=b"example image data")
    def test_get_image_from_file(self, mock_open):
        file_path = "/path/to/image.jpg"
        image_data = b"example image data"
        image = Image(file_path, "alt text")
        mock_open.assert_called_once_with(file_path, "rb")
        self.assertEqual(image._image, image_data)

    def test_get_image_from_file_handle(self):
        file_handle = BytesIO(b"example image data")
        image = Image(file_handle, "alt text")
        self.assertEqual(image._image, b"example image data")

    @patch("requests.post")
    def test_build(self, mock_post):
        session = {"accessJwt": "access_token"}
        image_data = b"example image data"
        mock_post.return_value.json.return_value = {"blob": "uploaded_blob"}
        image = Image(MagicMock(), "alt text")
        image._image = image_data
        result = image.build(session)
        mock_post.assert_called_once_with(
            RPC_SLUG + UPLOAD_BLOB,
            headers={
                "Content-Type": IMAGE_MIMETYPE,
                "Authorization": "Bearer " + session["accessJwt"],
            },
            data=image_data,
        )
        self.assertEqual(result, "uploaded_blob")


if __name__ == "__main__":
    unittest.main()
