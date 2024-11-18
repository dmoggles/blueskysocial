import requests
from blueskysocial.api_endpoints import UPLOAD_BLOB, RPC_SLUG

VIDEO_MIME_TYPES_FROM_EXTENTIONS = {
    "mp4": "video/mp4",
    "mpeg": "video/mpeg",
    "webm": "video/webm",
    "mov": "video/quicktime",
}


class Video:
    """
    A class used to represent a Video and handle its upload process.
    Attributes
    ----------
    path : str
        The file path of the video to be uploaded.
    _upload_blob : dict or None
        The response from the upload request, initially set to None.
    Methods
    -------
    build(session: dict) -> dict
        Reads the video file, determines its MIME type, uploads it to the server, 
        and returns the blob information from the server response.
    """
    def __init__(self, path:str):
        self._path = path
        self._upload_blob = None
    
    def build(self, session:dict)->dict:
        if self._upload_blob is None:
            with open(self._path, "rb") as file:
                stream = file.read()

            try: 
                mime_type = VIDEO_MIME_TYPES_FROM_EXTENTIONS[self._path.split(".")[-1]]
            except KeyError:
                raise Exception("Unsupported video format")
            resp = requests.post(
                RPC_SLUG + UPLOAD_BLOB,
                headers={"Authorization": f"Bearer {session["accessJwt"]}",
                            "Content-Type": mime_type},
                data=stream
            )
            resp.raise_for_status()
            self._upload_blob = resp.json()
        return self._upload_blob["blob"]