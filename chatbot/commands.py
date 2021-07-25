import logging
from abc import ABC
from typing import Dict, Optional, Type

from db import DbConnector
from irc.client import ServerConnection


def send_message(connection: ServerConnection, channel: str, text: str):
    connection.privmsg(channel, text=f"{text}")


class BaseCommand(ABC):
    def __init__(self, db_connector: DbConnector, **kwargs):
        self.db_connector = db_connector

    @property
    def is_restricted(self):
        return False

    def run(self):
        raise NotImplementedError


class SayHelloCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, user_name: str, **kwargs):
        super().__init__(db_connector)
        self.user_name = user_name

    def run(self):
        message = f"Welcome to the stream, {self.user_name}"
        return message


class ListCommandsCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, **kwargs):
        super().__init__(db_connector)

    def run(self):
        all_commands = " !".join(AVAILABLE_COMMANDS)
        message = f"!{all_commands}"
        return message


class TodayCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, **kwargs):
        super().__init__(db_connector)

    def run(self):
        return self.db_connector.retrive_command_response("today")


class SetTodayCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, command_input: str, **kwargs):
        super().__init__(db_connector)
        self.today_text = command_input

    @property
    def is_restricted(self):
        return True

    def run(self):
        self.db_connector.update_command(command_name="today", command_response=self.today_text)
        logging.info("Today has been set")


class BotCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, **kwargs):
        super().__init__(db_connector)

    def run(self):
        return self.db_connector.retrive_command_response("bot")


class SourceCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, **kwargs):
        super().__init__(db_connector)

    def run(self):
        return self.db_connector.retrive_command_response("source")


class SetSourceCommand(BaseCommand):
    def __init__(self, db_connector: DbConnector, command_input: str, **kwargs):
        super().__init__(db_connector)
        self.source_text = command_input

    @property
    def is_restricted(self):
        return True

    def run(self):
        self.db_connector.update_command(command_name="source", command_response=self.source_text)


AVAILABLE_COMMANDS: Dict[str, Type[BaseCommand]] = {
    "hello": SayHelloCommand,  # type: ignore
    "commands": ListCommandsCommand,
    "today": TodayCommand,
    "settoday": SetTodayCommand,
    "bot": BotCommand,
    "source": SourceCommand,
    "settsource": SetSourceCommand,
}


def commands_factory(command_name: str) -> Optional[Type[BaseCommand]]:
    try:
        return AVAILABLE_COMMANDS[command_name]
    except KeyError as e:
        logging.exception("Looks like this command doesn't exist: %s", e)
        return None