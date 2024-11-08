"""

The client module contains the Client class which is used to
interact with the BlueSky Social server.
"""
from typing import Dict, List
import requests
from blueskysocial.post import Post

from blueskysocial.api_endpoints import (
    RPC_SLUG,
    CREATE_SESSION,
    CREATE_RECORD,
    POST_TYPE,
)
from blueskysocial.errors import SessionNotAuthenticatedError
from blueskysocial.replies import get_reply_refs


class Client:
    """
    A client class for interacting with the BlueSky Social server.


    """

    def __init__(self):
        self._session = None

    @property
    def access_token(self):
        """The access token for the client.

        Returns:
            str: The access token.
        """
        return self._session["accessJwt"]

    @property
    def did(self):
        """The DID for the client.

        Returns:
            str: The DID (Decentralized Identifier) for the client.
        """
        return self._session["did"]

    def authenticate(self, handle: str, password: str):
        """Authenticate the client with the server.

        Args:
            handle (str): The handle or username of the client.
            password (str): The password of the client.

        Raises:
            requests.HTTPError: If the server returns an error response.

        Returns:
            dict: The session information returned by the server.
        """
        response = requests.post(
            RPC_SLUG + CREATE_SESSION,
            json={"identifier": handle, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        session = response.json()
        self._session = session

    def post(self, post: Post) -> dict:
        """Post content to the server.

        Args:
            post (Post): The post object to be posted.

        Returns:
            dict: The response from the server.

        Raises:
            Exception: If the client is not authenticated.
        """
        if not self._session:
            raise SessionNotAuthenticatedError("Client not authenticated.")

        response = requests.post(
            RPC_SLUG + CREATE_RECORD,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "repo": self.did,
                "collection": POST_TYPE,
                "record": post.build(self._session),
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def post_reply(self, post: Post, references: Dict[str, Dict[str, str]]) -> dict:
        """
        Posts a reply to an existing post.

        Args:
            post (Post): The post object to be replied to.
            references (Dict[str, Dict[str, str]]): A dictionary containing the root and
                parent references.
                - 'root': A dictionary with 'uri' and 'cid' keys for the root reference.
                - 'parent': A dictionary with 'uri' and 'cid' keys for the parent reference.

        Returns:
            dict: The JSON response from the server.

        Raises:
            AssertionError: If required references are missing.
            SessionNotAuthenticatedError: If the client is not authenticated.
            requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        assert "root" in references, "Root reference is required"
        assert "parent" in references, "Parent reference is required"
        assert "uri" in references["root"], "Root reference URI is required"
        assert "uri" in references["parent"], "Parent reference URI is required"
        assert "cid" in references["root"], "Root reference CID is required"
        assert "cid" in references["parent"], "Parent reference CID is required"
        if not self._session:
            raise SessionNotAuthenticatedError("Client not authenticated.")
        record = post.build(self._session)
        record["reply"] = references
        response = requests.post(
            RPC_SLUG + CREATE_RECORD,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "repo": self.did,
                "collection": POST_TYPE,
                "record": post.build(self._session),
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def post_thread(self, posts: List[Post]) -> List[Dict]:
        """
        Posts a thread of posts to the server.

        Args:
            posts (List[Post]): A list of post objects to be posted.

        Returns:
            List[Dict]: A list of JSON responses from the server.

        Raises:
            SessionNotAuthenticatedError: If the client is not authenticated.
            requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        if not self._session:
            raise SessionNotAuthenticatedError("Client not authenticated.")
        responses = []
        assert len(posts) > 1, "At least two posts are required to create a thread"
        prev_post_return = self.post(posts[0])
        responses.append(prev_post_return)
        for post in posts[1:]:

            references = get_reply_refs(prev_post_return["uri"])
            response = self.post_reply(post, references)
            responses.append(response)
            prev_post_return = response

        return responses
