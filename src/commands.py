import logging
from abc import ABC
from typing import Dict, Optional, Type

from irc.client import ServerConnection

TODAY: str = ""


def send_message(connection: ServerConnection, channel: str, text: str):
    connection.privmsg(channel, text=f"{text}")


class BaseCommand(ABC):
    def __init__(self, *args, **kwargs):
        ...

    @property
    def is_restricted(self):
        return False

    def run(self):
        raise NotImplementedError


class SayHelloCommand(BaseCommand):
    def __init__(self, user_name: str, **kwargs):
        super().__init__()
        self.user_name = user_name

    def run(self):
        message = f"Welcome to the stream, {self.user_name}"
        return message


class ListCommandsCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def run(self):
        all_commands = " !".join(AVAILABLE_COMMANDS)
        message = f"!{all_commands}"
        return message


class TodayCommand(BaseCommand):
    def __init__(self, **kwargs):
        super().__init__()

    def run(self):
        return TODAY


class SetTodayCommand(BaseCommand):
    def __init__(self, command_input: str, **kwargs):
        super().__init__()
        self.today_text = command_input

    @property
    def is_restricted(self):
        return True

    def run(self):
        global TODAY
        TODAY = self.today_text
        logging.info("Today has been set")


AVAILABLE_COMMANDS: Dict[str, Type[BaseCommand]] = {
    "hello": SayHelloCommand,  # type: ignore
    "commands": ListCommandsCommand,
    "today": TodayCommand,
    "settoday": SetTodayCommand,
}


def commands_factory(command_name: str) -> Optional[Type[BaseCommand]]:
    try:
        return AVAILABLE_COMMANDS[command_name]
    except KeyError as e:
        logging.exception("Looks like this command doesn't exist: %s", e)
        return None
