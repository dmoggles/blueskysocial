"""
Video attachment handling for BlueSky Social posts.

This module provides functionality for uploading and attaching video files to BlueSky Social posts.
It handles video file processing, MIME type detection, upload to the BlueSky API, and embedding
the video in post structures.

The module supports common video formats including MP4, MPEG, WebM, and QuickTime (MOV) files.
Videos are uploaded as blobs to the BlueSky API and then embedded in posts with optional
alternative text for accessibility.

Classes:
    Video: Handles video file upload and attachment to posts

Constants:
    VIDEO_MIME_TYPES_FROM_EXTENSIONS: Mapping of file extensions to MIME types

Example:
    # Create a video attachment and add it to a post
    video = Video("path/to/video.mp4", alt_text="A demo video")

    # The video will be automatically uploaded and attached when the post is created
    post = client.post("Check out this video!", video=video)
"""

import requests
from typing import cast, Optional, Tuple, Callable, Dict
from blueskysocial.api_endpoints import UPLOAD_BLOB, RPC_SLUG, VIDEO_TYPE
from blueskysocial.post_attachment import PostAttachment
from blueskysocial.utils import (
    get_auth_header,
    provide_aspect_ratio,
    get_video_aspect_ratio_spec,
)
from blueskysocial.typedefs import PostProtocol, ApiPayloadType, as_str

VIDEO_MIME_TYPES_FROM_EXTENSIONS = {
    "mp4": "video/mp4",
    "mpeg": "video/mpeg",
    "webm": "video/webm",
    "mov": "video/quicktime",
}
"""
Mapping of video file extensions to their corresponding MIME types.

This dictionary provides the mapping between common video file extensions and their
standard MIME types as used by the BlueSky API. The MIME type is used in the
Content-Type header when uploading video blobs.

Supported formats:
    - MP4: Modern, widely supported video format
    - MPEG: Standard video compression format
    - WebM: Open-source video format, web-optimized
    - MOV: QuickTime video format

Note: The extension matching is case-sensitive and expects lowercase extensions.
"""


