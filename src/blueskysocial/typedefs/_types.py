"""
Custom type definitions for BlueSky Social.

This module provides custom type aliases and recursive type definitions
used throughout the BlueSky Social library.
"""

from typing import Dict, Union, TypeAlias, List, Any

# Recursive dictionary type that can contain strings or nested dictionaries
RecursiveStrDict: TypeAlias = Dict[str, Union[str, List[str], "RecursiveStrDict"]]
DictStrOrInt: TypeAlias = Dict[str, Union[str, int]]
ApiPayloadType: TypeAlias = Dict[str, Any]
