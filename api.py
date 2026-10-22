import json

import requests
from envparse import env

env.read_envfile(".env")
ADMIN_SECRET = env.str("ADMIN_SECRET")


def api(endpoint: str) -> str:
    return env.str("API") + endpoint


def new_artist(common_name: str, aliases: list[str]):
    return requests.post(
        api("admin/artist/new/"),
        json.dumps(
            {"secret": ADMIN_SECRET, "commonName": common_name, "aliases": aliases}
        ),
    )


def edit_aliases(artist: int, add_aliases: list[str], remove_aliases: list[str]):
    return requests.post(
        api("admin/artist/editAliases/"),
        json.dumps(
            {
                "secret": ADMIN_SECRET,
                "id": artist,
                "aliases": add_aliases or None,
                "delAliases": remove_aliases or None,
            }
        ),
    )


def list_artists():
    return json.loads(requests.get(api("artistList")).content)["artists"]


def list_drawings():
    return json.loads(
        requests.post(
            api("admin/drawings/list"), json.dumps({"secret": ADMIN_SECRET})
        ).content
    )["drawings"]


def new_drawings(artist: int, b64img: str):
    return requests.post(
        api("admin/drawings/new"),
        json.dumps(
            {
                "secret": ADMIN_SECRET,
                "artistId": artist,
                "encodedImage": b64img,
            }
        ),
    )


def view_drawing(drawing_id: int):
    return requests.post(
        api("admin/drawings/view"),
        json.dumps({"secret": ADMIN_SECRET, "id": drawing_id}),
    )


def force_drawing(drawing_id: int):
    return requests.post(
        api("admin/force"), json.dumps({"secret": ADMIN_SECRET, "id": drawing_id})
    )
