"""
Wrapper class for a direct message in the BlueSky Social API.

This module provides the DirectMessage class which represents individual messages
within conversations. DirectMessage objects are typically created when retrieving
messages from a conversation and provide access to message content, metadata,
and the associated conversation.

Classes:
    DirectMessage: Represents a single direct message with text content, timestamp,
                  and conversation context.

Example:
    # DirectMessage objects are typically obtained from a conversation
    messages = conversation.get_messages()
    for message in messages:
        print(f"{message.sent_at}: {message.text}")
        print(f"Conversation with: {message.convo.participant}")
"""

from typing import Dict, Any
import datetime as dt
from blueskysocial.typedefs import ConvoProtocol, as_str


class DirectMessage:
    """
    Represents a single direct message within a BlueSky Social conversation.

    This class wraps the raw JSON data for a direct message and provides convenient
    access to message properties like text content, timestamp, and the associated
    conversation. DirectMessage objects are typically created when retrieving
    messages from a conversation.

    The class uses properties to provide clean access to the underlying JSON data
    while handling necessary data transformations (like parsing timestamps).

    Attributes:
        _raw_json (Dict[str, Any]): The raw JSON data from the BlueSky API containing
                                   message details like text, sentAt timestamp, etc.
        _convo (ConvoProtocol): The conversation object that this message belongs to

    Properties:
        text (str): The text content of the message
        sent_at (dt.datetime): The timestamp when the message was sent
        convo (ConvoProtocol): The conversation this message belongs to

    Example:
        # DirectMessage objects are typically created by the conversation's get_messages method
        messages = conversation.get_messages()
        message = messages[0]

        print(f"Message: {message.text}")
        print(f"Sent at: {message.sent_at}")
        print(f"From conversation with: {message.convo.participant}")
    """

    def __init__(self, raw_json: Dict[str, Any], convo: ConvoProtocol) -> None:
        """
        Initialize a DirectMessage instance.

        Creates a new DirectMessage object from raw JSON data and associates it
        with a conversation. This constructor is typically called internally by
        the conversation's get_messages method when processing API responses.

        Args:
            raw_json (Dict[str, Any]): The raw JSON data from the BlueSky API
                                      containing message details. Expected to have
                                      keys like 'text', 'sentAt', etc.
            convo (ConvoProtocol): The conversation object that this message
                                  belongs to, providing context and access to
                                  conversation-level operations.

        Example:
            # Typically called internally by conversation methods
            raw_message_data = {
                "text": "Hello, world!",
                "sentAt": "2023-01-01T12:00:00.000Z",
                # ... other message fields
            }
            message = DirectMessage(raw_message_data, conversation)
        """
        self._raw_json = raw_json
        self._convo = convo

    @property
    def text(self) -> str:
        """
        Get the text content of the direct message.

        Extracts and returns the message text from the raw JSON data. This is
        the main content of the message that was sent by the user.

        Returns:
            str: The text content of the message as sent by the user.
                Empty string if no text content is present.

        Example:
            message = conversation.get_messages()[0]
            print(f"Message content: {message.text}")

            # Output: Message content: Hello, how are you doing?
        """
        return as_str(self._raw_json["text"])

    @property
    def sent_at(self) -> dt.datetime:
        """
        Get the timestamp when the direct message was sent.

        Parses the 'sentAt' field from the raw JSON data and converts it from
        the BlueSky API's ISO 8601 timestamp format to a Python datetime object.
        The timestamp represents when the message was originally sent.

        Returns:
            dt.datetime: A datetime object representing when the message was sent,
                        in UTC timezone. The datetime includes microsecond precision.

        Raises:
            ValueError: If the timestamp format in the raw JSON doesn't match
                       the expected ISO 8601 format "%Y-%m-%dT%H:%M:%S.%fZ"
            KeyError: If the 'sentAt' field is missing from the raw JSON data

        Example:
            message = conversation.get_messages()[0]
            timestamp = message.sent_at
            print(f"Message sent at: {timestamp}")
            print(f"Date only: {timestamp.date()}")
            print(f"Time only: {timestamp.time()}")

            # Output:
            # Message sent at: 2023-01-01 12:30:45.123456
            # Date only: 2023-01-01
            # Time only: 12:30:45.123456
        """
        return dt.datetime.strptime(self._raw_json["sentAt"], "%Y-%m-%dT%H:%M:%S.%fZ")

    @property
    def convo(self) -> ConvoProtocol:
        """
        Get the conversation that this message belongs to.

        Returns the conversation object that contains this message, providing
        access to conversation-level properties and methods. This allows you
        to navigate from a message back to its conversation context.

        Returns:
            ConvoProtocol: The conversation object that this message is part of.
                          Provides access to conversation properties like participant,
                          unread_count, and methods like get_messages(), send_message().

        Example:
            messages = conversation.get_messages()
            message = messages[0]

            # Access conversation properties through the message
            participant = message.convo.participant
            unread_count = message.convo.unread_count

            print(f"This message is from conversation with: {participant}")
            print(f"Conversation has {unread_count} unread messages")

            # Send a reply in the same conversation
            reply = message.convo.send_message("Thanks for your message!")
        """
        return self._convo
