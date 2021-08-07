import logging
import re
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


class ShoutoutCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, command_input: str, **kwargs):
        self.db_connector = db_connector
        self.config = config
        self.command_input = command_input

    @property
    def is_restricted(self):
        return True

    def run(self) -> Optional[str]:
        user_name = self.command_input.strip("@")
        search_channel_url = f"https://api.twitch.tv/helix/search/channels?query={user_name}"
        headers = {
            "Authorization": f"Bearer {self.config.bot_api_token}",
            "Client-ID": self.config.client_id_api,
        }
        channel_search_response = httpx.get(search_channel_url, headers=headers)

        if channel_search_response.status_code == 200:
            channel_search_response_json = channel_search_response.json()
            if channel_search_response_json.get("data"):
                channel_data = channel_search_response_json["data"][0]
                display_name = channel_data["display_name"]
                url_suffix = channel_data["broadcaster_login"]
                if user_name.lower() == url_suffix:
                    return (
                        f"You should check out {display_name} or give them a follow here: "
                        f"https://twitch.tv/{url_suffix} <3"
                    )
                else:
                    return f"{user_name} is not a valid user"
            else:
                return f"{user_name} doesn't seem to exist"
        else:
            return None


class UptimeCommand(BaseCommand):
    # TODO: introduce a cool down period for the api call but this might be hard
    # to test without having to introduce sleep and make the tests slow as hell to run.
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
            # timestamp comes back in UTC so we need to compare to a UTC now later.
            start_time = datetime.strptime(
                start_time,
                "%Y-%m-%dT%H:%M:%SZ",
            )
            delta = (datetime.utcnow() - start_time).seconds
            hours = delta // 3600
            # we only do it for hours since that's the only one that's likely to be 0 for long
            if hours:
                hours_str = f"{hours} hours, "
            else:
                hours_str = ""
            minutes = (delta // 60) % 60
            seconds = delta % 60
            return f"We've been online for {hours_str}{minutes} minutes and {seconds} seconds"
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
        # TODO: find a way to get commands from the db too
        db_commands = self.db_connector.get_all_commands()
        special_comands = list(SPECIAL_COMMANDS.keys())
        if db_commands is None:
            db_commands = []
        all_commands = " !".join(db_commands + special_comands)
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

    @property
    def is_restricted(self):
        return False

    def run(self):
        try:
            assert self.user_id is not None
            self.db_connector.update_user_country(
                user_id=self.user_id, user_country=self.user_country
            )
        except AssertionError:
            return None


class TextCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, **kwargs):
        super().__init__(db_connector, config)
        self.command_name = kwargs.get("command_name", "no command name")

    def run(self) -> Optional[str]:
        command_response = self.db_connector.retrive_command_response(
            command_name=self.command_name
        )
        if command_response is not None:
            return command_response
        else:
            return f"{self.command_name} does not exist"


class TextCommandSetter(BaseCommand):
    def __init__(self, db_connector: DbConnector, config: Config, command_input: str, **kwargs):
        super().__init__(db_connector, config)
        self.command_input = command_input

    @property
    def is_restricted(self):
        return True

    def match_command(self):
        self.mactched_command = re.match(
            r"^(?P<command_name>\w+)\s?(?P<command_response>.*)", self.command_input
        )
        if self.mactched_command is not None:
            self.command_name, self.command_response = self.mactched_command.groups()

    def run(self):
        pass


class SetTextCommand(TextCommandSetter):
    def __init__(self, db_connector: DbConnector, config: Config, command_input: str, **kwargs):
        super().__init__(db_connector, config, command_input)
        self.match_command()

    def run(self):
        if self.command_name and self.command_response:
            # TODO: maybe we want to load the commands in a global so that we don't query the db every time
            command_exists = self.db_connector.retrive_command_response(
                command_name=self.command_name
            )
            if command_exists:
                self.db_connector.update_command(
                    command_name=self.command_name, command_response=self.command_response
                )
                return f"{self.command_name} command successfully updated"
            else:
                return f"{self.command_name} does not exist yet"
        else:
            return None


class AddTextCommand(TextCommandSetter):
    def __init__(self, db_connector: DbConnector, config: Config, command_input: str, **kwargs):
        super().__init__(db_connector, config, command_input, **kwargs)
        self.match_command()

    def run(self):
        if self.command_name and self.command_input:
            command_exists = self.db_connector.retrive_command_response(
                command_name=self.command_name
            )
            if command_exists:
                return f"{self.command_name} already exist use !set to update it"
            else:
                self.db_connector.add_new_command(
                    command_name=self.command_name, command_response=self.command_response
                )
                return f"{self.command_name} command successfully added"


class RemoveTextCommand(TextCommandSetter):
    def __init__(self, db_connector: DbConnector, config: Config, command_input: str, **kwargs):
        super().__init__(db_connector, config, command_input, **kwargs)
        self.match_command()

    def run(self) -> Optional[str]:
        if self.command_name:
            self.db_connector.remove_command(self.command_name)
            return f"{self.command_name} successfully removed"


SPECIAL_COMMANDS: Dict[str, Type[BaseCommand]] = {
    "hello": SayHelloCommand,
    "commands": ListCommandsCommand,
    "uptime": UptimeCommand,
    "setcountry": SetUserCountryCommand,
    "set": SetTextCommand,
    "add": AddTextCommand,
    "remove": RemoveTextCommand,
    "so": ShoutoutCommand,
}
COMMANDS_TO_IGNORE: List[str] = ["drop"]


def commands_factory(command_name: str) -> Optional[Type[BaseCommand]]:
    command = SPECIAL_COMMANDS.get(command_name)
    if command is not None:
        return command
    elif command_name not in COMMANDS_TO_IGNORE:
        return TextCommand
    else:
        return None
