"""
Wrapper class for a conversation in the BlueSky Social API.
"""

from typing import Dict, Any, List
import datetime as dt
import requests
from blueskysocial.convos.message import DirectMessage
from blueskysocial.convos.filters import Filter
from blueskysocial.api_endpoints import CHAT_SLUG, GET_MESSAGES, SEND_MESSAGE
from blueskysocial.utils import get_auth_header


class Convo:
    """
    A class to represent a conversation.
    Attributes:
    -----------
    raw_json : Dict[str, Any]
        The raw JSON data of the conversation.
    session : Dict[str, Any]
        The session data.
    Properties:
    -----------
    participant : str
        The handle of the other participant in the conversation.
    unread_count : int
        The number of unread messages in the conversation.
    opened : bool
        Whether the conversation has been opened.
    convo_id : str
        The ID of the conversation.
    last_message : str
        The text of the last message in the conversation.
    last_message_time : datetime
        The time the last message was sent.
    Methods:
    --------
    get_messages(filter: Filter = None) -> List[DirectMessage]
        Retrieves messages from the conversation, optionally filtered.
    send_message(text: str) -> DirectMessage
        Sends a message in the conversation.
    """

    def __init__(self, raw_json: Dict[str, Any], session: Dict[str, Any]):
        self._raw_json = raw_json
        self._session = session

    @property
    def participant(self):
        """
        Retrieve the handle of the participant in the conversation who is not the current session user.

        Returns:
            str: The handle of the other participant in the conversation.
        """
        return next(
            participant["handle"]
            for participant in self._raw_json["members"]
            if participant["handle"] != self._session["handle"]
        )

    @property
    def unread_count(self) -> int:
        """
        Returns the count of unread messages in the conversation.

        Returns:
            int: The number of unread messages.
        """
        return self._raw_json["unreadCount"]

    @property
    def opened(self) -> bool:
        """
        Check if the conversation has been opened.

        Returns:
            bool: True if the conversation has been opened, False otherwise.
        """
        return self._raw_json["opened"]

    @property
    def convo_id(self) -> str:
        """
        Retrieve the conversation ID from the raw JSON data.

        Returns:
            str: The conversation ID.
        """
        return self._raw_json["id"]

    @property
    def last_message(self) -> str:
        """
        Retrieve the text of the last message from the conversation.

        Returns:
            str: The text of the last message.
        """
        return self._raw_json["lastMessage"]["text"]

    @property
    def last_message_time(self) -> str:
        """
        Returns the timestamp of the last message in the conversation.

        The timestamp is extracted from the '_raw_json' attribute and is expected to be in the format
        "%Y-%m-%dT%H:%M:%S.%fZ".

        Returns:
            str: The timestamp of the last message as a string.
        """
        return dt.datetime.strptime(
            self._raw_json["lastMessage"]["sentAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )

    def get_messages(self, filter: Filter = None) -> List[DirectMessage]:
        """
        Retrieve messages from the conversation.

        Args:
            filter (Filter, optional): A filter function to apply to the messages.
                                       Only messages for which the filter function returns True will be included.
                                       Defaults to None.

        Returns:
            List[DirectMessage]: A list of DirectMessage objects representing the messages in the conversation.

        Raises:
            HTTPError: If the HTTP request to retrieve messages fails.
        """
        requests.get
        response = requests.get(
            CHAT_SLUG + GET_MESSAGES + "?convoId=" + self.convo_id,
            headers=get_auth_header(self._session["accessJwt"]),
        )
        response.raise_for_status()
        return [
            DirectMessage(message, self)
            for message in response.json()["messages"]
            if not filter or filter(DirectMessage(message, self))
        ]

    def send_message(self, text: str) -> DirectMessage:
        """
        Sends a direct message in the current conversation.

        Args:
            text (str): The text content of the message to be sent.

        Returns:
            DirectMessage: An instance of DirectMessage containing the response data.

        Raises:
            HTTPError: If the request to send the message fails.
        """
        response = requests.post(
            CHAT_SLUG + SEND_MESSAGE,
            headers=get_auth_header(self._session["accessJwt"]),
            json={"convoId": self.convo_id, "message": {"text": text}},
        )
        response.raise_for_status()
        return DirectMessage(response.json(), self)
