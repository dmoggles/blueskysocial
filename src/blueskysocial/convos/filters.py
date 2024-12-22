from abc import ABC, abstractmethod

"""
This module defines a set of filters for evaluating conversations based on various criteria.
Classes:
    Filter (ABC): An abstract base class for all filters.
        Methods:
            evaluate(convo): Abstract method to evaluate a conversation.
    UnreadCount (Filter): A filter to evaluate the unread count of a conversation.
        Methods:
            evaluate(convo): Returns the unread count of the conversation.
            value(value): Returns the provided value.
    Participant (Filter): A filter to evaluate the participant of a conversation.
        Methods:
            evaluate(convo): Returns the participant of the conversation.
            value(value): Returns the provided value.
    LastMessageDate (Filter): A filter to evaluate the last message date of a conversation.
        Methods:
            evaluate(convo): Returns the last message date of the conversation.
            value(value): Converts the provided value to a datetime object if necessary.
    GT (Filter): A filter to evaluate if a conversation attribute is greater than a given value.
        Methods:
            __init__(operand, value): Initializes the filter with an operand and a value.
            evaluate(convo): Returns True if the operand's value is greater than the provided value.
    Eq (Filter): A filter to evaluate if a conversation attribute is equal to a given value.
        Methods:
            __init__(operand, value): Initializes the filter with an operand and a value.
            evaluate(convo): Returns True if the operand's value is equal to the provided value.
    Neq (Filter): A filter to evaluate if a conversation attribute is not equal to a given value.
        Methods:
            __init__(operand, value): Initializes the filter with an operand and a value.
            evaluate(convo): Returns True if the operand's value is not equal to the provided value.
    LT (Filter): A filter to evaluate if a conversation attribute is less than a given value.
        Methods:
            __init__(operand, value): Initializes the filter with an operand and a value.
            evaluate(convo): Returns True if the operand's value is less than the provided value.
    And (Filter): A filter to evaluate if all provided filters are True for a conversation.
        Methods:
            __init__(*args): Initializes the filter with multiple filters.
            evaluate(convo): Returns True if all provided filters evaluate to True.
    Or (Filter): A filter to evaluate if any of the provided filters are True for a conversation.
        Methods:
            __init__(*args): Initializes the filter with multiple filters.
            evaluate(convo): Returns True if any of the provided filters evaluate to True.
"""
import datetime as dt


class Filter(ABC):
    """
    Abstract base class for conversation filters.
    This class defines the interface for filters that can be applied to conversations.
    Subclasses must implement the `evaluate` method to provide specific filtering logic.
    Methods:
        evaluate(convo): Abstract method that evaluates a conversation based on specific criteria.
    """

    @abstractmethod
    def evaluate(self, convo):
        """
        Evaluate the given conversation.

        Args:
            convo: The conversation object to be evaluated.

        Returns:
            None
        """
        pass


class UnreadCount(Filter):
    """
    UnreadCount is a filter class that provides methods to evaluate and return the unread count of a conversation.
    Methods:
        evaluate(cls, convo):
            Class method that takes a conversation object and returns its unread count.
        value(cls, value):
            Class method that takes a value and returns it as is.
    """

    @classmethod
    def evaluate(cls, convo):
        return convo.unread_count

    @classmethod
    def value(cls, value):
        return value


class Participant(Filter):
    """
    A filter class to evaluate and retrieve participant information from a conversation.
    Methods
    -------
    evaluate(cls, convo)
        Evaluates the given conversation and returns the participant.
    value(cls, value)
        Returns the provided value.
    """

    @classmethod
    def evaluate(cls, convo):
        return convo.participant

    @classmethod
    def value(cls, value):
        return value


class LastMessageTime(Filter):
    """
    A filter class to evaluate and convert the last message date of a conversation.
    Methods
    -------
    evaluate(cls, convo)
        Evaluates and returns the last message time of the given conversation.
    value(cls, value)
        Converts the given value to a datetime object if it is a string or date.
        If the value is a string, it is expected to be in the format '%Y-%m-%d'.
        If the value is a date, it is converted to a datetime object with the same year, month, and day.
        If the value is already a datetime object, it is returned as is.
    """

    @classmethod
    def evaluate(cls, convo):
        return convo.last_message_time

    @classmethod
    def value(cls, value):
        if isinstance(value, str):
            try:
                return dt.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        if isinstance(value, dt.datetime):
            return value
        if isinstance(value, dt.date):
            return dt.datetime(value.year, value.month, value.day)

        raise ValueError("Invalid value type. Expected str, date, or datetime object.")


