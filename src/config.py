from dotenv import load_dotenv
import os

load_dotenv("bot_env_vars.env")


class Config:
    def __init__(self) -> None:
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.oauth_token = os.getenv("OAUTH_TOKEN")
        self.bot_name = os.getenv("BOT_NAME")
        self.channel = os.getenv("CHANNEL")


if __name__ == "__main__":
    c = Config()
    print(c.client_id)
