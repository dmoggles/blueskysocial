from typing import List, Dict, Union
from io import BytesIO
import requests
from blueskysocial.api_endpoints import UPLOAD_BLOB, RPC_SLUG

IMAGE_MIMETYPE = "image/png"


class Image:
    """
    Represents an image object that can be initialized from a URL, a local file, or a file handle.

    Args:
        image (Union[str, BytesIO]): The image source, which can be a URL, a local file path, or a file handle.
        alt_text (str, optional): The alternative text for the image. Defaults to "".

    Raises:
        Exception: If the image file size exceeds 1000000 bytes.

    Attributes:
        _image_src (Union[str, BytesIO]): The image source.
        _alt_text (str): The alternative text for the image.
        _image (bytes): The image content.

    Methods:
        alt_text: Returns the alternative text for the image.
        _initialize: Initializes the image object.
        _get_image_from_url: Retrieves the image content from a URL.
        _get_image_from_file: Retrieves the image content from a local file.
        _get_image_from_file_handle: Retrieves the image content from a file handle.
        build: Builds and uploads the image to the server.

    """

    def __init__(self, image: Union[str, BytesIO], alt_text: str):
        self._image_src = image
        self._alt_text = alt_text
        self._initialize()

    @property
    def alt_text(self):
        """
        Returns the alternative text for the image.

        :return: The alternative text for the image.
        :rtype: str
        """
        return self._alt_text

    def _initialize(self):
        if isinstance(self._image_src, str):
            if self._image_src.startswith("http"):
                self._image = self._get_image_from_url()
            else:
                self._image = self._get_image_from_file()
        else:
            self._image = self._get_image_from_file_handle()

        if len(self._image) > 1000000:
            raise Exception(
                f"image file size too large. 1000000 bytes maximum, got: {len(self._image)}"
            )

    def _get_image_from_url(self):
        response = requests.get(self._image_src)
        response.raise_for_status()
        return response.content

    def _get_image_from_file(self):
        with open(self._image_src, "rb") as f:
            return f.read()

    def _get_image_from_file_handle(self):
        return self._image_src.read()

    def build(self, session: dict) -> dict:
        """
        Builds and uploads an image to the server.

        Args:
            session (dict): The session containing the access JWT.

        Returns:
            dict: The response JSON containing the uploaded image blob.
        """
        resp = requests.post(
            RPC_SLUG + UPLOAD_BLOB,
            headers={
                "Content-Type": IMAGE_MIMETYPE,
                "Authorization": "Bearer " + session["accessJwt"],
            },
            data=self._image,
        )
        resp.raise_for_status()
        return resp.json()["blob"]
