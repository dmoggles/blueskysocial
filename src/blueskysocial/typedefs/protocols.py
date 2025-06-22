"""
Protocol definitions for BlueSky Social types.
"""

from typing import Protocol
import datetime as dt
from typing_extensions import runtime_checkable
from blueskysocial.typedefs._types import ApiPayloadType


@runtime_checkable
class ConvoProtocol(Protocol):
    """
    Protocol defining the interface for a conversation object.

    This protocol defines the expected attributes and methods that a conversation
    object should have to be compatible with filters and other components.
    """

    @property
    def participant(self) -> str:
        """
        The handle of the other participant in the conversation.

        Returns:
            str: The handle of the participant who is not the current session user.
        """
        ...

    @property
    def unread_count(self) -> int:
        """
        The number of unread messages in the conversation.

        Returns:
            int: The count of unread messages.
        """
        ...

    @property
    def opened(self) -> bool:
        """
        Whether the conversation has been opened.

        Returns:
            bool: True if the conversation has been opened, False otherwise.
        """
        ...

    @property
    def convo_id(self) -> str:
        """
        The unique identifier of the conversation.

        Returns:
            str: The conversation ID.
        """
        ...

    @property
    def last_message(self) -> str:
        """
        The text content of the last message in the conversation.

        Returns:
            str: The text of the last message.
        """
        ...

    @property
    def last_message_time(self) -> dt.datetime:
        """
        The timestamp when the last message was sent.

        Returns:
            dt.datetime: The datetime object representing when the last message was sent.
        """
        ...


@runtime_checkable
class DirectMessageProtocol(Protocol):
    """
    Protocol defining the interface for a direct message object.

    This protocol defines the expected attributes and methods that a direct message
    object should have to be compatible with filters and other components.
    """

    @property
    def text(self) -> str:
        """
        The text content of the direct message.

        Returns:
            str: The text of the direct message.
        """
        ...

    @property
    def sent_at(self) -> dt.datetime:
        """
        The timestamp when the direct message was sent.

        Returns:
            dt.datetime: The datetime object representing when the direct message was sent.
        """
        ...

    @property
    def convo(self) -> ConvoProtocol:
        """
        The conversation to which this direct message belongs.

        Returns:
            ConvoProtocol: The conversation instance.
        """
        ...


@runtime_checkable
class PostProtocol(Protocol):
    """
    Protocol defining the interface for a post object.

    This protocol defines the expected attributes and methods that a post
    object should have to be compatible with filters and other components.
    """

    @property
    def post(self) -> ApiPayloadType:
        """
        The post data as a dictionary.

        Returns:
            Dict[str, str]: The post data.
        """
        ...

    @property
    def embed(self) -> ApiPayloadType:
        """
        The embedded data associated with the post.

        Returns:
            Dict[str, str]: The embedded data.
        """
        ...
