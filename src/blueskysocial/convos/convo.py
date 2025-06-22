"""BlueSky Social Conversation Module.

This module provides the Convo class, which represents and manages individual
conversations in the BlueSky Social messaging system. It handles conversation
metadata, message retrieval, and message sending operations.

Classes:
    Convo: Represents a conversation with message management capabilities.

Example:
    Working with conversations:

    >>> # Assuming you have a client and session
    >>> convo_data = {...}  # Raw conversation data from API
    >>> convo = Convo(convo_data, session)
    >>>
    >>> # Check conversation status
    >>> print(f"Conversation with: {convo.participant}")
    >>> print(f"Unread messages: {convo.unread_count}")
    >>>
    >>> # Retrieve messages
    >>> messages = convo.get_messages()
    >>> for message in messages:
    ...     print(f"{message.sender}: {message.text}")
    >>>
    >>> # Send a new message
    >>> response = convo.send_message("Hello there!")
    >>> print(f"Message sent: {response.text}")

Note:
    This class is typically instantiated by the Client class when retrieving
    conversations. Direct instantiation requires proper session authentication.
"""

from typing import Dict, Any, List, Optional
import datetime as dt
import requests
from blueskysocial.convos.message import DirectMessage
from blueskysocial.convos.filters import Filter
from blueskysocial.api_endpoints import CHAT_SLUG, GET_MESSAGES, SEND_MESSAGE
from blueskysocial.utils import get_auth_header
from blueskysocial.typedefs import as_str, as_bool, as_int


