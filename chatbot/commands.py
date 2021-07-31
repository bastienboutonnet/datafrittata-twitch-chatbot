import logging
from abc import ABC
from datetime import datetime
from typing import Dict, List, Optional, Type

import httpx
from irc.client import ServerConnection

from chatbot.config import Config
from chatbot.db import DbConnector

START_TIME = datetime.now()


def send_message(connection: ServerConnection, channel: str, text: str):
    connection.privmsg(channel, text=f"{text}")


class BaseCommand(ABC):
    def __init__(self, db_connector: DbConnector, config: Config, **kwargs):
        self.db_connector = db_connector
        self.config = config

    @property
    def is_restricted(self):
        return False

    def run(self):
        raise NotImplementedError


class UptimeCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, **kwargs):
        self.db_connector = db_connector
        self.config = config

    def run(self):
        url = f"https://api.twitch.tv/helix/streams?user_login={self.config.channel}"
        headers = {
            "Authorization": f"Bearer {self.config.bot_api_token}",
            "Client-ID": self.config.client_id_api,
        }
        response = httpx.get(url, headers=headers)
        response_json = response.json()
        if response_json.get("data", []):
            start_time = response_json["data"][0]["started_at"]
            start_time = datetime.strptime(
                start_time,
                "%Y-%m-%dT%H:%M:%SZ",
            )
            delta = (datetime.now() - start_time).seconds
            hours = delta // 3600
            minutes = (delta // 60) % 60
            seconds = delta % 60
            return f"We've been online for {hours} hours, {minutes} minutes and {seconds} seconds"
        else:
            return f"{self.config.channel} is not currently streaming"


class SayHelloCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, user_name: str, **kwargs):
        super().__init__(db_connector, config=config)
        self.user_name = user_name

    def run(self):
        message = f"Welcome to the stream, {self.user_name}"
        return message


class ListCommandsCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, **kwargs):
        super().__init__(db_connector, config)

    def run(self):
        all_commands = " !".join(AVAILABLE_COMMANDS)
        message = f"!{all_commands}"
        return message


class TodayCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, **kwargs):
        super().__init__(db_connector, config)

    def run(self):
        today_text = self.db_connector.retrive_command_response("today")
        if today_text:
            return f"{START_TIME.strftime('%m/%d/%Y')} | {today_text}"


class SetTodayCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, command_input: str, **kwargs):
        super().__init__(db_connector, config)
        self.today_text = command_input

    @property
    def is_restricted(self):
        return True

    def run(self):
        self.db_connector.update_command(command_name="today", command_response=self.today_text)
        logging.info("Today has been set")


class BotCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, **kwargs):
        super().__init__(db_connector, config)

    def run(self):
        return self.db_connector.retrive_command_response("bot")


class SourceCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, **kwargs):
        super().__init__(db_connector, config)

    def run(self):
        return self.db_connector.retrive_command_response("source")


class SetSourceCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, command_input: str, **kwargs):
        super().__init__(db_connector, config)
        self.source_text = command_input

    @property
    def is_restricted(self):
        return True

    def run(self):
        self.db_connector.update_command(command_name="source", command_response=self.source_text)


class SetUserCountryCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, command_input: str, **kwargs):
        super().__init__(db_connector, config)
        self.user_id = kwargs.get("user_id")
        self.user_country = command_input.lower()

    def run(self):
        try:
            assert self.user_id is not None
            self.db_connector.update_user_country(
                user_id=self.user_id, user_country=self.user_country
            )
        except AssertionError:
            return None


AVAILABLE_COMMANDS: Dict[str, Type[BaseCommand]] = {
    "hello": SayHelloCommand,
    "commands": ListCommandsCommand,
    "today": TodayCommand,
    "settoday": SetTodayCommand,
    "bot": BotCommand,
    "source": SourceCommand,
    "settsource": SetSourceCommand,
    "uptime": UptimeCommand,
    "setcountry": SetUserCountryCommand,
}
COMMANDS_TO_IGNORE: List[str] = ["drop", "keyboard", "dj", "frittata", "work", "discord"]


def commands_factory(command_name: str) -> Optional[Type[BaseCommand]]:
    try:
        return AVAILABLE_COMMANDS[command_name]
    except KeyError:
        return None
