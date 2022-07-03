import requests
import json


async def get_uuid(name):
    try:
        name_data = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}").json()
        return name_data["id"]
    except json.decoder.JSONDecodeError:
        return None


async def get_name(uuid):
    try:
        name_data = requests.get(f"https://api.mojang.com/user/profiles/{uuid}/names").json()
        return name_data[-1]['name']
    except json.decoder.JSONDecodeError:
        return uuid