class Video(PostAttachment):
    """
    Handles video file upload and attachment to BlueSky Social posts.

    This class manages the complete lifecycle of video attachments, from local file
    processing to upload and embedding in posts. It automatically handles MIME type
    detection, file upload to the BlueSky blob storage, and proper embedding in the
    post structure.

    The Video class extends PostAttachment and implements the attachment interface,
    allowing it to be used seamlessly with the post creation system. Videos are
    uploaded once and cached for reuse within the same session.

    Attributes:
        _path (str): The file system path to the video file
        _upload_blob (dict | None): Cached upload response from the BlueSky API,
                                   None until first upload
        _alt_text (str): Alternative text description for accessibility

    Methods:
        __init__(path, alt_text): Initialize with video file path and optional alt text
        attach_to_post(post, session): Attach this video to a post structure
        build(session): Upload the video and return blob information
        alt_text: Property to access the alternative text

    Example:
        # Create a video attachment
        video = Video("demo.mp4", alt_text="Product demonstration video")

        # Use with a post (video is uploaded automatically)
        post = client.post("Check this out!", attachments=[video])

        # Or attach manually to a post structure
        video.attach_to_post(post, session)
    """

    def __init__(
        self,
        path: str,
        alt_text: str = "",
        aspect_ratio: Optional[Tuple[int, int]] = None,
        require_aspect_ratio: bool = False,
    ) -> None:
        """
        Initialize a Video attachment with file path and optional alternative text.

        Creates a new Video instance that can be attached to BlueSky Social posts.
        The video file is not uploaded immediately - upload occurs when the video
        is first attached to a post or when build() is called explicitly.

        Args:
            path (str): The file system path to the video file. Should be a valid
                       path to an existing video file in a supported format.
                       Supported extensions: mp4, mpeg, webm, mov
            alt_text (str, optional): Alternative text description of the video
                                    content for accessibility purposes. Defaults to
                                    empty string. Should describe the video content
                                    for users who cannot view the video.

            aspect_ratio (Optional[Tuple[int, int]], optional): Aspect ratio of the video
                                                            in the format (width, height).
                                                            This is used for display
                                                            purposes in the post embed.
                                                            If not provided, the aspect ratio
                                                            will be attempted to be set automatically
                                                            based on the video file metadata.
            require_aspect_ratio (Optional[bool], optional): If True, the aspect ratio
                                                            must either be provided
                                                            or automatically determined from the video file
                                                            and if it cannot be determined,
                                                            an error will be raised.
                                                            If False, the aspect ratio is optional.

        Raises:
            FileNotFoundError: If the specified video file path does not exist
                              (raised when build() is called, not during initialization)

        Example:
            # Basic video attachment
            video = Video("path/to/video.mp4")

            # Video with accessibility description
            video = Video(
                "demo.mp4",
                alt_text="Product demonstration showing key features"
            )
        """
        self._path = path
        self._upload_blob: ApiPayloadType = {}
        self._alt_text = alt_text
        self._aspect_ratio = aspect_ratio
        self._require_aspect_ratio = require_aspect_ratio

    def attach_to_post(self, post: PostProtocol, session: ApiPayloadType) -> None:
        """
        Attach this video to a BlueSky Social post structure.

        This method integrates the video into a post's embed structure, uploading
        the video file if it hasn't been uploaded yet. The video becomes part of
        the post's multimedia content and will be displayed when the post is viewed.

        The method modifies the post structure in-place, adding an embed field with
        the video blob information and alternative text. If the post already has
        an embed, it will be replaced with the video embed.

        Args:
            post (PostProtocol): The post object to attach the video to. Must have
                               a 'post' attribute containing the post structure dict.
            session (ApiPayloadType): The authenticated session data containing
                                    access tokens needed for video upload.

        Raises:
            FileNotFoundError: If the video file path does not exist
            Exception: If the video format is not supported
            requests.HTTPError: If the video upload to BlueSky API fails
            KeyError: If required session data is missing

        Example:
            video = Video("demo.mp4", alt_text="Demo video")

            # Attach to an existing post
            video.attach_to_post(my_post, session)

            # The post now has video embedded
            # post.post["embed"] contains the video information
        """
        video_embed: ApiPayloadType = {
            "$type": VIDEO_TYPE,
            "video": self.build(session),
            "alt": self.alt_text,
        }
        aspect_ratio = provide_aspect_ratio(self)
        if aspect_ratio:
            video_embed["aspectRatio"] = aspect_ratio
        post.post["embed"] = video_embed

    def build(self, session: ApiPayloadType) -> ApiPayloadType:
        """
        Upload the video file and return the blob information for embedding.

        This method handles the complete video upload process: reading the file,
        determining the MIME type, uploading to BlueSky's blob storage, and
        returning the blob reference needed for post embedding.

        The method implements caching - if the video has already been uploaded
        in this session, it returns the cached blob information without
        re-uploading. This allows the same video to be reused multiple times
        efficiently.

        Args:
            session (ApiPayloadType): The authenticated session containing access
                                    tokens and other authentication data needed
                                    for the upload API call.

        Returns:
            ApiPayloadType: The blob information dictionary from the BlueSky API,
                          containing references needed to embed the video in posts.
                          Includes fields like blob ID, MIME type, and size.

        Raises:
            FileNotFoundError: If the video file at the specified path doesn't exist
            Exception: If the video file extension is not supported (not in
                      VIDEO_MIME_TYPES_FROM_EXTENSIONS)
            requests.HTTPError: If the HTTP upload request fails (network issues,
                              authentication problems, file too large, etc.)
            KeyError: If the session doesn't contain required authentication data

        Example:
            video = Video("demo.mp4")
            blob_info = video.build(session)

            # blob_info contains the uploaded video reference
            # Can be used directly in post embed structures
        """
        if not self._upload_blob:
            with open(self._path, "rb") as file:
                stream = file.read()

            try:
                mime_type = VIDEO_MIME_TYPES_FROM_EXTENSIONS[self._path.split(".")[-1]]
            except KeyError:
                raise Exception("Unsupported video format")

            access_token = as_str(session["accessJwt"])
            headers = get_auth_header(access_token)
            headers["Content-Type"] = mime_type

            resp = requests.post(
                RPC_SLUG + UPLOAD_BLOB,
                headers=headers,
                data=stream,
            )
            resp.raise_for_status()
            self._upload_blob = resp.json()

        return cast(ApiPayloadType, self._upload_blob["blob"])

    @property
    def alt_text(self) -> str:
        """
        Get the alternative text description for the video.

        Returns the accessibility description that was provided when the Video
        instance was created. This text is used by screen readers and other
        assistive technologies to describe the video content to users who
        cannot view the video directly.

        The alternative text is also used by the BlueSky platform for content
        indexing and may be displayed in contexts where the video cannot be
        loaded or played.

        Returns:
            str: The alternative text description of the video content.
                Empty string if no alt text was provided during initialization.

        Example:
            video = Video("demo.mp4", alt_text="Product demonstration video")
            print(f"Video description: {video.alt_text}")
            # Output: Video description: Product demonstration video

            # For videos without alt text
            video2 = Video("clip.mp4")
            print(f"Alt text: '{video2.alt_text}'")
            # Output: Alt text: ''
        """
        return self._alt_text

    @property
    def data_accessor(self) -> str:
        """
        Get the file path of the video data accessor.
        This property returns the file system path to the video file that this
        Video instance represents. It is used to access the video file for
        reading and uploading to the BlueSky API.
        """
        return self._path

    @property
    def aspect_ratio(self) -> Optional[Tuple[int, int]]:
        """
        Get the aspect ratio of the video.
        Returns the aspect ratio as a tuple of (width, height) if it was provided
        during initialization or determined automatically. If no aspect ratio is
        available, returns None.
        Returns:
            Optional[Tuple[int, int]]: The aspect ratio of the video as a tuple
                                       (width, height) or None if not available.

        Example:
            video = Video("demo.mp4", aspect_ratio=(16, 9))
            print(video.aspect_ratio)  # Output: (16, 9)
            video2 = Video("clip.mp4")
            print(video2.aspect_ratio)  # Output: None (if not set or determined)

        """
        return self._aspect_ratio

    @property
    def require_aspect_ratio(self) -> bool:
        """
        Check if the image requires an aspect ratio.

        Returns True if the image requires an aspect ratio to be provided,
        otherwise returns False. This is used to determine if aspect ratio
        validation should be enforced during post attachment.

        Returns:
            bool: True if aspect ratio is required, False otherwise.
        """
        return self._require_aspect_ratio

    @property
    def aspect_ratio_function(self) -> Callable[[str], Optional[Dict[str, int]]]:
        """
        Get the function to provide aspect ratio for the video.
        Returns a function that takes the video data as input and returns
        the aspect ratio as a dictionary with 'width' and 'height' keys.
        """
        return get_video_aspect_ratio_spec
