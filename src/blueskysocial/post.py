"""
Post creation and management for BlueSky Social.

This module provides the Post class which handles creating, formatting, and building
posts for the BlueSky Social platform. It supports rich text features including
mentions, hashtags, URLs, and multimedia attachments.

The Post class handles:
- Text content with automatic facet parsing (mentions, hashtags, URLs)
- Multimedia attachments (images and videos)
- Rich text formatting with markdown-style links
- Language specification
- Character encoding and byte index management
- Attachment validation and limits

Key Features:
- Automatic parsing of @mentions with handle resolution
- Hashtag detection and processing
- URL detection and link creation
- Markdown-style rich links [text](url)
- Image and video attachment support
- Multi-language post support
- Character limit enforcement (300 characters)

Classes:
    Post: Main class for creating and managing BlueSky Social posts

Example:
    # Create a simple text post
    post = Post("Hello, world!")

    # Create a post with mentions and hashtags
    post = Post("Hello @alice.bsky.social! Check out #bluesky")

    # Create a post with image attachments
    from blueskysocial.image import Image
    image = Image("photo.jpg", alt_text="A beautiful sunset")
    post = Post("Check out this photo!", with_attachments=image)

    # Build the post for submission
    built_post = post.build(session)
"""

from typing import List, Dict, Union, Optional, Any, cast
from datetime import datetime, timezone
import re
import requests

from blueskysocial.api_endpoints import (
    POST_TYPE,
    MENTION_TYPE,
    LINK_TYPE,
    RPC_SLUG,
    RESOLVE_HANDLE,
    HASHTAG_TYPE,
)
from blueskysocial.image import Image
from blueskysocial.video import Video
from blueskysocial.post_attachment import PostAttachment
from blueskysocial.typedefs import ApiPayloadType, as_str, DictStrOrInt
from blueskysocial.errors import (
    PostTooLongError,
    TooManyAttachmentsError,
    TooManyImagesError,
    InvalidAttachmentsError,
)


