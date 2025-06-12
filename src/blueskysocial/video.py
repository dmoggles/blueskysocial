import requests
from blueskysocial.api_endpoints import UPLOAD_BLOB, RPC_SLUG, VIDEO_TYPE
from blueskysocial.post_attachment import PostAttachment
from blueskysocial.utils import get_auth_header

VIDEO_MIME_TYPES_FROM_EXTENTIONS = {
    "mp4": "video/mp4",
    "mpeg": "video/mpeg",
    "webm": "video/webm",
    "mov": "video/quicktime",
}


class Video(PostAttachment):
    """
    A class used to represent a Video and handle its upload process.
    Attributes
    ----------
    path : str
        The file path of the video to be uploaded.
    _upload_blob : dict or None
        The response from the upload request, initially set to None.
    Methods
    -------
    build(session: dict) -> dict
        Reads the video file, determines its MIME type, uploads it to the server,
        and returns the blob information from the server response.
    """

    def __init__(self, path: str, alt_text: str = ""):
        self._path = path
        self._upload_blob = None
        self._alt_text = alt_text

    def attach_to_post(self, post, session):
        post.post["embed"] = {"$type": VIDEO_TYPE, "video": self.build(session), "alt": self.alt_text}

    def build(self, session: dict) -> dict:
        if self._upload_blob is None:
            with open(self._path, "rb") as file:
                stream = file.read()

            try:
                mime_type = VIDEO_MIME_TYPES_FROM_EXTENTIONS[self._path.split(".")[-1]]
            except KeyError:
                raise Exception("Unsupported video format")
            access_token = session["accessJwt"]
            headers = get_auth_header(access_token)
            headers["Content-Type"] = mime_type
            resp = requests.post(
                RPC_SLUG + UPLOAD_BLOB,
                headers=headers,
                data=stream,
            )
            resp.raise_for_status()
            self._upload_blob = resp.json()
        return self._upload_blob["blob"]

    @property
    def alt_text(self):
        """
        Returns the alternative text for the image.

        :return: The alternative text for the image.
        :rtype: str
        """
        return self._alt_text
