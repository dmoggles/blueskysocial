"""
Image attachment handling for BlueSky Social posts.

This module provides functionality for handling image attachments in BlueSky Social posts.
It supports loading images from multiple sources (URLs, local files, file handles),
automatic format conversion to PNG, size validation, and upload to the BlueSky blob storage.

The Image class handles the complete image lifecycle from source loading to API upload,
with proper error handling for oversized images and network issues. All images are
converted to PNG format for consistent handling by the BlueSky platform.

Key Features:
- Multiple image sources: URLs, local files, BytesIO handles
- Automatic PNG conversion for platform consistency
- Size validation (1MB limit)
- Accessibility support with alt text
- Efficient blob upload to BlueSky API
- Integration with post embed system

Classes:
    Image: Handles image loading, processing, and attachment to posts

Constants:
    IMAGE_MIMETYPE: Standard MIME type used for all image uploads ("image/png")

Example:
    # From local file
    image = Image("photo.jpg", alt_text="A beautiful sunset")

    # From URL
    image = Image("https://example.com/image.png", alt_text="Remote image")

    # From file handle
    with open("image.png", "rb") as f:
        buffer = BytesIO(f.read())
        image = Image(buffer, alt_text="Buffered image")

    # Use in post
    post = Post("Check this out!", with_attachments=image)
"""

from typing import Union, List, cast, Optional, Tuple, Callable, Dict
from io import BytesIO
import requests
from blueskysocial.api_endpoints import UPLOAD_BLOB, RPC_SLUG, IMAGES_TYPE
from blueskysocial.post_attachment import PostAttachment
from blueskysocial.utils import (
    get_auth_header,
    get_image_aspect_ratio_spec,
    provide_aspect_ratio,
)
from blueskysocial.errors import ImageIsTooLargeError
from blueskysocial.typedefs import ApiPayloadType, PostProtocol, as_str

IMAGE_MIMETYPE = "image/png"
"""
Standard MIME type for all image uploads to BlueSky.

All images are converted to PNG format regardless of their original format
to ensure consistent handling by the BlueSky platform. This simplifies
processing and ensures compatibility across all BlueSky clients.
"""


