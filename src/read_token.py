import json

def get_access_token():
    with open("src/data/access_token.json", "r") as f:
        data = json.load(f)
        return data["access_token"]