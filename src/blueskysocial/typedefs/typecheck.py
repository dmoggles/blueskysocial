from typing import Any
from bs4 import Tag


def as_str(value: Any) -> str:
    """
    Convert a value to a string, handling None and other types gracefully.

    Args:
        value (Any): The value to convert to a string.

    Returns:
        str: The string representation of the value, or an empty string if the value is None.
    """
    return str(value) if value is not None else ""


def as_bool(value: Any) -> bool:
    """
    Convert a value to a boolean, handling None and other types gracefully.

    Args:
        value (Any): The value to convert to a boolean.

    Returns:
        bool: The boolean representation of the value, or False if the value is None.
    """
    return bool(value) if value is not None else False


def as_int(value: Any) -> int:
    """
    Convert a value to an integer, handling None and other types gracefully.

    Args:
        value (Any): The value to convert to an integer.

    Returns:
        int: The integer representation of the value, or 0 if the value is None.
    """
    return int(value) if value is not None else 0


def as_bs4_tag(value: Any) -> Tag:
    """
    Convert a value to a string, handling None and other types gracefully.

    Args:
        value (Any): The value to convert to a string.

    Returns:
        Tag: The BeautifulSoup Tag representation of the value.
    """
    if isinstance(value, Tag):
        return value
    raise TypeError(
        f"Expected a BeautifulSoup Tag, got {type(value).__name__} instead."
    )
