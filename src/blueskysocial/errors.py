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


class InvalidUserHandleError(Exception):
    """
    Exception raised when a user is invalid.

    This error is intended to be used when an operation requires a valid user handle,
    but the user provided is invalid.

    Attributes:
        None
    """


class PostTooLongError(Exception):
    """
    Exception raised when a post exceeds the maximum allowed length.

    This error is intended to be used when a post's content exceeds the platform's
    character limit.

    Attributes:
        None
    """


class ImageIsTooLargeError(Exception):
    """
    Exception raised when an image exceeds the maximum allowed size.

    This error is intended to be used when an image's file size exceeds the platform's
    limit for image uploads.

    Attributes:
        None
    """


class TooManyImagesError(Exception):
    """
    Exception raised when too many images are attached to a post.

    This error is intended to be used when a post exceeds the maximum number of
    allowed image attachments.

    Attributes:
        None
    """

    MAX_IMAGES = 4

    def __init__(self, images_count: int) -> None:
        """
        Initializes the TooManyImagesError with the count of images and the maximum allowed.

        Args:
            images_count (int): The number of images currently attached.
        """
        super().__init__(
            f"Too many images attached: {images_count} (max {self.MAX_IMAGES})"
        )
        self.images_count = images_count


class TooManyAttachmentsError(Exception):
    """
    Exception raised when too many attachments are added to a post.

    This error is intended to be used when a post exceeds the maximum number of
    allowed attachments.

    Attributes:
        None
    """

    MAX_ATTACHMENTS = 1

    def __init__(self, attachments_count: int) -> None:
        """
        Initializes the TooManyAttachmentsError with the count of attachments and the maximum allowed.

        Args:
            attachments_count (int): The number of attachments currently added.
        """
        super().__init__(
            f"Too many non-image attachments added: {attachments_count} (max {self.MAX_ATTACHMENTS})"
        )
        self.attachments_count = attachments_count


class InvalidAttachmentsError(Exception):
    """
    Exception raised when an attachment is invalid.

    This error is intended to be used when an operation requires a valid attachment,
    but the attachment provided is invalid.

    Attributes:
        None
    """


class UnknownAspectRatioError(Exception):
    """
    Exception raised when the aspect ratio of an image is unknown.

    This error is intended to be used when an operation requires a known aspect ratio,
    but the aspect ratio of the provided image cannot be determined.

    Attributes:
        None
    """
