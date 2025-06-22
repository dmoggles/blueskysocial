"""
Protocol definitions for BlueSky Social types.
"""

from typing import Protocol, Callable, Dict, Optional, Tuple, Any
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


class AspectRatioConsumerProtocol(Protocol):
    """
    Protocol defining the interface for an object that consumes aspect ratio data.

    This protocol defines the expected attributes and methods that an object
    should have to be compatible with aspect ratio specifications.
    """

    @property
    def data_accessor(self) -> str | bytes:
        """
        The data accessor for the aspect ratio consumer.  Provides the data that can be used to determine the aspect ratio.

        Returns:
            str|bytes: The data accessor, which can be a string or bytes.
        """
        ...

    @property
    def aspect_ratio_function(self) -> Callable[[Any], Optional[Dict[str, int]]]:
        """
        The function used to calculate the aspect ratio from the data accessor.
        This function should take the data accessor as input and return a dictionary
        containing the width and height of the aspect ratio.
        Returns:
            Callable[[str|bytes], Dict[str, int]]: A function that takes the data accessor and returns a dictionary with width and height.
        """
        ...

    @property
    def aspect_ratio(self) -> Optional[Tuple[int, int]]:
        """
        The aspect ratio of the data accessor.

        Returns:
            Optional[Tuple[int, int]]: A tuple containing the width and height of the aspect ratio, or None if not applicable.
        """
        ...

    @property
    def require_aspect_ratio(self) -> bool:
        """
        Whether the aspect ratio is required for the consumer.

        Returns:
            bool: True if the aspect ratio is required, False otherwise.
        """
        ...
