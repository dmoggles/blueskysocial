"""

This module contains the Post class, which represents a post in a social media feed.

"""
from typing import List, Dict
from datetime import datetime, timezone
import re
import requests

from blueskysocial.api_endpoints import (
    POST_TYPE,
    MENTION_TYPE,
    LINK_TYPE,
    RPC_SLUG,
    RESOLVE_HANDLE,
    IMAGES_TYPE,
)
from blueskysocial.image import Image


class Post:
    """
    Represents a post in a social media feed.

    Args:
        content (str): The content of the post.

    Attributes:
        _post (dict): The dictionary representing the post.

    Methods:
        add_languages(languages: List[str]) -> Post: Add a language to the post.
        _parse_mentions() -> List[Dict]: Parse the mentions from the post.
        _parse_urls() -> List[Dict]: Parse the URLs from the post.
        parse_facets() -> List[Dict]: Parse the facets from the post.
        build() -> dict: Build the post.
    """

    def __init__(self, content: str, images: List[Image] = None):
        self._images = images or []
        if len(self._images) > 4:
            raise Exception("Maximum of 4 images allowed per post")

        self.content_str = content
        self._post = {
            "$type": POST_TYPE,
            "text": content,
        }

    def add_languages(self, languages: List[str]):
        """
        Add a list of languages to the post.

        Parameters:
        languages (List[str]): A list of languages to be added to the post.

        Returns:
        self: The updated Post object.
        """
        self._post["langs"] = languages
        return self

    def _handle_first_rich_url(self) -> Dict:
        """
        Handle the first rich url in the post.

        Returns:
            Dict: A dictionary representing the first rich url found in the post.
                The dictionary contains the following keys:
                - "start": The starting index of the rich url in the post text.
                - "end": The ending index of the rich url in the post text.
                - "url": The url of the rich url.
        """
        regex = rb"\[(.*?)\]\(\s*(https?://[^\s)]+)\s*\)"
        text_bytes = self._post["text"].encode("UTF-8")

        m = re.search(regex, text_bytes)
        if m:
            span = {
                "start": m.start(1) - 1,
                "end": m.end(1) - 1,
                "url": m.group(2).decode("UTF-8"),
            }
            self._post["text"] = (
                self._post["text"][: m.start(1) - 1]
                + self._post["text"][m.start(1) : m.end(1)]
                + self._post["text"][m.end() :]
            )
            return span
        return None

    def _parse_rich_urls(self) -> List[Dict]:
        """
        Parse urls of the format [text](url) from the post.

        This will also modify the post text to keep only the text part.

        Returns:
            List[Dict]: A list of dictionaries representing the rich urls found in the post.
                Each dictionary contains the following keys:
                - "start": The starting index of the rich url in the post text.
                - "end": The ending index of the rich url in the post text.
                - "url": The url of the rich url.

        """
        self._post["text"] = self.content_str
        spans = []
        while True:
            span = self._handle_first_rich_url()
            if span:
                spans.append(span)
            else:
                break
        return spans

    def _parse_mentions(self) -> List[Dict]:
        """Parse the mentions from the post.

        Returns:
            List[Dict]: A list of dictionaries representing the mentions found in the post.
                Each dictionary contains the following keys:
                - "start": The starting index of the mention in the post text.
                - "end": The ending index of the mention in the post text.
                - "handle": The handle of the mentioned user.
        """
        spans = []
        # regex based on: https://atproto.com/specs/handle#handle-identifier-syntax
        mention_regex = rb"[$|\W](@([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
        text_bytes = self._post["text"].encode("UTF-8")
        for m in re.finditer(mention_regex, text_bytes):
            spans.append(
                {
                    "start": m.start(1),
                    "end": m.end(1),
                    "handle": m.group(1)[1:].decode("UTF-8"),
                }
            )
        return spans

    def _parse_urls(self) -> List[Dict]:
        spans = []
        # partial/naive URL regex based on: https://stackoverflow.com/a/3809435
        # tweaked to disallow some training punctuation
        url_regex = rb"[$|\W](https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
        text_bytes = self._post["text"].encode("UTF-8")
        for m in re.finditer(url_regex, text_bytes):
            spans.append(
                {
                    "start": m.start(1),
                    "end": m.end(1),
                    "url": m.group(1).decode("UTF-8"),
                }
            )
        return spans

    def parse_facets(self) -> List[Dict]:
        """
        Parses the mentions and URLs in the post and returns a list of facets.

        Each facet contains the index range and features of a mention or URL.

        Returns:
            List[Dict]: A list of facets, where each facet is a dictionary with the following keys:
                - 'index': A dictionary containing the byte start and end positions of the mention or URL.
                - 'features': A list of dictionaries representing the features of the mention or URL.
        """
        facets = []
        for u in self._parse_rich_urls():
            facets.append(
                {
                    "index": {
                        "byteStart": u["start"],
                        "byteEnd": u["end"],
                    },
                    "features": [
                        {
                            "$type": LINK_TYPE,
                            # NOTE: URI ("I") not URL ("L")
                            "uri": u["url"],
                        }
                    ],
                }
            )
        for m in self._parse_mentions():
            resp = requests.get(
                RPC_SLUG + RESOLVE_HANDLE,
                params={"handle": m["handle"]},
            )
            # If the handle can't be resolved, just skip it!
            # It will be rendered as text in the post instead of a link
            if resp.status_code == 400:
                continue
            did = resp.json()["did"]
            facets.append(
                {
                    "index": {
                        "byteStart": m["start"],
                        "byteEnd": m["end"],
                    },
                    "features": [{"$type": MENTION_TYPE, "did": did}],
                }
            )
        for u in self._parse_urls():
            facets.append(
                {
                    "index": {
                        "byteStart": u["start"],
                        "byteEnd": u["end"],
                    },
                    "features": [
                        {
                            "$type": LINK_TYPE,
                            # NOTE: URI ("I") not URL ("L")
                            "uri": u["url"],
                        }
                    ],
                }
            )
        facets.sort(key=lambda x: x["index"]["byteStart"])
        return facets

    def build(self, session: dict):
        """Build the post.

        This method builds the post by setting the "createdAt" field to the current
        datetime in UTC and converting it to ISO 8601 format. It also parses the
        facets and adds them to the post if they exist.

        Args:
            session (dict): The session dictionary.

        Returns:
            dict: The built post.

        """
        self._post["createdAt"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        facets = self.parse_facets()
        if len(self._post["text"]) > 300:
            raise Exception("Maximum of 300 characters allowed per post")
        if facets:
            self._post["facets"] = facets

        if self._images:
            self._post["embed"] = {
                "$type": IMAGES_TYPE,
                "images": [
                    {"alt": image.alt_text, "image": image.build(session)}
                    for image in self._images
                ],
            }
        return self._post
