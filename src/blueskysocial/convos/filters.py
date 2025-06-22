"""
This module defines a comprehensive set of filters and operands for evaluating conversations
based on various criteria in the BlueSky Social API.

The module implements a filter system with two main components:
1. Operands: Extract specific values from conversation objects
2. Filters: Apply comparison operations and logical combinations

Classes:
    Operand (ABC): Abstract base class for extracting values from conversations
    Filter (ABC): Abstract base class for filtering conversations

    Operands:
        UnreadCount: Extracts the unread message count from a conversation
        Participant: Extracts the participant handle from a conversation
        LastMessageTime: Extracts the last message timestamp from a conversation

    Comparison Filters:
        GT: Greater than comparison filter
        Eq: Equality comparison filter
        Neq: Not equal comparison filter
        LT: Less than comparison filter

    Logical Filters:
        And: Logical AND combination of multiple filters
        Or: Logical OR combination of multiple filters
        Not: Logical NOT negation of a filter

Example:
    # Filter for conversations with more than 5 unread messages
    unread_filter = GT(UnreadCount, 5)

    # Filter for conversations with a specific participant
    participant_filter = Eq(Participant, "user123")

    # Combine filters with logical operations
    combined_filter = And(unread_filter, participant_filter)
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Any, Type
from blueskysocial.typedefs import ConvoProtocol, DirectMessageProtocol, as_bool
import datetime as dt


def time_transform(value: dt.datetime | str | dt.date) -> dt.datetime:
    """
    Transform various date/time formats to a datetime object for comparison.

    Handles:
    - String dates in "YYYY-MM-DD" format
    - String datetimes in "YYYY-MM-DD HH:MM:SS" format
    - datetime.datetime objects (returned unchanged)
    - datetime.date objects (converted to datetime at midnight)

    Args:
        value (dt.datetime | str | dt.date): The comparison value to transform

    Returns:
        dt.datetime: A datetime object ready for comparison
    """
    if isinstance(value, str):
        try:
            return dt.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    if isinstance(value, dt.datetime):
        return value
    return dt.datetime(value.year, value.month, value.day)


T = TypeVar("T")


class Operand(ABC):
    """
    Abstract base class for operands used in filters.

    Operands are responsible for extracting specific values from conversation objects
    and transforming comparison values for filtering operations. They work in conjunction
    with Filter classes to create complete filtering expressions.

    This class defines the interface that all operands must implement:
    - extract(): Extract a value from a conversation object
    - rhs_transform(): Transform right-hand side values for comparison

    Methods:
        extract(convo): Abstract class method that extracts a value from a conversation
        rhs_transform(value): Abstract class method that transforms comparison values
    """

    @classmethod
    @abstractmethod
    def extract(cls, operatable: ConvoProtocol | DirectMessageProtocol) -> Any:
        """
        Extract a specific value from the given conversation.

        This method should be implemented by subclasses to extract relevant
        data from conversation objects (e.g., unread count, participant, timestamp).

        Args:
            operatable (ConvoProtocol|DirectMessageProtocol): The conversation object to extract from

        Returns:
            Any: The extracted value from the conversation
        """
        pass

    @classmethod
    @abstractmethod
    def rhs_transform(cls, value: Any) -> Any:
        """
        Transform the right-hand side value for comparison operations.

        This method allows operands to normalize or convert comparison values
        to match the format of extracted values. For example, converting string
        dates to datetime objects.

        Args:
            value (Any): The raw comparison value to be transformed

        Returns:
            Any: The transformed value ready for comparison
        """
        pass


class Filter(ABC):
    """
    Abstract base class for conversation filters.

    Filters are callable objects that evaluate conversations and return boolean results.
    They implement the __call__ method to make them function-like, allowing them to be
    used directly with conversation objects.

    All filters must implement the __call__ method which takes a conversation and returns
    a boolean indicating whether the conversation matches the filter criteria.

    The filter system supports:
    - Comparison filters (GT, Eq, Neq, LT) that compare operand values
    - Logical filters (And, Or, Not) that combine multiple filters

    Methods:
        __call__(convo): Abstract method that evaluates a conversation and returns bool

    Example:
        # Create a filter and use it
        my_filter = GT(UnreadCount, 5)
        result = my_filter(conversation)  # Returns True/False
    """

    @abstractmethod
    def __call__(
        self, convo_or_direct_message: ConvoProtocol | DirectMessageProtocol
    ) -> bool:
        """
        Evaluate the given conversation against this filter's criteria.

        This method makes Filter objects callable, allowing them to be used as
        functions that take a conversation and return a boolean result.

        Args:
            convo_or_direct_message (ConvoProtocol | DirectMessageProtocol): The conversation or direct message to evaluate

        Returns:
            bool: True if the conversation matches the filter criteria, False otherwise
        """
        pass


class UnreadCount(Operand):
    """
    Operand for extracting the unread message count from a conversation.

    This operand extracts the number of unread messages in a conversation,
    which can be used with comparison filters to filter conversations based
    on their unread message count.

    The rhs_transform method returns values unchanged since unread counts
    are already integers and don't need transformation.

    Methods:
        extract(convo): Returns the unread message count from the conversation
        rhs_transform(value): Returns the value unchanged (pass-through)

    Example:
        # Filter for conversations with more than 10 unread messages
        filter = GT(UnreadCount, 10)
    """

    @classmethod
    def extract(cls, operatable: ConvoProtocol | DirectMessageProtocol) -> int:
        """
        Extract the unread message count from a conversation.

        Args:
            operatable (ConvoProtocol | DirectMessageProtocol): The conversation object to extract from.  This can only be a ConvoProtocol object, not a DirectMessageProtocol object.

        Returns:
            int: The number of unread messages in the conversation
        """
        assert isinstance(
            operatable, ConvoProtocol
        ), "UnreadCount can only be applied to ConvoProtocol objects"
        return operatable.unread_count

    @classmethod
    def rhs_transform(cls, value: T) -> T:
        """
        Transform the right-hand side value for comparison.

        For UnreadCount, no transformation is needed since we're dealing
        with integer values that can be compared directly.

        Args:
            value (T): The comparison value (typically an integer)

        Returns:
            T: The same value unchanged
        """
        return value


class Participant(Operand):
    """
    Operand for extracting the participant handle from a conversation.

    This operand extracts the handle (username) of the other participant
    in a conversation, which can be used to filter conversations by who
    the user is chatting with.

    The rhs_transform method returns values unchanged since participant
    handles are already strings and don't need transformation.

    Methods:
        extract(convo): Returns the participant handle from the conversation
        rhs_transform(value): Returns the value unchanged (pass-through)

    Example:
        # Filter for conversations with a specific user
        filter = Eq(Participant, "alice.bsky.social")
    """

    @classmethod
    def extract(cls, operatable: ConvoProtocol | DirectMessageProtocol) -> str:
        """
        Extract the participant handle from a conversation.

        Args:
            operatable (ConvoProtocol | DirectMessageProtocol): The conversation object to extract from.  This can only be a ConvoProtocol object, not a DirectMessageProtocol object.

        Returns:
            str: The handle of the other participant in the conversation
        """
        assert isinstance(
            operatable, ConvoProtocol
        ), "Participant can only be applied to ConvoProtocol objects"
        return operatable.participant

    @classmethod
    def rhs_transform(cls, value: T) -> T:
        """
        Transform the right-hand side value for comparison.

        For Participant, no transformation is needed since we're dealing
        with string values that can be compared directly.

        Args:
            value (T): The comparison value (typically a string handle)

        Returns:
            T: The same value unchanged
        """
        return value


class LastMessageTime(Operand):
    """
    Operand for extracting the last message timestamp from a conversation.

    This operand extracts the datetime when the last message was sent in a
    conversation, which can be used to filter conversations based on recency
    or specific time ranges.

    The rhs_transform method handles various input formats for datetime
    comparison values, converting strings and dates to datetime objects
    for consistent comparison.

    Methods:
        extract(convo): Returns the last message timestamp from the conversation
        rhs_transform(value): Converts various date/time formats to datetime objects

    Example:
        # Filter for conversations with messages after a specific date
        filter = GT(LastMessageTime, "2023-01-01")

        # Or with a datetime object
        import datetime as dt
        filter = GT(LastMessageTime, dt.datetime(2023, 1, 1))
    """

    @classmethod
    def extract(cls, operatable: ConvoProtocol | DirectMessageProtocol) -> dt.datetime:
        """
        Extract the last message timestamp from a conversation.

        Args:
            operatable (ConvoProtocol | DirectMessageProtocol): The conversation object to extract from.  This can only be a ConvoProtocol object, not a DirectMessageProtocol object.

        Returns:
            dt.datetime: The timestamp when the last message was sent
        """
        assert isinstance(
            operatable, ConvoProtocol
        ), "LastMessageTime can only be applied to ConvoProtocol objects"
        return operatable.last_message_time

    @classmethod
    def rhs_transform(cls, value: dt.datetime | str | dt.date) -> dt.datetime:
        """
        Transform the right-hand side value to a datetime object for comparison.

        This method handles multiple input formats:
        - String dates in "YYYY-MM-DD" format
        - String datetimes in "YYYY-MM-DD HH:MM:SS" format
        - datetime.datetime objects (returned unchanged)
        - datetime.date objects (converted to datetime at midnight)

        Args:
            value (dt.datetime | str | dt.date): The comparison value to transform

        Returns:
            dt.datetime: A datetime object ready for comparison

        Raises:
            ValueError: If the string format is not recognized
        """
        return time_transform(value)


class SentAt(Operand):
    """
    A filter class to evaluate the sent time of a message in a conversation.

    Methods:
        evaluate(message):
            Evaluates the sent time of the message in the context of the given conversation.
            Returns the sent time of the message.
    """

    @classmethod
    def extract(cls, operatable: ConvoProtocol | DirectMessageProtocol) -> dt.datetime:
        """
        Extract the sent time from a direct message.
        Args:
            operatable (ConvoProtocol | DirectMessageProtocol): The conversation or direct message object to extract from. This can only be a DirectMessageProtocol object, not a ConvoProtocol object.
        Returns:
            dt.datetime: The sent time of the message.
        """
        assert isinstance(
            operatable, DirectMessageProtocol
        ), "SentAt can only be applied to DirectMessageProtocol objects"
        return operatable.sent_at

    @classmethod
    def rhs_transform(cls, value: dt.datetime | str | dt.date) -> dt.datetime:
        """
        Transform the right-hand side value to a datetime object for comparison.
        This method handles multiple input formats:
        - String dates in "YYYY-MM-DD" format
        - String datetimes in "YYYY-MM-DD HH:MM:SS" format
        - datetime.datetime objects (returned unchanged)
        - datetime.date objects (converted to datetime at midnight)
        Args:
            value (dt.datetime | str | dt.date): The comparison value to transform
        Returns:
            dt.datetime: A datetime object ready for comparison
        Raises:
            ValueError: If the string format is not recognized
        """
        return time_transform(value)


class GT(Filter):
    """
    Greater Than comparison filter.

    This filter evaluates to True when the operand's extracted value from a
    conversation is greater than the specified comparison value. The operand
    handles value extraction and transformation automatically.

    Attributes:
        operand (Operand): The operand that extracts values from conversations
        value (Any): The value to compare against the extracted values

    Methods:
        __init__(operand, value): Initialize the filter with an operand and comparison value
        __call__(convo): Evaluate if the operand's value is greater than the comparison value

    Example:
        # Filter for conversations with more than 5 unread messages
        unread_filter = GT(UnreadCount, 5)

        # Filter for conversations with recent messages (after yesterday)
        import datetime as dt
        yesterday = dt.datetime.now() - dt.timedelta(days=1)
        recent_filter = GT(LastMessageTime, yesterday)
    """

    def __init__(self, operand: Type[Operand], value: Any) -> None:
        """
        Initialize the Greater Than filter.

        Args:
            operand (Type[Operand]): The operand to extract values from conversations
            value (Any): The value to compare against (will be transformed by operand)
        """
        self.operand = operand
        self.value = value

    def __call__(
        self, convo_or_direct_message: ConvoProtocol | DirectMessageProtocol
    ) -> bool:
        """
        Evaluate if the operand's extracted value is greater than the comparison value.

        Args:
            convo_or_direct_message (ConvoProtocol | DirectMessageProtocol): The conversation or direct message to evaluate

        Returns:
            bool: True if extracted value > comparison value, False otherwise
        """
        return as_bool(
            self.operand.extract(convo_or_direct_message)
            > self.operand.rhs_transform(self.value)
        )


class Eq(Filter):
    """
    Equality comparison filter.

    This filter evaluates to True when the operand's extracted value from a
    conversation is equal to the specified comparison value. The operand
    handles value extraction and transformation automatically.

    Attributes:
        operand (Operand): The operand that extracts values from conversations
        value (Any): The value to compare against the extracted values

    Methods:
        __init__(operand, value): Initialize the filter with an operand and comparison value
        __call__(convo): Evaluate if the operand's value equals the comparison value

    Example:
        # Filter for conversations with a specific participant
        participant_filter = Eq(Participant, "alice.bsky.social")

        # Filter for conversations with exactly 0 unread messages
        read_filter = Eq(UnreadCount, 0)
    """

    def __init__(self, operand: Type[Operand], value: Any) -> None:
        """
        Initialize the Equality filter.

        Args:
            operand (Type[Operand]): The operand to extract values from conversations
            value (Any): The value to compare against (will be transformed by operand)
        """
        self.operand = operand
        self.value = value

    def __call__(
        self, convo_or_direct_message: ConvoProtocol | DirectMessageProtocol
    ) -> bool:
        """
        Evaluate if the operand's extracted value equals the comparison value.

        Args:
            convo_or_direct_message (ConvoProtocol | DirectMessageProtocol): The conversation or direct message to evaluate

        Returns:
            bool: True if extracted value == comparison value, False otherwise
        """
        return as_bool(
            self.operand.extract(convo_or_direct_message)
            == self.operand.rhs_transform(self.value)
        )


class Neq(Filter):
    """
    Not Equal comparison filter.

    This filter evaluates to True when the operand's extracted value from a
    conversation is not equal to the specified comparison value. The operand
    handles value extraction and transformation automatically.

    Attributes:
        operand (Operand): The operand that extracts values from conversations
        value (Any): The value to compare against the extracted values

    Methods:
        __init__(operand, value): Initialize the filter with an operand and comparison value
        __call__(convo): Evaluate if the operand's value is not equal to the comparison value

    Example:
        # Filter for conversations not with a specific participant
        not_alice_filter = Neq(Participant, "alice.bsky.social")

        # Filter for conversations that have unread messages (not 0)
        unread_filter = Neq(UnreadCount, 0)
    """

    def __init__(self, operand: Type[Operand], value: Any) -> None:
        """
        Initialize the Not Equal filter.

        Args:
            operand (Type[Operand]): The operand to extract values from conversations
            value (Any): The value to compare against (will be transformed by operand)
        """
        self.operand = operand
        self.value = value

    def __call__(
        self, convo_or_direct_message: ConvoProtocol | DirectMessageProtocol
    ) -> bool:
        """
        Evaluate if the operand's extracted value is not equal to the comparison value.

        Args:
            convo_or_direct_message (ConvoProtocol | DirectMessageProtocol): The conversation or direct message to evaluate

        Returns:
            bool: True if extracted value != comparison value, False otherwise
        """
        return as_bool(
            self.operand.extract(convo_or_direct_message)
            != self.operand.rhs_transform(self.value)
        )


class LT(Filter):
    """
    Less Than comparison filter.

    This filter evaluates to True when the operand's extracted value from a
    conversation is less than the specified comparison value. The operand
    handles value extraction and transformation automatically.

    Attributes:
        operand (Operand): The operand that extracts values from conversations
        value (Any): The value to compare against the extracted values

    Methods:
        __init__(operand, value): Initialize the filter with an operand and comparison value
        __call__(convo): Evaluate if the operand's value is less than the comparison value

    Example:
        # Filter for conversations with fewer than 3 unread messages
        low_unread_filter = LT(UnreadCount, 3)

        # Filter for conversations with messages before a specific date
        old_filter = LT(LastMessageTime, "2023-01-01")
    """

    def __init__(self, operand: Type[Operand], value: Any) -> None:
        """
        Initialize the Less Than filter.

        Args:
            operand (Type[Operand]): The operand to extract values from conversations
            value (Any): The value to compare against (will be transformed by operand)
        """
        self.operand = operand
        self.value = value

    def __call__(
        self, convo_or_direct_message: ConvoProtocol | DirectMessageProtocol
    ) -> bool:
        """
        Evaluate if the operand's extracted value is less than the comparison value.

        Args:
            convo_or_direct_message (ConvoProtocol | DirectMessageProtocol): The conversation or direct message to evaluate

        Returns:
            bool: True if extracted value < comparison value, False otherwise
        """
        return as_bool(
            self.operand.extract(convo_or_direct_message)
            < self.operand.rhs_transform(self.value)
        )


class And(Filter):
    """
    Logical AND combination filter.

    This filter evaluates to True only when ALL of its sub-filters evaluate to True
    for a given conversation. It implements short-circuit evaluation, stopping at
    the first filter that returns False.

    Attributes:
        args (tuple[Filter, ...]): A tuple of Filter objects to be combined with AND logic

    Methods:
        __init__(*args): Initialize with multiple filters to combine
        __call__(convo): Evaluate all filters and return True only if all are True

    Example:
        # Filter for conversations with Alice that have unread messages
        participant_filter = Eq(Participant, "alice.bsky.social")
        unread_filter = GT(UnreadCount, 0)
        combined_filter = And(participant_filter, unread_filter)

        # Can combine many filters
        complex_filter = And(
            GT(UnreadCount, 5),
            Neq(Participant, "spam.user"),
            GT(LastMessageTime, "2023-01-01")
        )
    """

    def __init__(self, *args: Filter) -> None:
        """
        Initialize the AND filter with multiple sub-filters.

        Args:
            *args (Filter): Variable number of Filter objects to combine with AND logic
        """
        self.args = args

    def __call__(
        self, convo_or_direct_message: ConvoProtocol | DirectMessageProtocol
    ) -> bool:
        """
        Evaluate all sub-filters against the conversation using AND logic.

        Uses short-circuit evaluation - returns False as soon as any sub-filter
        returns False, without evaluating the remaining filters.

        Args:
            convo_or_direct_message (ConvoProtocol | DirectMessageProtocol): The conversation or direct message to evaluate

        Returns:
            bool: True if ALL sub-filters return True, False otherwise
        """
        return all(arg(convo_or_direct_message) for arg in self.args)


class Or(Filter):
    """
    Logical OR combination filter.

    This filter evaluates to True when ANY of its sub-filters evaluate to True
    for a given conversation. It implements short-circuit evaluation, returning
    True as soon as any sub-filter returns True.

    Attributes:
        args (tuple[Filter, ...]): A tuple of Filter objects to be combined with OR logic

    Methods:
        __init__(*args): Initialize with multiple filters to combine
        __call__(convo): Evaluate filters and return True if any is True

    Example:
        # Filter for conversations with Alice OR Bob
        alice_filter = Eq(Participant, "alice.bsky.social")
        bob_filter = Eq(Participant, "bob.bsky.social")
        either_filter = Or(alice_filter, bob_filter)

        # Filter for urgent conversations (many unread OR very recent)
        many_unread = GT(UnreadCount, 10)
        very_recent = GT(LastMessageTime, "2023-12-01")
        urgent_filter = Or(many_unread, very_recent)
    """

    def __init__(self, *args: Filter) -> None:
        """
        Initialize the OR filter with multiple sub-filters.

        Args:
            *args (Filter): Variable number of Filter objects to combine with OR logic
        """
        self.args = args

    def __call__(
        self, convo_or_direct_message: ConvoProtocol | DirectMessageProtocol
    ) -> bool:
        """
        Evaluate sub-filters against the conversation using OR logic.

        Uses short-circuit evaluation - returns True as soon as any sub-filter
        returns True, without evaluating the remaining filters.

        Args:
            convo_or_direct_message (ConvoProtocol | DirectMessageProtocol): The conversation or direct message to evaluate

        Returns:
            bool: True if ANY sub-filter returns True, False if all return False
        """
        return any(arg(convo_or_direct_message) for arg in self.args)


class Not(Filter):
    """
    Logical NOT negation filter.

    This filter negates the result of another filter, evaluating to True when
    the sub-filter evaluates to False, and vice versa. This allows for creating
    inverse conditions easily.

    Attributes:
        arg (Filter): The single Filter object to be negated

    Methods:
        __init__(arg): Initialize with a single filter to negate
        __call__(convo): Evaluate the sub-filter and return the opposite result

    Example:
        # Filter for conversations NOT with Alice
        alice_filter = Eq(Participant, "alice.bsky.social")
        not_alice_filter = Not(alice_filter)

        # Filter for conversations that are NOT fully read (have unread messages)
        fully_read_filter = Eq(UnreadCount, 0)
        has_unread_filter = Not(fully_read_filter)

        # Negate complex filters
        urgent_filter = And(
            GT(UnreadCount, 5),
            GT(LastMessageTime, "2023-01-01")
        )
        not_urgent_filter = Not(urgent_filter)
    """

    def __init__(self, arg: Filter) -> None:
        """
        Initialize the NOT filter with a single sub-filter to negate.

        Args:
            arg (Filter): The Filter object whose result will be negated
        """
        self.arg = arg

    def __call__(
        self, convo_or_direct_message: ConvoProtocol | DirectMessageProtocol
    ) -> bool:
        """
        Evaluate the sub-filter and return the negated result.

        Args:
            convo_or_direct_message (ConvoProtocol | DirectMessageProtocol): The conversation or direct message to evaluate

        Returns:
            bool: True if the sub-filter returns False, False if the sub-filter returns True
        """
        return not self.arg(convo_or_direct_message)