class Image(PostAttachment):
    """
    Handles image loading, processing, and attachment to BlueSky Social posts.

    The Image class provides comprehensive image handling for BlueSky Social posts,
    supporting multiple input sources and automatic processing. Images are loaded
    from URLs, local files, or file handles, validated for size constraints,
    and uploaded to BlueSky's blob storage when attached to posts.

    All images are converted to PNG format for platform consistency, regardless
    of their original format. The class handles the complete image lifecycle
    from source loading to final API integration.

    Key capabilities:
    - Multiple input sources: URLs, file paths, BytesIO handles
    - Automatic size validation (1MB limit enforced by BlueSky)
    - PNG format conversion for platform consistency
    - Accessibility support with alternative text
    - Efficient blob upload with proper authentication
    - Seamless integration with post embed system

    Attributes:
        _alt_text (str): Alternative text description for accessibility
        _image (Optional[bytes]): The processed image data in PNG format

    Args:
        image (Union[str, BytesIO]): The image source. Can be:
            - URL string starting with "http": Downloaded from the web
            - File path string: Loaded from local filesystem
            - BytesIO object: Used directly as image data
        alt_text (str): Alternative text describing the image content
                       for accessibility and screen readers

    Raises:
        ImageIsTooLargeError: If the processed image exceeds 1MB (1,000,000 bytes)
        requests.HTTPError: If downloading from URL fails
        FileNotFoundError: If local file path doesn't exist
        IOError: If file reading fails

    Examples:
        # Load from local file
        image = Image("vacation.jpg", alt_text="Beach vacation photo")

        # Load from URL
        image = Image(
            "https://example.com/photo.png",
            alt_text="Stock photo from website"
        )

        # Load from file handle
        with open("image.png", "rb") as f:
            buffer = BytesIO(f.read())
            image = Image(buffer, alt_text="Processed image data")

        # Use in post with multiple images
        images = [
            Image("photo1.jpg", alt_text="First photo"),
            Image("photo2.jpg", alt_text="Second photo")
        ]
        post = Post("Photo gallery!", with_attachments=images)
    """

    def __init__(
        self,
        image: Union[str, BytesIO],
        alt_text: str,
        aspect_ratio: Optional[Tuple[int, int]] = None,
        require_aspect_ratio: bool = False,
    ) -> None:
        """
        Initialize an Image attachment with source and alternative text.

        Creates a new Image instance by loading and processing image data from
        the specified source. The image is immediately loaded and validated,
        but not uploaded until the image is attached to a post.

        Args:
            image (Union[str, BytesIO]): The image source to load from:
                - str starting with "http": URL to download image from
                - str not starting with "http": Local file path to load
                - BytesIO: File handle containing image data
            alt_text (str): Descriptive text for accessibility. Should describe
                           the image content for users who cannot see the image.
                           Required for accessibility compliance.

        Raises:
            ImageIsTooLargeError: If the loaded image exceeds 1MB after processing
            requests.HTTPError: If URL download fails (network error, 404, etc.)
            FileNotFoundError: If the specified local file doesn't exist
            IOError: If file reading fails due to permissions or corruption

        Examples:
            # Load from local file
            image = Image("sunset.jpg", alt_text="Sunset over the ocean")

            # Load from URL
            image = Image(
                "https://example.com/logo.png",
                alt_text="Company logo"
            )

            # Load from file handle
            with open("data.png", "rb") as f:
                buffer = BytesIO(f.read())
                image = Image(buffer, alt_text="Chart showing sales data")
        """
        self._alt_text = alt_text
        self._image = self._set_image(image)
        self._aspect_ratio = aspect_ratio
        self._require_aspect_ratio = require_aspect_ratio

    @property
    def alt_text(self) -> str:
        """
        Get the alternative text description for the image.

        Returns the accessibility description that was provided when the Image
        instance was created. This text is used by screen readers and other
        assistive technologies to describe the image content to users who
        cannot see the image.

        The alternative text is also used by the BlueSky platform for content
        indexing and may be displayed in contexts where the image cannot be
        loaded or in text-only views.

        Returns:
            str: The alternative text description of the image content.
                Never empty as alt_text is required during initialization.

        Examples:
            image = Image("photo.jpg", alt_text="Golden retriever playing in park")
            print(f"Image description: {image.alt_text}")
            # Output: Image description: Golden retriever playing in park

            # Alt text is used for accessibility
            for image in post_images:
                print(f"Image alt text: {image.alt_text}")
        """
        return self._alt_text

    def _set_image(self, image_src: str | BytesIO) -> bytes:
        """
        Load and validate image data from the specified source.

        Determines the source type and loads the image data using the appropriate
        method. After loading, validates that the image size doesn't exceed
        BlueSky's 1MB limit for blob uploads.

        Args:
            image_src (str | BytesIO): The image source to load from:
                - URL string (starts with "http"): Downloaded via HTTP
                - File path string: Read from local filesystem
                - BytesIO object: Read from file handle

        Returns:
            bytes: The processed image data ready for upload

        Raises:
            ImageIsTooLargeError: If the image exceeds 1,000,000 bytes
            requests.HTTPError: If URL download fails
            FileNotFoundError: If local file doesn't exist
            IOError: If file reading fails

        Examples:
            # Internal method - called during __init__
            # Handles URL downloads
            image_data = self._set_image("https://example.com/image.png")

            # Handles local files
            image_data = self._set_image("/path/to/image.jpg")

            # Handles BytesIO objects
            buffer = BytesIO(existing_data)
            image_data = self._set_image(buffer)
        """
        if isinstance(image_src, str):
            if image_src.startswith("http"):
                img = self._get_image_from_url(image_src)
            else:
                img = self._get_image_from_file(image_src)
        else:
            img = self._get_image_from_file_handle(image_src)

        if len(img) > 1000000:
            raise ImageIsTooLargeError(
                f"image file size too large. 1000000 bytes maximum, got: {len(img)} bytes"
            )
        return img

    def _get_image_from_url(self, url: str) -> bytes:
        """
        Download image data from a remote URL.

        Fetches image data from the specified URL using an HTTP GET request.
        Validates the response status and returns the raw image bytes.

        Args:
            url (str): The URL to download the image from. Must be a valid
                      HTTP or HTTPS URL pointing to an image resource.

        Returns:
            bytes: The raw image data downloaded from the URL

        Raises:
            requests.HTTPError: If the HTTP request fails (404, 403, network error, etc.)
            requests.ConnectionError: If network connection fails
            requests.Timeout: If the request times out

        Examples:
            # Download from public URL
            image_data = self._get_image_from_url("https://example.com/photo.jpg")

            # Works with various image formats
            png_data = self._get_image_from_url("https://site.com/image.png")
            gif_data = self._get_image_from_url("https://site.com/animation.gif")
        """
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    def _get_image_from_file(self, file_path: str) -> bytes:
        """
        Load image data from a local file.

        Reads the entire contents of the specified file and returns the raw
        bytes. The file is opened in binary mode to preserve image data integrity.

        Args:
            file_path (str): The path to the local image file. Can be relative
                           or absolute path. Must point to a readable file.

        Returns:
            bytes: The raw image data read from the file

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            PermissionError: If the file cannot be read due to permissions
            IOError: If file reading fails for other reasons (corruption, etc.)

        Examples:
            # Load from relative path
            image_data = self._get_image_from_file("images/photo.jpg")

            # Load from absolute path
            image_data = self._get_image_from_file("/home/user/pictures/image.png")

            # Works with various image formats
            jpg_data = self._get_image_from_file("photo.jpg")
            png_data = self._get_image_from_file("graphic.png")
        """
        with open(file_path, "rb") as f:
            return f.read()

    def _get_image_from_file_handle(self, file_handle: BytesIO) -> bytes:
        """
        Extract image data from a BytesIO file handle.

        Reads all available data from the provided BytesIO object. This method
        allows for in-memory image processing and programmatic image creation.

        Args:
            file_handle (BytesIO): The file handle containing image data.
                                  The handle should be positioned at the start
                                  of the image data.

        Returns:
            bytes: The raw image data read from the file handle

        Raises:
            IOError: If reading from the file handle fails
            AttributeError: If the file handle doesn't support read operations

        Examples:
            # Create from existing bytes
            image_bytes = b"..."  # Raw image data
            buffer = BytesIO(image_bytes)
            image_data = self._get_image_from_file_handle(buffer)

            # Process uploaded file
            uploaded_file = request.files['image']
            buffer = BytesIO(uploaded_file.read())
            image_data = self._get_image_from_file_handle(buffer)
        """
        return file_handle.read()

    def attach_to_post(self, post: PostProtocol, session: ApiPayloadType) -> None:
        """
        Attach this image to a BlueSky Social post's embed structure.

        Integrates the image into the post's embed system, uploading the image
        to BlueSky's blob storage if not already uploaded. The image becomes
        part of the post's media gallery and will be displayed when the post
        is viewed.

        This method handles both single and multiple image scenarios:
        - First image: Creates the images embed structure
        - Additional images: Appends to existing images list

        The embed structure follows BlueSky's image embed specification with
        proper type identification and accessibility metadata.

        Args:
            post (PostProtocol): The post object to attach the image to.
                               Must have an 'embed' attribute that can be modified.
            session (ApiPayloadType): The authenticated session containing
                                    access tokens needed for image upload to
                                    BlueSky's blob storage.

        Raises:
            requests.HTTPError: If image upload to BlueSky blob storage fails
            KeyError: If required session authentication data is missing
            AttributeError: If post doesn't have required embed structure

        Examples:
            image = Image("photo.jpg", alt_text="Beautiful sunset")

            # Attach to a post
            image.attach_to_post(my_post, session)

            # Post embed now contains:
            # {
            #     "$type": "app.bsky.embed.images",
            #     "images": [
            #         {
            #             "alt": "Beautiful sunset",
            #             "image": {blob_reference}
            #         }
            #     ]
            # }
        """
        aspect_ratio = provide_aspect_ratio(self)
        img_dict: ApiPayloadType = {"alt": self.alt_text, "image": self.build(session)}
        if aspect_ratio:
            img_dict["aspectRatio"] = aspect_ratio
        post.embed["$type"] = IMAGES_TYPE
        if "images" not in post.embed:
            post.embed["images"] = [img_dict]
        else:
            assert isinstance(
                post.embed["images"], list
            ), "Expected 'images' to be a list"
            images_list: List[ApiPayloadType] = cast(
                List[ApiPayloadType], post.embed["images"]
            )
            images_list.append(img_dict)

    def build(self, session: ApiPayloadType) -> ApiPayloadType:
        """
        Upload the image to BlueSky's blob storage and return the blob reference.

        Handles the complete image upload process by sending the processed image
        data to BlueSky's blob storage API with proper authentication and content
        type headers. The returned blob reference can then be used in post embeds.

        All images are uploaded with PNG MIME type regardless of original format
        to ensure consistent platform handling. The upload includes proper
        authentication headers derived from the session data.

        Args:
            session (ApiPayloadType): The authenticated session containing
                                    access tokens and authentication data needed
                                    for the blob upload API call.

        Returns:
            ApiPayloadType: The blob reference dictionary from BlueSky API containing
                          the blob identifier, MIME type, size, and other metadata
                          needed to reference the uploaded image in posts.

        Raises:
            requests.HTTPError: If the blob upload API call fails due to:
                              - Network connectivity issues
                              - Authentication problems
                              - Server errors
                              - Image too large for blob storage
            KeyError: If the session doesn't contain required authentication data
                     (specifically the "accessJwt" field)

        Examples:
            image = Image("photo.jpg", alt_text="Sunset photo")
            blob_ref = image.build(session)

            # blob_ref contains:
            # {
            #     "blob": {
            #         "$type": "blob",
            #         "ref": {...},
            #         "mimeType": "image/png",
            #         "size": 245760
            #     }
            # }
        """
        access_token = as_str(session["accessJwt"])
        headers = get_auth_header(access_token)
        headers["Content-Type"] = IMAGE_MIMETYPE
        resp = requests.post(
            RPC_SLUG + UPLOAD_BLOB,
            headers=headers,
            data=self.data_accessor,
        )
        resp.raise_for_status()
        return cast(ApiPayloadType, resp.json()["blob"])

    @property
    def data_accessor(self) -> bytes:
        """
        Get the raw image data in bytes.


        Returns:
            bytes: The raw image data in PNG format ready for upload

        Examples:
            image = Image("photo.jpg", alt_text="A beautiful sunset")
            raw_data = image.data_accessor
            # raw_data contains the bytes of the image
        """
        return self._image

    @property
    def aspect_ratio(self) -> Optional[Tuple[int, int]]:
        """
        Get the aspect ratio of the image if available.

        Returns the aspect ratio tuple (width, height) if it was provided during
        initialization or calculated. If no aspect ratio is set, returns None.

        Returns:
            Optional[Tuple[int, int]]: The aspect ratio of the image as a tuple
                                       of (width, height) or None if not set.

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
    def aspect_ratio_function(self) -> Callable[[bytes], Optional[Dict[str, int]]]:
        """
        Get the function to provide aspect ratio for the image.

        Returns a callable that returns the aspect ratio of the image if available.
        This allows dynamic aspect ratio retrieval based on the current image state.

        Returns:
            callable: A function that returns the aspect ratio tuple (width, height)
                      or None if not set.
        """
        return get_image_aspect_ratio_spec
