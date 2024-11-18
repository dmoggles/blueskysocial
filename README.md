# blueskysocial

blueskysocial is a Python library for managing social media posts and images. It provides a Client class for interacting with social media platforms, as well as classes for representing posts and images.

## Installation

To install blueskysocial, you can use pip:

```bash
pip install blueskysocial
```

## Usage

### Making an individual post

```python
from blueskysocial import Client, Post, Image

client = Client()
client.authenticate(user_name, password)

image = Image('path/to/image.jpg', alt_text='This is an image.')
post = Post('Hello, world!, This is my first post.', images=[image])
client.post(post)
```

### Posting threads

```python
from blueskysocial import Client, Post, Image

client = Client()
client.authenticate(user_name, password)

image = Image('path/to/image.jpg', alt_text='This is an image.')
post = Post('Hello, world!, This is my first post.', images=[image])
second_post = Post('Another Post')
client.post_thread([post,second_post])
```

### Posting with a video.
As of version 1.5.0, embedding video in your post is supported.  Currently video can only be embedded from a local file.  Please note, that when embedding a video in a post, it may take several minutes for Bluesky to process your video, during which a video frame with "Video Not Found" will appear in your post.  

The following video formats are supported
- mp4
- mpeg
- webm
- mov

```python
from blueskysocial import Client, Post, Video
client = Client()
client.authenticate(user_name, password)

video = Video('path/to/video.mov')
post = Post('Video Post', video=video)
client.post(post)
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
blueskysocial is licensed under the MIT License. See [LICENSE](LICENSE) for more information.
```

