"""
Wrapper class for a direct message in the BlueSky Social API.
"""

from typing import Dict, Any, TYPE_CHECKING
import datetime as dt

if TYPE_CHECKING:
    from blueskysocial.convos.convo import Convo


class DirectMessage:
    """
    A class to represent a direct message in a conversation.
    Attributes:
    -----------
    raw_json : Dict[str, Any]
        The raw JSON data of the direct message.
    convo : Convo
        The conversation to which this direct message belongs.
    Methods:
    --------
    text() -> str:
        Returns the text content of the direct message.
    sent_at() -> dt.datetime:
        Returns the timestamp when the direct message was sent.
    convo() -> Convo:
        Returns the conversation to which this direct message belongs.
    """

    def __init__(self, raw_json: Dict[str, Any], convo: "Convo"):
        self._raw_json = raw_json
        self._convo = convo

    @property
    def text(self) -> str:
        """
        Retrieve the text content from the raw JSON data.

        Returns:
            str: The text content extracted from the raw JSON.
        """
        return self._raw_json["text"]

    @property
    def sent_at(self) -> dt.datetime:
        """
        Parses the 'sentAt' timestamp from the raw JSON data and returns it as a datetime object.

        Returns:
            datetime: The parsed datetime object representing when the message was sent.
        """
        return dt.datetime.strptime(self._raw_json["sentAt"], "%Y-%m-%dT%H:%M:%S.%fZ")

    @property
    def convo(self) -> "Convo":
        """
        Returns the conversation instance associated with this message.

        Returns:
            Convo: The conversation instance.
        """
        return self._convo
