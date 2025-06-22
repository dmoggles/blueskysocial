from bs4 import BeautifulSoup
import requests
from blueskysocial.api_endpoints import RPC_SLUG, UPLOAD_BLOB
from blueskysocial.post_attachment import PostAttachment
from blueskysocial.utils import get_auth_header, bs4_tag_extract_content
from blueskysocial.typedefs import as_bs4_tag, ApiPayloadType, PostProtocol

IMAGE_MIMETYPE = "image/png"


class WebCard(PostAttachment):
    def __init__(self, url: str):
        self._url = url

    @staticmethod
    def fetch_embed_url_card(access_token: str, url: str) -> ApiPayloadType:

        # the required fields for every embed card
        card: ApiPayloadType = {
            "uri": url,
            "title": "",
            "description": "",
        }

        # fetch the HTML
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # parse out the "og:title" and "og:description" HTML meta tags
        title_tag = as_bs4_tag(soup.find("meta", property="og:title"))

        if title_tag:
            card["title"] = bs4_tag_extract_content(title_tag)
        description_tag = as_bs4_tag(soup.find("meta", property="og:description"))
        if description_tag:
            card["description"] = bs4_tag_extract_content(description_tag)

        # if there is an "og:image" HTML meta tag, fetch and upload that image
        image_tag = as_bs4_tag(soup.find("meta", property="og:image"))
        if image_tag:
            img_url = bs4_tag_extract_content(image_tag)
            # naively turn a "relative" URL (just a path) into a full URL, if needed
            if "://" not in img_url:
                img_url = url + img_url
            resp = requests.get(img_url)
            resp.raise_for_status()
            headers = get_auth_header(access_token)
            headers["Content-Type"] = IMAGE_MIMETYPE
            blob_resp = requests.post(
                RPC_SLUG + UPLOAD_BLOB,
                headers=headers,
                data=resp.content,
            )
            blob_resp.raise_for_status()
            card["thumb"] = blob_resp.json()["blob"]

        return {
            "$type": "app.bsky.embed.external",
            "external": card,
        }

    def attach_to_post(self, post: PostProtocol, session: ApiPayloadType) -> None:
        try:
            post.post["embed"] = self.fetch_embed_url_card(
                session["accessJwt"], self._url
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch embed card for {self._url}: {e}"
            ) from e
