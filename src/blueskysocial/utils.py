"""
Utilities for the BlueSky Social API.
"""

from typing import Dict, Optional, Union
from bs4 import Tag
from bs4.element import NavigableString
from PIL import Image
from io import BytesIO
import cv2
from blueskysocial.typedefs import AspectRatioConsumerProtocol
from blueskysocial.errors import UnknownAspectRatioError


def parse_uri(uri: str) -> Dict[str, str]:
    """
    Parses a URI string and extracts the repository, collection, and rkey.

    Args:
        uri (str): The URI string to parse.

    Returns:
        Dict: A dictionary containing the 'repo', 'collection', and 'rkey' extracted from the URI.
    """
    repo, collection, rkey = uri.split("/")[2:5]
    return {
        "repo": repo,
        "collection": collection,
        "rkey": rkey,
    }


def get_auth_header(
    token: str, headers: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Returns a dictionary containing the Authorization header with the given token.

    Args:
        token (str): The token to use for the Authorization header.
        headers (Dict[str, str], optional): Additional headers to include. Defaults to None.

    Returns:
        Dict[str, str]: A dictionary containing the Authorization header with the given token.
    """
    if headers is None:
        headers = {}
    headers["Authorization"] = f"Bearer {token}"
    return headers


def bs4_tag_extract_content(tag: Optional[Union[Tag, NavigableString]]) -> str:
    """
    Extracts the content from a BeautifulSoup tag, handling None values.

    Args:
        tag: A BeautifulSoup tag object, NavigableString, or None.

    Returns:
        str: The content of the tag, or an empty string if the tag is None.
    """
    if tag is None:
        return ""
    if isinstance(tag, Tag):
        content = tag.get("content")
        return str(content) if content is not None else ""
    return ""


def get_image_aspect_ratio_spec(image: bytes) -> Optional[Dict[str, int]]:
    """
    Returns the aspect ratio of an image as a tuple of (width, height).

    Args:
        image (bytes): The image data in bytes.

    Returns:
        Tuple[int, int]: A tuple containing the width and height of the image.
    """
    try:
        with Image.open(BytesIO(image)) as img:
            width, height = img.size
            return {
                "width": width,
                "height": height,
            }
    except Exception:
        return None


def get_video_aspect_ratio_spec(path: str) -> Optional[Dict[str, int]]:
    try:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {path}")
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        cap.release()
        return {
            "width": int(width),
            "height": int(height),
        }
    except Exception:
        return None


def provide_aspect_ratio(
    consumer: AspectRatioConsumerProtocol,
) -> Optional[Dict[str, int]]:
    """
    Provides the aspect ratio of the data accessor of the consumer.

    Args:
        consumer (AspectRatioConsumerProtocol): The consumer object that implements the protocol.

    Returns:
        Optional[Dict[str, int]]: A dictionary containing the width and height of the aspect ratio, or None if not applicable.
    """
    if consumer.aspect_ratio is not None:
        return {"width": consumer.aspect_ratio[0], "height": consumer.aspect_ratio[1]}

    aspect_ratio = consumer.aspect_ratio_function(consumer.data_accessor)
    if aspect_ratio is None and consumer.require_aspect_ratio:
        raise UnknownAspectRatioError(
            f"{consumer.__class__} aspect ratio could not be determined. "
            "Please provide a valid aspect ratio function or data accessor."
            "or provide a valid aspect ratio at construction time using the aspect_ratio parameter."
        )
    return aspect_ratio