class Convo:
    """Represents a BlueSky Social conversation with message management.

    The Convo class encapsulates a conversation between users, providing access
    to conversation metadata, message history, and messaging capabilities. It
    handles both direct messages and group conversations.

    Attributes:
        _raw_json (Dict[str, Any]): Raw conversation data from the BlueSky API.
        _session (Dict[str, Any]): Authenticated session data for API requests.

    Example:
        Typical usage through the Client class:

        >>> client = Client()
        >>> client.authenticate("handle", "password")
        >>> convos = client.get_convos()
        >>> convo = convos[0]
        >>>
        >>> # Access conversation information
        >>> print(f"Chatting with: {convo.participant}")
        >>> print(f"Last message: {convo.last_message}")
        >>> print(f"Sent at: {convo.last_message_time}")
        >>>
        >>> # Manage messages
        >>> if convo.unread_count > 0:
        ...     messages = convo.get_messages()
        ...     for msg in messages:
        ...         print(f"{msg.sender}: {msg.text}")
        >>>
        >>> # Send a reply
        >>> response = convo.send_message("Thanks for the update!")

    Note:
        Conversation objects are typically created by the Client class when
        fetching conversations from the server. They require valid session
        authentication to perform message operations.
    """

    def __init__(self, raw_json: Dict[str, Any], session: Dict[str, Any]) -> None:
        """Initialize a new Convo instance.

        Creates a conversation object from raw API data and session information.
        This constructor is typically called by the Client class when fetching
        conversations from the BlueSky server.

        Args:
            raw_json (Dict[str, Any]): Raw conversation data from the BlueSky API,
                                      containing conversation metadata, member information,
                                      and recent message details.
            session (Dict[str, Any]): Authenticated session data including access tokens
                                     and user information required for API operations.

        Example:
            >>> # Typically called internally by Client
            >>> session = {"accessJwt": "token", "handle": "user.bsky.social"}
            >>> convo_data = {"id": "convo123", "members": [...], "lastMessage": {...}}
            >>> convo = Convo(convo_data, session)
        """
        self._raw_json = raw_json
        self._session = session

    @property
    def participant(self) -> str:
        """Get the handle of the other participant in a direct conversation.

        For direct (two-person) conversations, returns the handle of the participant
        who is not the current authenticated user. For group conversations with
        multiple participants, returns the first non-self participant found.

        Returns:
            str: The handle of the other participant in format "user.bsky.social".

        Raises:
            StopIteration: If no other participants are found (shouldn't occur in
                          valid conversations).
            KeyError: If the conversation data is malformed and missing expected fields.

        Example:
            >>> convo = client.get_convo_for_members("alice.bsky.social")
            >>> print(f"Chatting with: {convo.participant}")  # "alice.bsky.social"

        Note:
            This property is most useful for direct messages. For group conversations,
            consider accessing the full member list through the raw conversation data
            or implementing a separate members property.
        """
        return as_str(
            next(
                participant["handle"]
                for participant in self._raw_json["members"]
                if participant["handle"] != self._session["handle"]
            )
        )

    @property
    def unread_count(self) -> int:
        """Get the number of unread messages in the conversation.

        Returns the count of messages that haven't been read by the current user.
        This count is maintained by the BlueSky server and updates when messages
        are read or new messages arrive.

        Returns:
            int: The number of unread messages. Returns 0 if all messages have
                 been read or if the conversation has no messages.

        Example:
            >>> convo = client.get_convos()[0]
            >>> if convo.unread_count > 0:
            ...     print(f"You have {convo.unread_count} unread messages")
            ...     messages = convo.get_messages()
            ... else:
            ...     print("No unread messages")

        Note:
            The unread count reflects the server state at the time the conversation
            was fetched. It may not reflect real-time changes until refreshed.
        """
        return as_int(self._raw_json["unreadCount"])

    @property
    def opened(self) -> bool:
        """Check if the conversation has been opened by the current user.

        Indicates whether the authenticated user has previously opened/viewed
        this conversation. This is typically used for UI state management
        and notification purposes.

        Returns:
            bool: True if the conversation has been opened by the current user,
                  False if it's a new or unopened conversation.

        Example:
            >>> for convo in client.get_convos():
            ...     status = "opened" if convo.opened else "new"
            ...     print(f"Conversation with {convo.participant}: {status}")

        Note:
            This status is user-specific and maintained by the server. Opening
            a conversation typically marks it as read and may affect unread counts.
        """
        return as_bool(self._raw_json["opened"])

    @property
    def convo_id(self) -> str:
        """Get the unique identifier for this conversation.

        Returns the conversation's unique ID as assigned by the BlueSky server.
        This ID is used internally for API operations like retrieving messages
        and sending new messages.

        Returns:
            str: The conversation's unique identifier string.

        Example:
            >>> convo = client.get_convos()[0]
            >>> print(f"Conversation ID: {convo.convo_id}")
            >>> # Use ID for direct API calls if needed
            >>> messages = convo.get_messages()  # Uses this ID internally

        Note:
            This ID is persistent and won't change for the lifetime of the
            conversation. It's safe to store for later reference.
        """
        return as_str(self._raw_json["id"])

    @property
    def last_message(self) -> str:
        """Get the text content of the most recent message in the conversation.

        Returns the text of the last message sent in this conversation by any
        participant. This provides a quick preview of the conversation's current state.

        Returns:
            str: The text content of the most recent message.

        Raises:
            KeyError: If the conversation data is malformed or missing the last message.

        Example:
            >>> convos = client.get_convos()
            >>> for convo in convos:
            ...     preview = convo.last_message
            ...     if len(preview) > 50:
            ...         preview = preview[:47] + "..."
            ...     print(f"{convo.participant}: {preview}")

        Note:
            This only returns the text content. For full message details including
            sender, timestamp, and any attachments, use get_messages() to retrieve
            the complete message objects.
        """
        return as_str(self._raw_json["lastMessage"]["text"])

    @property
    def last_message_time(self) -> dt.datetime:
        """Get the timestamp when the last message was sent.

        Returns the date and time when the most recent message in the conversation
        was sent, parsed from the BlueSky API timestamp format.

        Returns:
            dt.datetime: The timestamp of the last message as a datetime object
                        in UTC timezone.

        Raises:
            ValueError: If the timestamp format in the raw data is invalid.
            KeyError: If the conversation data is missing the last message timestamp.

        Example:
            >>> convo = client.get_convos()[0]
            >>> last_time = convo.last_message_time
            >>> print(f"Last message sent: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
            >>>
            >>> # Check if message is recent
            >>> import datetime as dt
            >>> now = dt.datetime.utcnow()
            >>> if (now - last_time).total_seconds() < 3600:
            ...     print("Message sent within the last hour")

        Note:
            The timestamp is returned in UTC. Convert to local timezone if needed
            for user display. The expected format from the API is ISO 8601 with
            microseconds: "%Y-%m-%dT%H:%M:%S.%fZ"
        """
        return dt.datetime.strptime(
            self._raw_json["lastMessage"]["sentAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )

    def get_messages(self, msg_filter: Optional[Filter] = None) -> List[DirectMessage]:
        """Retrieve messages from the conversation with optional filtering.

        Fetches all messages in the conversation from the BlueSky server and
        optionally applies a filter to return only messages matching specific criteria.

        Args:
            msg_filter (Optional[Filter]): An optional filter function or Filter object
                                      to apply to the messages. Only messages for which
                                      the filter returns True will be included in the
                                      result. If None, all messages are returned.

        Returns:
            List[DirectMessage]: A list of DirectMessage objects representing the
                               messages in the conversation, ordered by the server
                               (typically chronological).

        Raises:
            requests.HTTPError: If the HTTP request to retrieve messages fails due to
                              authentication issues, network problems, or server errors.
            requests.Timeout: If the request times out.
            KeyError: If the response format is unexpected or missing required fields.

        Example:
            >>> convo = client.get_convos()[0]
            >>>
            >>> # Get all messages
            >>> all_messages = convo.get_messages()
            >>> for msg in all_messages:
            ...     print(f"{msg.sender}: {msg.text}")
            >>>
            >>> # Get messages from specific sender
            >>> from blueskysocial.convos.filters import Filter
            >>> alice_filter = Filter(lambda msg: msg.sender == "alice.bsky.social")
            >>> alice_messages = convo.get_messages(alice_filter)
            >>>
            >>> # Get recent messages only
            >>> import datetime as dt
            >>> recent_filter = Filter(lambda msg:
            ...     (dt.datetime.utcnow() - msg.sent_at).days < 7)
            >>> recent_messages = convo.get_messages(recent_filter)

        Note:
            - Filtering is applied client-side after retrieving all messages
            - Large conversations may take time to fetch all messages
            - Messages are typically returned in chronological order
        """
        response = requests.get(
            CHAT_SLUG + GET_MESSAGES + "?convoId=" + self.convo_id,
            headers=get_auth_header(self._session["accessJwt"]),
        )
        response.raise_for_status()
        return [
            DirectMessage(message, self)
            for message in response.json()["messages"]
            if not msg_filter or msg_filter(DirectMessage(message, self))
        ]

    def send_message(self, text: str) -> DirectMessage:
        """Send a text message in this conversation.

        Sends a new message to all participants in the conversation and returns
        the created message object with server-assigned metadata.

        Args:
            text (str): The text content of the message to send. Must be non-empty
                       and within platform limits for message length.

        Returns:
            DirectMessage: A DirectMessage object representing the sent message,
                          including server-assigned ID, timestamp, and other metadata.

        Raises:
            requests.HTTPError: If the request fails due to authentication issues,
                              message content violations, or server errors.
            requests.Timeout: If the request times out while sending.
            ValueError: If the text is empty or exceeds length limits.

        Example:
            >>> convo = client.get_convo_for_members("alice.bsky.social")
            >>>
            >>> # Send a simple message
            >>> message = convo.send_message("Hello Alice! How are you?")
            >>> print(f"Message sent at: {message.sent_at}")
            >>> print(f"Message ID: {message.message_id}")
            >>>
            >>> # Send a longer message
            >>> long_message = "This is a longer message that explains..."
            >>> response = convo.send_message(long_message)
            >>>
            >>> # Check if message was delivered
            >>> if response.message_id:
            ...     print("Message delivered successfully")

        Note:
            - The message will be sent to all participants in the conversation
            - The returned DirectMessage object contains the message as stored on the server
            - Message delivery is typically immediate but may be subject to rate limits
            - Empty or whitespace-only messages may be rejected by the server
        """
        response = requests.post(
            CHAT_SLUG + SEND_MESSAGE,
            headers=get_auth_header(self._session["accessJwt"]),
            json={"convoId": self.convo_id, "message": {"text": text}},
        )
        response.raise_for_status()
        return DirectMessage(response.json(), self)
