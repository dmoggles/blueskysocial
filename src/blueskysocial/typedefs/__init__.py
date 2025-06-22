"""
Typing protocols and type definitions for BlueSky Social.
"""

from .protocols import (
    ConvoProtocol,
    DirectMessageProtocol,
    PostProtocol,
    AspectRatioConsumerProtocol,
)
from ._types import RecursiveStrDict, DictStrOrInt, ApiPayloadType
from .typecheck import as_str, as_bs4_tag, as_bool, as_int

__all__ = [
    "ConvoProtocol",
    "DirectMessageProtocol",
    "PostProtocol",
    "RecursiveStrDict",
    "as_str",
    "DictStrOrInt",
    "ApiPayloadType",
    "as_bs4_tag",
    "as_bool",
    "as_int",
    "AspectRatioConsumerProtocol",
]