class Post:
    """
    Represents and manages a BlueSky Social post with rich text and media features.

    The Post class handles the complete lifecycle of a social media post, from content
    parsing and attachment management to final API-ready structure building. It
    automatically processes rich text features like mentions, hashtags, and URLs,
    while managing multimedia attachments with proper validation.

    Key capabilities:
    - Automatic facet parsing for @mentions, #hashtags, and URLs
    - Rich link formatting with markdown syntax [text](url)
    - Image and video attachment support with validation
    - Multi-language post support
    - Character limit enforcement
    - Proper Unicode and byte index handling

    Attributes:
        content_str (str): The original post content string
        attachments (List[PostAttachment]): List of media attachments
        _post (ApiPayloadType): The internal post structure for API submission

    Args:
        content (str): The text content of the post. Supports rich text features
                      like @mentions, #hashtags, URLs, and [text](url) links.
        with_attachments (Optional[Union[PostAttachment, List[PostAttachment]]]):
                         Media attachments to include. Can be a single attachment
                         or list of attachments. Cannot mix images and videos.

    Raises:
        InvalidAttachmentsError: If trying to mix video and image attachments
        TooManyImagesError: If more than the maximum number of images are provided
        TooManyAttachmentsError: If more than the maximum number of attachments are provided
        PostTooLongError: If the post content exceeds 300 characters (raised during build)

    Examples:
        # Simple text post
        post = Post("Hello, BlueSky!")

        # Post with mentions and hashtags
        post = Post("Hello @alice.bsky.social! Loving #bluesky #decentralized")

        # Post with rich link
        post = Post("Check out [BlueSky](https://bsky.app)!")

        # Post with image attachment
        from blueskysocial.image import Image
        image = Image("sunset.jpg", alt_text="Beautiful sunset over the ocean")
        post = Post("Amazing sunset tonight!", with_attachments=image)

        # Post with multiple images
        images = [
            Image("pic1.jpg", alt_text="First photo"),
            Image("pic2.jpg", alt_text="Second photo")
        ]
        post = Post("Photo gallery:", with_attachments=images)
    """

    def __init__(
        self,
        content: str,
        with_attachments: Optional[Union[PostAttachment, List[PostAttachment]]] = None,
    ) -> None:
        """
        Initialize a new Post instance with content and optional attachments.

        Creates a new post with the specified text content and media attachments.
        Performs validation to ensure attachments are compatible (cannot mix
        images and videos) and don't exceed platform limits.

        Args:
            content (str): The text content of the post. Can include rich text
                          features like @mentions, #hashtags, URLs, and markdown
                          links [text](url). Maximum 300 characters after processing.
            with_attachments (Optional[Union[PostAttachment, List[PostAttachment]]]):
                            Media attachments to include with the post. Can be:
                            - None: No attachments
                            - Single PostAttachment: One image or video
                            - List[PostAttachment]: Multiple attachments (all same type)
                            Cannot mix Image and Video attachments in the same post.

        Raises:
            InvalidAttachmentsError: If trying to include both video and image
                                   attachments in the same post
            TooManyImagesError: If providing more images than the platform allows
            TooManyAttachmentsError: If providing more attachments than allowed

        Examples:
            # Text-only post
            post = Post("Hello, world!")

            # Post with single image
            image = Image("photo.jpg", alt_text="A photo")
            post = Post("Check this out!", with_attachments=image)

            # Post with multiple images
            images = [Image("1.jpg"), Image("2.jpg")]
            post = Post("Photo album:", with_attachments=images)

            # Invalid: mixing image and video (raises InvalidAttachmentsError)
            # post = Post("Mixed media", with_attachments=[image, video])
        """
        self._assert_dont_have_video_and_images(with_attachments)
        self.attachments = []
        if with_attachments:
            if isinstance(with_attachments, list):
                self.attachments = with_attachments
            else:
                self.attachments = [with_attachments]

        self.verify_attachments()

        self.content_str = content

        self._post: ApiPayloadType = {
            "$type": POST_TYPE,
            "text": content,
        }

    def _assert_dont_have_video_and_images(
        self, attachments: Optional[Union[PostAttachment, List[PostAttachment]]]
    ) -> None:
        """
        Validate that attachments don't mix video and image types.

        BlueSky Social posts cannot contain both video and image attachments
        simultaneously. This method enforces that constraint by checking
        the attachment types and raising an error if both are present.

        Args:
            attachments (Optional[Union[PostAttachment, List[PostAttachment]]]):
                        The attachments to validate. Can be None, a single
                        attachment, or a list of attachments.

        Raises:
            InvalidAttachmentsError: If the attachments contain both Video and
                                   Image instances, which is not allowed by the platform.

        Examples:
            # Valid: single attachment (no validation needed)
            self._assert_dont_have_video_and_images(image)

            # Valid: all images
            self._assert_dont_have_video_and_images([image1, image2])

            # Valid: single video
            self._assert_dont_have_video_and_images(video)

            # Invalid: mixed types (raises InvalidAttachmentsError)
            # self._assert_dont_have_video_and_images([image, video])
        """
        if isinstance(attachments, PostAttachment):
            return  # Single attachment, no need to check
        if attachments:
            has_video = any(isinstance(attachment, Video) for attachment in attachments)
            has_images = any(
                isinstance(attachment, Image) for attachment in attachments
            )
            if has_video and has_images:
                raise InvalidAttachmentsError(
                    "A post cannot contain both video and images."
                )

    @property
    def post(self) -> ApiPayloadType:
        """
        Get the internal post structure for API submission.

        Returns the underlying dictionary that represents the post in the format
        expected by the BlueSky API. This structure is built incrementally as
        the post is processed and contains all the metadata, facets, and content.

        Returns:
            ApiPayloadType: The post dictionary containing:
                - $type: The post type identifier
                - text: The processed text content
                - createdAt: Timestamp (added during build())
                - facets: Rich text features (added during build())
                - embed: Media attachments (added during build())
                - langs: Language codes (if specified)

        Example:
            post = Post("Hello @alice.bsky.social!")
            internal_structure = post.post
            # Returns: {"$type": "app.bsky.feed.post", "text": "Hello @alice.bsky.social!"}

            # After building:
            post.build(session)
            full_structure = post.post
            # Now includes createdAt, facets, etc.
        """
        return self._post

    def verify_attachments(self) -> None:
        """
        Validate attachment count against platform limits.

        Checks that the number of attachments doesn't exceed BlueSky Social's
        limits. Different limits apply based on attachment type:
        - Images: Limited by TooManyImagesError.MAX_IMAGES
        - Other attachments: Limited by TooManyAttachmentsError.MAX_ATTACHMENTS

        Raises:
            TooManyImagesError: If the number of image attachments exceeds the
                              maximum allowed (includes the actual count)
            TooManyAttachmentsError: If the number of non-image attachments
                                   exceeds the maximum allowed (includes the actual count)

        Examples:
            # Valid: within image limits
            post = Post("Photos", with_attachments=[image1, image2])  # Assuming ≤ MAX_IMAGES

            # Invalid: too many images (raises TooManyImagesError)
            # many_images = [Image(f"pic{i}.jpg") for i in range(20)]
            # post = Post("Too many photos", with_attachments=many_images)

            # Invalid: too many video attachments (raises TooManyAttachmentsError)
            # many_videos = [Video(f"vid{i}.mp4") for i in range(10)]
            # post = Post("Too many videos", with_attachments=many_videos)
        """
        if all(isinstance(attachment, Image) for attachment in self.attachments):
            if len(self.attachments) > TooManyImagesError.MAX_IMAGES:
                raise TooManyImagesError(len(self.attachments))
        else:
            if len(self.attachments) > TooManyAttachmentsError.MAX_ATTACHMENTS:
                raise TooManyAttachmentsError(len(self.attachments))

    def add_languages(self, languages: List[str]) -> "Post":
        """
        Add language codes to specify the post's languages.

        Sets the languages for the post content, which helps with content
        discovery and accessibility. Language codes should follow ISO 639-1
        or BCP 47 standards (e.g., 'en', 'es', 'fr', 'en-US').

        Args:
            languages (List[str]): A list of language codes representing the
                                 languages used in the post content. Common codes:
                                 - 'en': English
                                 - 'es': Spanish
                                 - 'fr': French
                                 - 'de': German
                                 - 'ja': Japanese
                                 - 'en-US': American English
                                 - 'pt-BR': Brazilian Portuguese

        Returns:
            Post: The same Post instance for method chaining

        Examples:
            # Single language
            post = Post("Hello, world!").add_languages(['en'])

            # Multiple languages for multilingual content
            post = Post("Hello! ¡Hola! Bonjour!").add_languages(['en', 'es', 'fr'])

            # Method chaining
            post = (Post("Multilingual content")
                   .add_languages(['en', 'es'])
                   .build(session))
        """
        self._post["langs"] = languages
        return self

    def _byte_index_to_char_index(self, text: str, byte_index: int) -> int:
        """
        Convert a byte index to a character index in a Unicode string.

        BlueSky's API uses byte indices for text ranges, but Python string
        operations use character indices. This method converts between the two,
        handling multi-byte Unicode characters correctly.

        Args:
            text (str): The Unicode string to index into
            byte_index (int): The byte position in the UTF-8 encoded version
                            of the string

        Returns:
            int: The corresponding character position in the Unicode string.
                Returns 0 for byte_index 0, and len(text) for byte indices
                beyond the string length.

        Examples:
            # ASCII text (1 byte per character)
            text = "Hello"
            char_idx = self._byte_index_to_char_index(text, 3)  # Returns 3

            # Unicode text with multi-byte characters
            text = "Hello 🌍"  # Earth emoji is 4 bytes
            char_idx = self._byte_index_to_char_index(text, 9)  # Returns 7 (after emoji)
        """
        if byte_index == 0:
            return 0

        # Get the UTF-8 bytes up to the byte_index
        text_bytes = text.encode("utf-8")
        if byte_index >= len(text_bytes):
            return len(text)

        # Decode the bytes up to byte_index back to characters
        # Use 'ignore' to handle partial multi-byte characters
        partial_text = text_bytes[:byte_index].decode("utf-8", errors="ignore")
        return len(partial_text)

    def _char_index_to_byte_index(self, text: str, char_index: int) -> int:
        """
        Convert a character index to a byte index in the UTF-8 encoded string.

        The inverse of _byte_index_to_char_index, this method converts from
        Python's character-based string indexing to the byte-based indexing
        used by BlueSky's API for text ranges.

        Args:
            text (str): The Unicode string to index into
            char_index (int): The character position in the Unicode string

        Returns:
            int: The corresponding byte position in the UTF-8 encoded version
                of the string. Returns 0 for char_index 0, and the total byte
                length for character indices beyond the string length.

        Examples:
            # ASCII text (1 byte per character)
            text = "Hello"
            byte_idx = self._char_index_to_byte_index(text, 3)  # Returns 3

            # Unicode text with multi-byte characters
            text = "Hello 🌍"  # Earth emoji is 4 bytes
            byte_idx = self._char_index_to_byte_index(text, 7)  # Returns 9 (after emoji)
        """
        if char_index == 0:
            return 0

        if char_index >= len(text):
            return len(text.encode("utf-8"))

        # Get the characters up to char_index and encode to get byte length
        char_substring = text[:char_index]
        return len(char_substring.encode("utf-8"))

    def _handle_first_rich_url(self) -> DictStrOrInt | None:
        """
        Process the first markdown-style rich URL in the post text.

        Finds and processes markdown-style links in the format [text](url),
        removing the markdown syntax and keeping only the display text while
        returning the URL information for facet creation.

        This method modifies the post text in-place, removing the markdown
        syntax but preserving the link text. It handles Unicode properly
        by working with byte indices and converting to character indices.

        Returns:
            DictStrOrInt | None: A dictionary containing the processed link info:
                - "start": Character index where the link text starts
                - "end": Character index where the link text ends
                - "url": The URL from the markdown link
                Returns None if no markdown link is found.

        Examples:
            # Before: "Check out [BlueSky](https://bsky.app)!"
            # After: "Check out BlueSky!"
            # Returns: {"start": 10, "end": 17, "url": "https://bsky.app"}

            # Before: "Visit [the site](http://example.com) for info"
            # After: "Visit the site for info"
            # Returns: {"start": 6, "end": 14, "url": "http://example.com"}
        """
        regex = rb"\[(.*?)\]\(\s*(https?://[^\s)]+)\s*\)"
        text_str = as_str(self._post["text"])
        text_bytes = text_str.encode("UTF-8")

        m = re.search(regex, text_bytes)
        if m:
            # Convert byte indices to character indices
            char_start_bracket = self._byte_index_to_char_index(text_str, m.start(0))
            char_start_text = self._byte_index_to_char_index(text_str, m.start(1))
            char_end_text = self._byte_index_to_char_index(text_str, m.end(1))
            char_end_full = self._byte_index_to_char_index(text_str, m.end(0))

            # Reconstruct the text by removing the markdown syntax but keeping the link text
            new_text = (
                text_str[:char_start_bracket]
                + text_str[char_start_text:char_end_text]
                + text_str[char_end_full:]
            )

            # Calculate the new position of the link text in the processed text
            # It starts where the bracket was, since we remove the bracket
            new_start = char_start_bracket
            new_end = char_start_bracket + (char_end_text - char_start_text)

            span: DictStrOrInt = {
                "start": new_start,
                "end": new_end,
                "url": m.group(2).decode("UTF-8"),
            }

            # Update the post text
            self._post["text"] = new_text
            return span
        return None

    def _parse_rich_urls(self) -> List[DictStrOrInt]:
        """
        Parse all markdown-style rich URLs from the post content.

        Processes all markdown-style links in the format [text](url) by repeatedly
        calling _handle_first_rich_url() until no more are found. This method
        modifies the post text to remove markdown syntax while preserving the
        display text, and returns information about all the links found.

        The method resets the post text to the original content before processing
        to ensure consistent parsing results.

        Returns:
            List[DictStrOrInt]: A list of dictionaries, each containing:
                - "start": Character index where the link text starts (after processing)
                - "end": Character index where the link text ends (after processing)
                - "url": The URL from the markdown link

        Examples:
            # Input: "Check [BlueSky](https://bsky.app) and [Mastodon](https://mastodon.social)!"
            # Final text: "Check BlueSky and Mastodon!"
            # Returns: [
            #     {"start": 6, "end": 13, "url": "https://bsky.app"},
            #     {"start": 18, "end": 26, "url": "https://mastodon.social"}
            # ]

            # Input: "No markdown links here"
            # Returns: []
        """
        self._post["text"] = self.content_str
        spans: List[DictStrOrInt] = []
        while True:
            span = self._handle_first_rich_url()
            if span:
                spans.append(span)
            else:
                break
        return spans

    def _parse_mentions(self) -> List[DictStrOrInt]:
        """
        Parse @mentions from the post content.

        Finds all @mention patterns in the post text using a regex based on
        BlueSky's handle identifier syntax. Mentions must be preceded by a
        word boundary and follow the domain name format (e.g., @user.bsky.social).

        Returns:
            List[DictStrOrInt]: A list of dictionaries, each containing:
                - "start": Character index where the @mention starts
                - "end": Character index where the @mention ends
                - "handle": The handle without the @ symbol (e.g., "user.bsky.social")

        Examples:
            # Input: "Hello @alice.bsky.social and @bob.example.com!"
            # Returns: [
            #     {"start": 6, "end": 23, "handle": "alice.bsky.social"},
            #     {"start": 28, "end": 43, "handle": "bob.example.com"}
            # ]

            # Input: "Email me at user@domain.com (not a mention)"
            # Returns: [] (email addresses are not mentions due to regex design)
        """
        spans: List[DictStrOrInt] = []
        # regex based on: https://atproto.com/specs/handle#handle-identifier-syntax
        mention_regex = rb"[$|\W](@([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
        text_str = as_str(self._post["text"])

        text_bytes = text_str.encode("UTF-8")
        for m in re.finditer(mention_regex, text_bytes):
            spans.append(
                {
                    "start": self._byte_index_to_char_index(text_str, m.start(1)),
                    "end": self._byte_index_to_char_index(text_str, m.end(1)),
                    "handle": m.group(1)[1:].decode("UTF-8"),
                }
            )
        return spans

    def _parse_hashtags(self) -> List[DictStrOrInt]:
        """
        Parse #hashtags from the post content.

        Finds all hashtag patterns in the post text using a regex that matches
        # symbols followed by word characters. Hashtags must be preceded by
        a word boundary to avoid matching # symbols within words.

        Returns:
            List[DictStrOrInt]: A list of dictionaries, each containing:
                - "start": Character index where the #hashtag starts
                - "end": Character index where the #hashtag ends
                - "tag": The hashtag text without the # symbol (e.g., "bluesky")

        Examples:
            # Input: "Loving #bluesky and #decentralized social media! #web3"
            # Returns: [
            #     {"start": 7, "end": 15, "tag": "bluesky"},
            #     {"start": 20, "end": 33, "tag": "decentralized"},
            #     {"start": 49, "end": 53, "tag": "web3"}
            # ]

            # Input: "Price is $#100 (not a hashtag)"
            # Returns: [] (# not preceded by word boundary)
        """
        spans: List[DictStrOrInt] = []
        # regex based on: https://stackoverflow.com/a/2166801
        hashtag_regex = rb"[\W](#\w+)"
        text_str = as_str(self._post["text"])
        text_bytes = text_str.encode("UTF-8")
        for m in re.finditer(hashtag_regex, text_bytes):
            spans.append(
                {
                    "start": self._byte_index_to_char_index(text_str, m.start(1)),
                    "end": self._byte_index_to_char_index(text_str, m.end(1)),
                    "tag": m.group(1)[1:].decode("UTF-8"),
                }
            )
        return spans

    def _parse_urls(self) -> List[DictStrOrInt]:
        """
        Parse plain URLs from the post content.

        Finds HTTP and HTTPS URLs in the post text using a regex pattern.
        This method handles plain URLs (not markdown-style rich links) and
        excludes some trailing punctuation to avoid including sentence-ending
        punctuation in the URL.

        Returns:
            List[DictStrOrInt]: A list of dictionaries, each containing:
                - "start": Character index where the URL starts
                - "end": Character index where the URL ends
                - "url": The complete URL string

        Examples:
            # Input: "Visit https://bsky.app for more info!"
            # Returns: [
            #     {"start": 6, "end": 21, "url": "https://bsky.app"}
            # ]

            # Input: "Check http://example.com and https://www.test.co.uk/path?param=value"
            # Returns: [
            #     {"start": 6, "end": 25, "url": "http://example.com"},
            #     {"start": 30, "end": 71, "url": "https://www.test.co.uk/path?param=value"}
            # ]
        """
        spans: List[DictStrOrInt] = []
        # partial/naive URL regex based on: https://stackoverflow.com/a/3809435
        # tweaked to disallow some training punctuation
        url_regex = rb"[$|\W](https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
        text_str = as_str(self._post["text"])
        text_bytes = text_str.encode("UTF-8")
        for m in re.finditer(url_regex, text_bytes):
            spans.append(
                {
                    "start": self._byte_index_to_char_index(text_str, m.start(1)),
                    "end": self._byte_index_to_char_index(text_str, m.end(1)),
                    "url": m.group(1).decode("UTF-8"),
                }
            )
        return spans

    def parse_facets(self) -> List[ApiPayloadType]:
        """
        Parse all rich text features (facets) from the post content.

        Analyzes the post text to identify and create facets for:
        - Rich URLs from markdown [text](url) syntax
        - @mentions with handle resolution via BlueSky API
        - Plain URLs (HTTP/HTTPS)
        - #hashtags

        Each facet includes byte-based index information (required by BlueSky API)
        and feature metadata. Mentions are resolved to DIDs (Decentralized
        Identifiers) via API calls, with invalid handles gracefully skipped.

        Returns:
            List[ApiPayloadType]: A list of facet dictionaries, each containing:
                - 'index': Byte-based start/end positions in the text
                    - 'byteStart': Starting byte position
                    - 'byteEnd': Ending byte position
                - 'features': List of feature objects with type and metadata:
                    - Links: {"$type": "app.bsky.richtext.facet#link", "uri": "..."}
                    - Mentions: {"$type": "app.bsky.richtext.facet#mention", "did": "..."}
                    - Hashtags: {"$type": "app.bsky.richtext.facet#tag", "tag": "..."}

        The facets are sorted by byte position to ensure consistent ordering.

        Examples:
            # Input: "Hello @alice.bsky.social! Check out https://bsky.app #awesome"
            # Returns facets for:
            # 1. @alice.bsky.social (mention with resolved DID)
            # 2. https://bsky.app (link)
            # 3. #awesome (hashtag)

            # Input: "Visit [BlueSky](https://bsky.app) - it's #amazing!"
            # Returns facets for:
            # 1. BlueSky -> https://bsky.app (rich link)
            # 2. #amazing (hashtag)
        """
        facets: List[Dict[str, Any]] = []
        text_str = as_str(self._post["text"])

        for u in self._parse_rich_urls():
            facets.append(
                {
                    "index": {
                        "byteStart": self._char_index_to_byte_index(
                            text_str, int(u["start"])
                        ),
                        "byteEnd": self._char_index_to_byte_index(
                            text_str, int(u["end"])
                        ),
                    },
                    "features": [
                        {
                            "$type": LINK_TYPE,
                            # NOTE: URI ("I") not URL ("L")
                            "uri": u["url"],
                        }
                    ],
                }
            )
        for m in self._parse_mentions():
            resp = requests.get(
                RPC_SLUG + RESOLVE_HANDLE,
                params={"handle": m["handle"]},
            )
            # If the handle can't be resolved, just skip it!
            # It will be rendered as text in the post instead of a link
            if resp.status_code == 400:
                continue
            did = resp.json()["did"]
            facets.append(
                {
                    "index": {
                        "byteStart": self._char_index_to_byte_index(
                            text_str, int(m["start"])
                        ),
                        "byteEnd": self._char_index_to_byte_index(
                            text_str, int(m["end"])
                        ),
                    },
                    "features": [{"$type": MENTION_TYPE, "did": did}],
                }
            )
        for u in self._parse_urls():
            facets.append(
                {
                    "index": {
                        "byteStart": self._char_index_to_byte_index(
                            text_str, int(u["start"])
                        ),
                        "byteEnd": self._char_index_to_byte_index(
                            text_str, int(u["end"])
                        ),
                    },
                    "features": [
                        {
                            "$type": LINK_TYPE,
                            # NOTE: URI ("I") not URL ("L")
                            "uri": u["url"],
                        }
                    ],
                }
            )
        for h in self._parse_hashtags():
            facets.append(
                {
                    "index": {
                        "byteStart": self._char_index_to_byte_index(
                            text_str, int(h["start"])
                        ),
                        "byteEnd": self._char_index_to_byte_index(
                            text_str, int(h["end"])
                        ),
                    },
                    "features": [
                        {
                            "$type": HASHTAG_TYPE,
                            "tag": h["tag"],
                        }
                    ],
                }
            )
        facets.sort(key=lambda x: x["index"]["byteStart"])
        return facets

    def build(self, session: ApiPayloadType) -> ApiPayloadType:
        """
        Build the final post structure ready for API submission.

        Finalizes the post by adding required metadata and processing all
        rich text features. This method should be called before submitting
        the post to the BlueSky API.

        The build process:
        1. Sets the creation timestamp (current UTC time)
        2. Parses and validates facets (mentions, links, hashtags)
        3. Enforces character limit (300 characters)
        4. Processes and attaches media attachments
        5. Returns the complete API-ready post structure

        Args:
            session (ApiPayloadType): The authenticated session containing
                                    access tokens and user information needed
                                    for attachment uploads and handle resolution.

        Returns:
            ApiPayloadType: The complete post dictionary ready for API submission,
                          containing all required fields like $type, text, createdAt,
                          facets, and embed information.

        Raises:
            PostTooLongError: If the post text exceeds 300 characters after
                            processing (includes the actual text and length)
            requests.HTTPError: If attachment upload fails during processing
            Various attachment errors: From attachment.attach_to_post() calls

        Examples:
            post = Post("Hello @alice.bsky.social! #greeting")
            built_post = post.build(session)

            # built_post now contains:
            # {
            #     "$type": "app.bsky.feed.post",
            #     "text": "Hello @alice.bsky.social! #greeting",
            #     "createdAt": "2023-01-01T12:00:00.000Z",
            #     "facets": [...],  # mention and hashtag facets
            #     # ... other fields as needed
            # }
        """
        self._post["createdAt"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        facets = self.parse_facets()
        text_str = as_str(self._post["text"])
        if len(text_str) > 300:
            raise PostTooLongError(
                f"Maximum of 300 characters allowed per post.  Post text: {text_str} (length: {len(text_str)})"
            )
        if facets:
            self._post["facets"] = facets

        for attachment in self.attachments:
            attachment.attach_to_post(self, session)
        return self._post

    @property
    def embed(self) -> Dict[str, ApiPayloadType]:
        """
        Get or create the embed structure for the post.

        Returns the embed dictionary where media attachments and other embedded
        content are stored. If no embed exists yet, creates an empty one and
        adds it to the post structure.

        The embed is used by attachment classes to store their media information
        and by the BlueSky API to render rich media content in posts.

        Returns:
            Dict[str, ApiPayloadType]: The embed dictionary containing media
                                     and other embedded content information.
                                     Initially empty, populated by attachments
                                     during the build process.

        Examples:
            post = Post("Check this out!", with_attachments=image)

            # Before build - embed exists but may be empty
            embed = post.embed
            # Returns: {}

            # After build - embed contains media information
            post.build(session)
            embed = post.embed
            # Returns: {"$type": "app.bsky.embed.images", "images": [...], ...}
        """
        if "embed" not in self._post:
            embed: ApiPayloadType = {}
            self.post["embed"] = embed
        return cast(ApiPayloadType, self.post["embed"])
