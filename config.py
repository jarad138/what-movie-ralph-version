from dotenv import load_dotenv
import sys
import os


class Load:
    giphy_api_key: str | None
    tmdb_token: str | None

    def __init__(self):
        load_dotenv()

        self.tmbd_token = os.getenv("TMDB_TOKEN")
        self.giphy_api_key = os.getenv("GIPHY_API_KEY")

        if not self.tmbd_token:
            print("No TMDB_TOKEN")
            sys.exit(1)

        if not self.giphy_api_key:
            print("No GIPHY_API_KEY")
            sys.exit(1)

