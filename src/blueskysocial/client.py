"""BlueSky Social Client Module.

This module provides the Client class, which serves as the main interface for
interacting with the BlueSky Social server. The client handles authentication,
posting content, managing conversations, and other core social media operations.

Classes:
    Client: Main client for BlueSky Social API interactions.

Example:
    Basic usage of the BlueSky Social client:

    >>> client = Client()
    >>> client.authenticate("your.handle", "your_password")
    >>> post = Post("Hello, BlueSky!")
    >>> response = client.post(post)
    >>> print(f"Post created: {response['uri']}")

    Working with conversations:

    >>> convos = client.get_convos()
    >>> for convo in convos:
    ...     print(f"Conversation with {len(convo.members)} members")

    Creating a thread:

    >>> posts = [Post("First post"), Post("Second post"), Post("Third post")]
    >>> thread_responses = client.post_thread(posts)
    >>> print(f"Thread created with {len(thread_responses)} posts")

Note:
    All methods that interact with the server require authentication. Call
    authenticate() before using other methods.
"""

from typing import Dict, List, Union, Optional, cast
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
from blueskysocial.typedefs import ApiPayloadType, as_str


class Client:
    """A client for interacting with the BlueSky Social API.

    The Client class provides a high-level interface for authenticating with
    the BlueSky Social server and performing various operations such as posting
    content, managing conversations, and resolving handles.

    Attributes:
        _session (ApiPayloadType): Internal session data from authentication.
        _authenticated (bool): Whether the client is currently authenticated.

    Example:
        Basic client setup and authentication:

        >>> client = Client()
        >>> client.authenticate("your.handle", "your_password")
        >>> print(f"Authenticated as: {client.handle}")

        Posting content:

        >>> post = Post("Hello, world!")
        >>> response = client.post(post)
        >>> print(f"Posted with URI: {response['uri']}")

    Note:
        Most operations require authentication. Always call authenticate()
        before using other methods.
    """

    def __init__(self) -> None:
        """Initialize a new BlueSky Social client.

        Creates an unauthenticated client instance with empty session data.
        Call authenticate() to establish a session with the server.

        Example:
            >>> client = Client()
            >>> print(client.authenticated)  # False
            >>> client.authenticate("handle", "password")
            >>> print(client.authenticated)  # True
        """
        self._session: ApiPayloadType = {}
        self._authenticated = False

    @property
    def authenticated(self) -> bool:
        """Check if the client is authenticated with the BlueSky server.

        Returns:
            bool: True if the client has an active authenticated session,
                  False otherwise.

        Example:
            >>> client = Client()
            >>> print(client.authenticated)  # False
            >>> client.authenticate("handle", "password")
            >>> print(client.authenticated)  # True
        """
        return self._authenticated

    @property
    def handle(self) -> str:
        """Get the authenticated user's handle.

        Returns:
            str: The handle (username) of the authenticated user.

        Raises:
            SessionNotAuthenticatedError: If the client is not authenticated.

        Example:
            >>> client = Client()
            >>> client.authenticate("alice.bsky.social", "password")
            >>> print(client.handle)  # "alice.bsky.social"
        """
        if not self._session:
            raise SessionNotAuthenticatedError("Client not authenticated.")
        return as_str(self._session["handle"])

    @property
    def access_token(self) -> str:
        """Get the access token for authenticated API requests.

        Returns:
            str: The JWT access token for making authenticated requests.

        Raises:
            SessionNotAuthenticatedError: If the client is not authenticated.

        Example:
            >>> client = Client()
            >>> client.authenticate("handle", "password")
            >>> token = client.access_token
            >>> print(f"Token starts with: {token[:20]}...")

        Note:
            This token is used internally for API authentication. Handle with care
            and avoid logging or exposing it in production code.
        """
        if not self._session:
            raise SessionNotAuthenticatedError("Client not authenticated.")
        return as_str(self._session["accessJwt"])

    @property
    def did(self) -> str:
        """Get the Decentralized Identifier (DID) for the authenticated user.

        Returns:
            str: The DID of the authenticated user, used as a unique identifier
                 across the decentralized network.

        Raises:
            SessionNotAuthenticatedError: If the client is not authenticated.

        Example:
            >>> client = Client()
            >>> client.authenticate("alice.bsky.social", "password")
            >>> print(client.did)  # "did:plc:abc123..."

        Note:
            DIDs are permanent identifiers that remain constant even if the
            user changes their handle or moves to a different server.
        """
        if not self._session:
            raise SessionNotAuthenticatedError("Client not authenticated.")
        return as_str(self._session["did"])

    def authenticate(self, handle: str, password: str) -> None:
        """Authenticate the client with the BlueSky server.

        Establishes a session with the BlueSky server using the provided
        credentials. This must be called before using other API methods.

        Args:
            handle (str): The handle (username) or email address for login.
                         Can be in formats like "alice.bsky.social" or "alice@email.com".
            password (str): The password for the account.

        Raises:
            requests.HTTPError: If authentication fails due to invalid credentials
                               or server errors.
            requests.Timeout: If the request times out after 10 seconds.
            requests.RequestException: For other network-related errors.

        Example:
            >>> client = Client()
            >>> client.authenticate("alice.bsky.social", "secure_password")
            >>> print(f"Logged in as: {client.handle}")

            # Or with email
            >>> client.authenticate("alice@example.com", "secure_password")

        Note:
            Store credentials securely. Consider using environment variables
            or secure credential storage systems in production applications.
        """
        response = requests.post(
            RPC_SLUG + CREATE_SESSION,
            json={"identifier": handle, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        session = response.json()
        self._session = session
        self._authenticated = True

    def post(self, post: Post) -> ApiPayloadType:
        """Post content to the BlueSky Social server.

        Creates a new post on the authenticated user's timeline. The post can
        contain text, images, videos, web cards, and other attachments.

        Args:
            post (Post): A Post object containing the content to be posted.
                        See the Post class for details on creating posts with
                        various types of content.

        Returns:
            ApiPayloadType: The server response containing post metadata including:
                - uri: The unique identifier for the created post
                - cid: The content identifier hash
                - validation_status: Status of content validation

        Raises:
            SessionNotAuthenticatedError: If the client is not authenticated.
            requests.HTTPError: If the server returns an error response.
            requests.Timeout: If the request times out after 10 seconds.

        Example:
            >>> client = Client()
            >>> client.authenticate("handle", "password")
            >>>
            >>> # Simple text post
            >>> post = Post("Hello, BlueSky!")
            >>> response = client.post(post)
            >>> print(f"Posted: {response['uri']}")
            >>>
            >>> # Post with image
            >>> image = Image("path/to/image.jpg", alt_text="A beautiful sunset")
            >>> post = Post("Check out this sunset!", images=[image])
            >>> response = client.post(post)
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
        return cast(ApiPayloadType, response.json())

    def post_reply(
        self, post: Post, references: Dict[str, Dict[str, str]]
    ) -> ApiPayloadType:
        """Post a reply to an existing post.

        Creates a reply to an existing post by providing the necessary reference
        information to maintain the conversation thread structure.

        Args:
            post (Post): The Post object containing the reply content.
            references (Dict[str, Dict[str, str]]): Reference information for the reply:
                - 'root': Dict with 'uri' and 'cid' keys for the thread's root post
                - 'parent': Dict with 'uri' and 'cid' keys for the immediate parent post

                For a reply to the original post, both 'root' and 'parent' reference
                the same post. For nested replies, 'root' references the thread start
                and 'parent' references the post being directly replied to.

        Returns:
            ApiPayloadType: The server response containing reply metadata including:
                - uri: The unique identifier for the created reply
                - cid: The content identifier hash
                - validation_status: Status of content validation

        Raises:
            AssertionError: If required reference fields are missing or invalid.
            SessionNotAuthenticatedError: If the client is not authenticated.
            requests.HTTPError: If the server returns an error response.
            requests.Timeout: If the request times out after 10 seconds.

        Example:
            >>> client = Client()
            >>> client.authenticate("handle", "password")
            >>>
            >>> # Get references for a post you want to reply to
            >>> references = get_reply_refs("at://did:plc:abc.../post123")
            >>>
            >>> # Create and post the reply
            >>> reply = Post("Great post! Thanks for sharing.")
            >>> response = client.post_reply(reply, references)
            >>> print(f"Reply posted: {response['uri']}")

        Note:
            Use the get_reply_refs() function from blueskysocial.replies to
            automatically generate proper reference structures from a post URI.
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
        return cast(ApiPayloadType, response.json())

    def post_thread(self, posts: List[Post]) -> List[ApiPayloadType]:
        """Post a connected thread of posts to the BlueSky server.

        Creates a thread by posting multiple posts in sequence, where each
        subsequent post replies to the previous one, forming a connected
        conversation thread under the original post.

        Args:
            posts (List[Post]): A list of Post objects to be posted as a thread.
                               Must contain at least 2 posts. The first post becomes
                               the thread root, and subsequent posts become replies.

        Returns:
            List[ApiPayloadType]: A list of server responses, one for each posted
                                 message in the thread. Each response contains:
                                 - uri: The unique identifier for the post
                                 - cid: The content identifier hash
                                 - validation_status: Status of content validation

        Raises:
            AssertionError: If fewer than 2 posts are provided.
            SessionNotAuthenticatedError: If the client is not authenticated.
            requests.HTTPError: If any server request returns an error response.
            requests.Timeout: If any request times out after 10 seconds.

        Example:
            >>> client = Client()
            >>> client.authenticate("handle", "password")
            >>>
            >>> # Create a thread about a topic
            >>> posts = [
            ...     Post("🧵 Thread about BlueSky features (1/3)"),
            ...     Post("First, the decentralized architecture allows for... (2/3)"),
            ...     Post("Finally, the protocol enables true data portability. (3/3)")
            ... ]
            >>>
            >>> responses = client.post_thread(posts)
            >>> print(f"Thread created with {len(responses)} posts")
            >>> for i, response in enumerate(responses, 1):
            ...     print(f"Post {i}: {response['uri']}")

        Note:
            - Each post in the thread will appear as a reply to the previous one
            - The thread structure is maintained through reply references
            - If any post in the sequence fails, subsequent posts won't be created
        """
        if not self._session:
            raise SessionNotAuthenticatedError("Client not authenticated.")
        responses: List[ApiPayloadType] = []
        assert len(posts) > 1, "At least two posts are required to create a thread"
        prev_post_return = self.post(posts[0])
        responses.append(prev_post_return)
        for post in posts[1:]:

            references = get_reply_refs(prev_post_return["uri"])
            response = self.post_reply(post, references)
            responses.append(response)
            prev_post_return = response

        return responses

    def get_convos(self, convo_filter: Optional[Filter] = None) -> List[Convo]:
        """Retrieve a list of conversations for the authenticated user.

        Fetches all conversations that the authenticated user is a member of,
        with optional filtering to match specific criteria.

        Args:
            convo_filter (Optional[Filter]): An optional filter function or Filter object
                                            to apply to the conversations. Only conversations
                                            that pass the filter will be included in the
                                            returned list. If None, all conversations are returned.

        Returns:
            List[Convo]: A list of Convo objects representing the user's conversations.
                        Each Convo contains information about members, messages, and
                        conversation metadata.

        Raises:
            SessionNotAuthenticatedError: If the client is not authenticated.
            requests.HTTPError: If the server returns an error response.
            requests.Timeout: If the request times out.

        Example:
            >>> client = Client()
            >>> client.authenticate("handle", "password")
            >>>
            >>> # Get all conversations
            >>> all_convos = client.get_convos()
            >>> print(f"You have {len(all_convos)} conversations")
            >>>
            >>> # Get conversations with unread messages
            >>> unread_filter = Filter(lambda c: c.unread_count > 0)
            >>> unread_convos = client.get_convos(unread_filter)
            >>> print(f"You have {len(unread_convos)} unread conversations")
            >>>
            >>> # Get conversations with specific members
            >>> alice_filter = Filter(lambda c: "alice.bsky.social" in [m.handle for m in c.members])
            >>> alice_convos = client.get_convos(alice_filter)

        Note:
            The filter is applied to Convo objects after they are retrieved from
            the server, so filtering happens client-side.
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
            if not convo_filter or convo_filter(Convo(convo, self._session))
        ]

    def get_convo_for_members(self, members: Union[List[str], str]) -> Convo:
        """Retrieve or create a conversation for the specified members.

        Gets an existing conversation that includes exactly the specified members,
        or creates a new conversation if one doesn't exist. This is useful for
        starting direct messages or group conversations.

        Args:
            members (Union[List[str], str]): The members to include in the conversation.
                                           Can be a single handle string or a list of handles.
                                           Maximum of 10 members allowed per conversation.
                                           Handles can be in format "alice.bsky.social"
                                           or full DIDs.

        Returns:
            Convo: A Convo object representing the conversation with the specified
                  members. Contains conversation metadata, member information, and
                  recent messages.

        Raises:
            AssertionError: If more than 10 members are specified.
            SessionNotAuthenticatedError: If the client is not authenticated.
            requests.HTTPError: If the server returns an error response.
            requests.Timeout: If the request times out.

        Example:
            >>> client = Client()
            >>> client.authenticate("handle", "password")
            >>>
            >>> # Start a direct message
            >>> dm_convo = client.get_convo_for_members("alice.bsky.social")
            >>> print(f"DM with {dm_convo.members[0].handle}")
            >>>
            >>> # Create a group conversation
            >>> group_members = ["alice.bsky.social", "bob.bsky.social", "charlie.bsky.social"]
            >>> group_convo = client.get_convo_for_members(group_members)
            >>> print(f"Group chat with {len(group_convo.members)} members")

        Note:
            - The authenticated user is automatically included in the conversation
            - If a conversation already exists with these exact members, it returns
              the existing conversation rather than creating a new one
            - Member handles are resolved to DIDs automatically
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
        """Resolve a BlueSky handle to its corresponding DID.

        Converts a human-readable handle (like "alice.bsky.social") to its
        corresponding Decentralized Identifier (DID). This is useful for operations
        that require DIDs rather than handles.

        Args:
            handle (str): The handle to resolve. Can be in various formats:
                         - "alice.bsky.social" (full handle)
                         - "alice" (short handle, will be expanded)
                         - Custom domain handles

        Returns:
            str: The resolved DID for the handle, in format "did:plc:..." or "did:web:..."

        Raises:
            SessionNotAuthenticatedError: If the client is not authenticated.
            requests.HTTPError: If the handle cannot be resolved or doesn't exist.
            requests.Timeout: If the resolution request times out.

        Example:
            >>> client = Client()
            >>> client.authenticate("handle", "password")
            >>>
            >>> # Resolve a handle to DID
            >>> did = client.resolve_handle("alice.bsky.social")
            >>> print(f"alice.bsky.social resolves to: {did}")
            >>>
            >>> # Use in conversation creation
            >>> alice_did = client.resolve_handle("alice.bsky.social")
            >>> bob_did = client.resolve_handle("bob.bsky.social")
            >>> convo = client.get_convo_for_members([alice_did, bob_did])

        Note:
            - DIDs are permanent identifiers that don't change if a user changes handles
            - This method uses the authenticated client's access token for resolution
            - The resolved DID can be used in API calls that require user identification
        """
        return resolve_handle(handle, self.access_token)
