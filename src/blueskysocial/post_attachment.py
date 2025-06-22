from abc import ABC, abstractmethod
from blueskysocial.typedefs import ApiPayloadType, PostProtocol


class PostAttachment(ABC):
    """
    Abstract base class for post attachments.
    This class defines the interface for attaching an attachment to a post.
    Subclasses must implement the `attach_to_post` method.
    Methods
    -------
    attach_to_post(post, session: dict)
    """

    @abstractmethod
    def attach_to_post(self, post: PostProtocol, session: ApiPayloadType) -> None:
        """
        Attach the attachment to the post.
        """
