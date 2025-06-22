"""
Utilities for facilitating the retrieval of reply
references in the BlueSky Social API.
"""

from typing import Dict
import requests
from blueskysocial.api_endpoints import RPC_SLUG
from blueskysocial.utils import parse_uri


def get_reply_refs(parent_uri: str) -> Dict[str, Dict[str, str]]:
    """
    Retrieves the root and parent references for a given parent URI.
    This function takes a parent URI, parses it, and makes a request to fetch the
    corresponding record. If the parent record is a reply, it fetches the root
    record as well. It then returns a dictionary containing the URIs and CIDs
    (Content Identifiers) of both the root and parent records.
    Args:
        parent_uri (str): The URI of the parent record.
    Returns:
        Dict: A dictionary containing the URIs and CIDs of the root and parent records.
            The dictionary has the following structure:
            {
                "root": {
                    "uri": str,
                    "cid": str,
                },
                "parent": {
                    "uri": str,
                    "cid": str,
                },
            }
    Raises:
        requests.exceptions.HTTPError: If the HTTP request to fetch the record fails.
    """
    uri_parts = parse_uri(parent_uri)

    resp = requests.get(
        RPC_SLUG + "com.atproto.repo.getRecord",
        params=uri_parts,
        timeout=10,
    )
    resp.raise_for_status()
    parent = resp.json()

    parent_reply = parent["value"].get("reply")
    if parent_reply is not None:
        root_uri = parent_reply["root"]["uri"]
        root_repo, root_collection, root_rkey = root_uri.split("/")[2:5]
        resp = requests.get(
            RPC_SLUG + "com.atproto.repo.getRecord",
            params={
                "repo": root_repo,
                "collection": root_collection,
                "rkey": root_rkey,
            },
            timeout=10,
        )
        resp.raise_for_status()
        root = resp.json()
    else:
        # The parent record is a top-level post, so it is also the root
        root = parent

    return {
        "root": {
            "uri": root["uri"],
            "cid": root["cid"],
        },
        "parent": {
            "uri": parent["uri"],
            "cid": parent["cid"],
        },
    }