class SentAt(Filter):
    """
    A filter class to evaluate the sent time of a message in a conversation.

    Methods:
        evaluate(message):
            Evaluates the sent time of the message in the context of the given conversation.
            Returns the sent time of the message.
    """

    @classmethod
    def evaluate(cls, message):
        return message.sent_at

    @classmethod
    def value(cls, value):
        return value


class GT(Filter):
    """
    A filter class that evaluates if the value of a given operand in a conversation
    is greater than a specified value.
    Attributes:
        operand: The operand whose value will be evaluated.
        value: The value to compare against the operand's value.
    Methods:
        evaluate(convo):
            Evaluates if the operand's value in the given conversation is greater
            than the specified value.
    """

    def __init__(self, operand, value):
        self.operand = operand
        self.value = value

    def evaluate(self, convo):
        return self.operand.evaluate(convo) > self.operand.value(self.value)


class Eq(Filter):
    """
    A filter that checks if the value of an operand is equal to a specified value.
    Attributes:
        operand: The operand whose value is to be compared.
        value: The value to compare against the operand's value.
    Methods:
        evaluate(convo):
            Evaluates the filter against a conversation object.
            Returns True if the operand's value is equal to the specified value, otherwise False.
    """

    def __init__(self, operand, value):
        self.operand = operand
        self.value = value

    def evaluate(self, convo):
        return self.operand.evaluate(convo) == self.operand.value(self.value)


class Neq(Filter):
    """
    A filter that evaluates to True if the operand's value is not equal to the specified value.
    Attributes:
        operand (Filter): The filter whose value is to be compared.
        value (Any): The value to compare against the operand's value.
    Methods:
        evaluate(convo):
            Evaluates the filter against a conversation object.
            Returns True if the operand's value is not equal to the specified value, False otherwise.
    """

    def __init__(self, operand, value):
        self.operand = operand
        self.value = value

    def evaluate(self, convo):
        return self.operand.evaluate(convo) != self.operand.value(self.value)


class LT(Filter):
    """
    A filter class that evaluates whether the value of an operand is less than a specified value.
    Attributes:
        operand: The operand whose value will be evaluated.
        value: The value to compare against the operand's value.
    Methods:
        evaluate(convo):
            Evaluates the operand's value in the context of the given conversation and
            returns True if it is less than the specified value, otherwise False.
    """

    def __init__(self, operand, value):
        self.operand = operand
        self.value = value

    def evaluate(self, convo):
        return self.operand.evaluate(convo) < self.operand.value(self.value)


class And(Filter):
    """
    A filter that combines multiple filters using a logical AND operation.
    Args:
        *args: A variable number of filter instances.
    Methods:
        evaluate(convo):
            Evaluates the conversation against all the provided filters.
            Returns True if all filters evaluate to True, otherwise False.
    """

    def __init__(self, *args):
        self.args = args

    def evaluate(self, convo):
        return all(arg.evaluate(convo) for arg in self.args)


class Or(Filter):
    """
    A filter that evaluates to True if any of its sub-filters evaluate to True.
    Attributes:
        args (tuple): A tuple of sub-filters to be evaluated.
    Methods:
        evaluate(convo):
            Evaluates the conversation against all sub-filters and returns True if any sub-filter evaluates to True.
    """

    def __init__(self, *args):
        self.args = args

    def evaluate(self, convo):
        return any(arg.evaluate(convo) for arg in self.args)


class Not(Filter):
    """
    A filter that negates the result of a sub-filter.
    Attributes:
        arg (Filter): The sub-filter to be negated.
    Methods:
        evaluate(convo):
            Evaluates the conversation against the sub-filter
            and returns the negation of the sub-filter's result.
    """

    def __init__(self, arg):
        self.arg = arg

    def evaluate(self, convo):
        return not self.arg.evaluate(convo)
