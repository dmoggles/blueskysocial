import requests

from blueskysocial.post import Post
from blueskysocial.image import Image
from blueskysocial.api_endpoints import (
    RPC_SLUG,
    CREATE_SESSION,
    CREATE_RECORD,
    POST_TYPE,
)


class Client:
    """
    A client class for interacting with the BlueSky Social server.


    """

    def __init__(self):
        self._session = None

    @property
    def access_token(self):
        """The access token for the client.

        Returns:
            str: The access token.
        """
        return self._session["accessJwt"]

    @property
    def did(self):
        """The DID for the client.

        Returns:
            str: The DID (Decentralized Identifier) for the client.
        """
        return self._session["did"]

    def authenticate(self, handle: str, password: str):
        """Authenticate the client with the server.

        Args:
            handle (str): The handle or username of the client.
            password (str): The password of the client.

        Raises:
            requests.HTTPError: If the server returns an error response.

        Returns:
            dict: The session information returned by the server.
        """
        response = requests.post(RPC_SLUG + CREATE_SESSION, json={"identifier": handle, "password": password})
        response.raise_for_status()
        session = response.json()
        self._session = session

    def post(self, post: Post) -> dict:
        """Post content to the server.

        Args:
            post (Post): The post object to be posted.

        Returns:
            dict: The response from the server.

        Raises:
            Exception: If the client is not authenticated.
        """
        if not self._session:
            raise Exception("Client not authenticated.")

        response = requests.post(
            RPC_SLUG + CREATE_RECORD,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "repo": self.did,
                "collection": POST_TYPE,
                "record": post.build(self._session),
            },
        )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    client = Client()
    client.authenticate("mclachbot.bsky.social", "Rivka2015!")
    image = Image(r"C:\Users\dmitr\python\footballdashboards\pizza.png", "build_up_pizza")
    post = Post(
        "Automated post test. Includes image. Mentioning @chicagodmitry.bsky.social",
        images=[image],
    )
    client.post(post)
