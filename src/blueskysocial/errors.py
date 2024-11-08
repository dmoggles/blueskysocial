"""
Custom exceptions for the blueskysocial package.
"""


class SessionNotAuthenticatedError(Exception):
    """
    Exception raised when a session is not authenticated.

    This error is intended to be used when an operation requires an authenticated
    session, but the session provided is not authenticated.

    Attributes:
        None
    """
