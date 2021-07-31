import os

import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "bot_env_vars.env"))


class Config:
    def __init__(self) -> None:
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.oauth_token = os.getenv("OAUTH_TOKEN")
        self.bot_name = os.getenv("BOT_NAME")
        self.channel = os.getenv("CHANNEL")
        self.oauth_token_api = os.getenv("OAUTH_TOKEN_API")
        self.client_id_api = os.getenv("CLIENT_ID_API")
        self.bot_api_token = self.get_bot_api_token()

    def get_bot_api_token(self):
        r = httpx.post(
            "https://id.twitch.tv/oauth2/token"
            f"?client_id={self.client_id_api}"
            f"&client_secret={self.client_secret}"
            "&grant_type=client_credentials"
        )
        if r.json():
            return r.json()["access_token"]


if __name__ == "__main__":
    c = Config()
