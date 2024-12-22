import unittest
from unittest.mock import patch, mock_open
from blueskysocial.video import Video, VIDEO_MIME_TYPES_FROM_EXTENTIONS
from blueskysocial.api_endpoints import UPLOAD_BLOB, RPC_SLUG


class TestVideo(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data=b"example video data")
    @patch("requests.post")
    def test_build(self, mock_post, mock_open):
        session = {"accessJwt": "access_token"}
        file_path = "/path/to/video.mp4"
        video_data = b"example video data"
        mock_post.return_value.json.return_value = {"blob": "uploaded_blob"}

        video = Video(file_path)
        result = video.build(session)

        mock_open.assert_called_once_with(file_path, "rb")
        mock_post.assert_called_once_with(
            RPC_SLUG + UPLOAD_BLOB,
            headers={
                "Authorization": f"Bearer {session['accessJwt']}",
                "Content-Type": VIDEO_MIME_TYPES_FROM_EXTENTIONS["mp4"],
            },
            data=video_data,
        )
        self.assertEqual(result, "uploaded_blob")

    @patch("builtins.open", new_callable=mock_open, read_data=b"example video data")
    @patch("requests.post")
    def test_build_unsupported_format(self, mock_post, mock_open):
        session = {"accessJwt": "access_token"}
        file_path = "/path/to/video.unsupported"
        video = Video(file_path)

        with self.assertRaises(Exception) as context:
            video.build(session)

        self.assertTrue("Unsupported video format" in str(context.exception))
        mock_open.assert_called_once_with(file_path, "rb")
        mock_post.assert_not_called()
