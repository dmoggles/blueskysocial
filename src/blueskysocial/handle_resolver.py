"""
Access function to resolve the handle of a user.
"""

import requests
from blueskysocial.api_endpoints import RPC_SLUG, RESOLVE_HANDLE
from blueskysocial.utils import get_auth_header
from blueskysocial.errors import InvalidUserHandleError
from blueskysocial.typedefs import as_str


def resolve_handle(handle: str, access_token: str) -> str:
    """
    Resolves the handle of a user.

    Args:
        handle (str): The handle of the user to resolve.
        access_token (str): The access token of the authenticated user.

    Returns:
        str: The resolved handle of the user.
    """
    response = requests.get(
        RPC_SLUG + RESOLVE_HANDLE + "?handle=" + handle,
        headers=get_auth_header(access_token),
    )
    if response.status_code == 400:
        raise InvalidUserHandleError(f"Invalid user handle {handle}")

    response.raise_for_status()
    return as_str(response.json()["did"])
