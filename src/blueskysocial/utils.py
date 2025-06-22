"""
Utilities for the BlueSky Social API.
"""

from typing import Dict, Optional
from bs4 import Tag


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


def bs4_tag_extract_content(tag: Tag) -> str:
    """
    Extracts the content from a BeautifulSoup tag, handling None values.

    Args:
        tag: A BeautifulSoup tag object.

    Returns:
        str: The content of the tag, or an empty string if the tag is None.
    """
    return str(tag.get("content", "")) if tag else ""
