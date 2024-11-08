"""
Utilities for the BlueSky Social API.
"""

from typing import Dict


def parse_uri(uri: str) -> Dict:
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
