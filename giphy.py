from urllib.parse import urlencode
import requests
import functools

class Client:
    api_key: str

    def __init__(self, api_key):
        if not api_key:
            raise Exception("Token is required")
        self.api_key = api_key

    @functools.cache
    def gifs_search(self, q, limit):
        params = {
            "api_key": self.api_key,
            "q": q,
            "limit": limit
        }
        url = f"https://api.giphy.com/v1/gifs/search?{urlencode(params)}"

        response = requests.get(url)

        if response.status_code != 200:
            print("error:", response.text)
            raise Exception(f"failed to fetch data: {response.status_code}")

        data = response.json()
        return data




