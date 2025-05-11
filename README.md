# blueskysocial

blueskysocial is a Python library for managing social media posts and images. It provides a Client class for interacting with social media platforms, as well as classes for representing posts and images.

## Important Note About Issues

While I welcome issues and try to work on them, I also have come to realise that I frequently don't see them. 

**If you submit an issue, I kindly ask that you also send me a message to https://bsky.app/profile/dmitry.mclachbot.com to let me know about it**

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
post = Post('Hello, world!, This is my first post.', with_attachments=[image])
client.post(post)
```

### Posting threads

```python
from blueskysocial import Client, Post, Image

client = Client()
client.authenticate(user_name, password)

image = Image('path/to/image.jpg', alt_text='This is an image.')
post = Post('Hello, world!, This is my first post.', with_attachments=[image])
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
post = Post('Video Post', with_attachments=video)
client.post(post)
```

### Link Shortening
Bluesky counts URL characters towards the 300 character limit.  The solution to this is to format your links.  `blueskysocial` supports markdown link formatting.  If you format your post text in the following fashion
```python
from blueskysocial import Client, Post

client = Client()
client.authenticate(user_name, password)
post = Post('Hello, world!, This is my first post.  But with a link.  [Click here](http://really.long.url.here)'),
clinet.post(post)
```
Your post text will be "Hello, world!, This is my first post. But with a link. Click here", with the words "Click here" being a link.  In this fashion, only the characters in "Click here" count towards the limit

### Web Cards
Webcards are the small preview images of a linked website that appear at the bottom of the posts and also serve as links.  You can embed a webcard with the following syntax
```python
from blueskysocial import Client, Post, WebCard

client = Client()
client.authenticate(user_name, password)
webcard = WebCard("http://url_to_link_to.com/article")
post = Post('Check out this article!', with_attachments=webcard)
clinet.post(post)
```

## Direct Messsage Interface


Get all convos and show the member and last message of the last conversation
```python
convos = client.get_convos()
print(convos[-1].participant)
print(convos[-1].last_message)
```

Get convos based ona filter.  Many other filters are available, this is not an exhaustive list

```python
convos = client.get_convos(
    bs.F.And(
        bs.F.Eq(bs.F.Participant, 'someusername.bsky.social'),
        bs.F.GT(bs.F.LastMessageTime, '2024-01-01')
    )
)
print(convos[-1].participant)
print(convos[-1].last_message)
```

Get all messages in a conversation
```python
messages = convos[-1].get_messages()
print(messages[0].sent_at)
print(messages[-1].sent_at)
print(messages[0].text)
```

Please notice that the message list is ordered such that last message is first
```
2024-11-26 12:47:31.704000
2024-11-22 22:33:38.323000
Great stuff!
```

Get a conversation with a specific member or members.  This is also how you create a new conversation if you want to DM someone you haven't sent messages to before

```python
convo = client.get_convo_for_members('someusername.bsky.social')
```

Send a message

```python
convo.send_message('Hello, World!')
```


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
blueskysocial is licensed under the MIT License. See [LICENSE](LICENSE) for more information.
```

