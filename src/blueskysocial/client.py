"""

The client module contains the Client class which is used to
interact with the BlueSky Social server.
"""

from typing import Dict, List, Union
import requests
from blueskysocial.post import Post

from blueskysocial.api_endpoints import (
    RPC_SLUG,
    CREATE_SESSION,
    CREATE_RECORD,
    POST_TYPE,
    CHAT_SLUG,
    LIST_CONVOS,
    GET_CONVO_FOR_MEMBERS,
)
from blueskysocial.errors import SessionNotAuthenticatedError
from blueskysocial.replies import get_reply_refs
from blueskysocial.convos import Convo
from blueskysocial.convos.filters import Filter
from blueskysocial.utils import get_auth_header
from blueskysocial.handle_resolver import resolve_handle


class Client:
    """
    A client class for interacting with the BlueSky Social server.


    """

    def __init__(self):
        self._session = None

    @property
    def handle(self):
        """The handle of the client.

        Returns:
            str: The handle of the client.
        """
        return self._session["handle"]

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
            headers=get_auth_header(self.access_token),
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
            headers=get_auth_header(self.access_token),
            json={
                "repo": self.did,
                "collection": POST_TYPE,
                "record": record,
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

    def get_convos(self, filter: Filter = None) -> List[Convo]:
        """
        Retrieve a list of conversations.

        Args:
            filter (Filter, optional): A filter to apply to the conversations. Defaults to None.

        Returns:
            List[Convo]: A list of Convo objects that match the filter criteria.

        Raises:
            requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        response = requests.get(
            CHAT_SLUG + LIST_CONVOS,
            headers=get_auth_header(self.access_token),
        )
        response.raise_for_status()
        convos = response.json()
        return [
            Convo(convo, self._session)
            for convo in convos["convos"]
            if not filter or filter.evaluate(Convo(convo, self._session))
        ]

    def get_convo_for_members(self, members: Union[List[str], str]) -> Convo:
        """
        Retrieve a conversation for the specified members.

        Args:
            members (Union[List[str], str]): A list of member handles or a single member handle.
                                                A maximum of 10 members can be in a conversation.

        Returns:
            Convo: An instance of the Convo class representing the conversation.

        Raises:
            AssertionError: If the number of members exceeds 10.
            requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        if isinstance(members, str):
            members = [members]
        assert len(members) <= 10, "A maximum of 10 members can be in a conversation."
        member_dids = [resolve_handle(member, self.access_token) for member in members]
        response = requests.get(
            CHAT_SLUG + GET_CONVO_FOR_MEMBERS,
            headers=get_auth_header(self.access_token),
            params={"members": member_dids},
        )
        response.raise_for_status()
        convo = response.json()["convo"]
        return Convo(convo, self._session)

    def resolve_handle(self, handle: str) -> str:
        """
        Resolves a given handle to its corresponding identifier using the access token.

        Args:
            handle (str): The handle to be resolved.

        Returns:
            str: The resolved identifier for the given handle.
        """
        return resolve_handle(handle, self.access_token)
