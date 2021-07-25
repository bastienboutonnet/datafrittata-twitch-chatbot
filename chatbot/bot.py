import re
from typing import Dict, List, Optional

import irc.bot
from rich.console import Console

from chatbot.commands import COMMANDS_TO_IGNORE, commands_factory, send_message
from chatbot.config import Config
from chatbot.db import DbConnector

console = Console()


# TODO: DOn't forget to thank wOrd2vect for the tip on irc.bot


class Bot(irc.bot.SingleServerIRCBot):
    ELEVATED_BADGES = {"broadcaster"}

    def __init__(self, config: Config, db_connector: DbConnector):
        self._config = config
        self.client_id = self._config.client_id
        self.token = self._config.oauth_token
        self.channel = f"#{self._config.channel}"
        self.bot_name = self._config.bot_name
        self.db_connector = db_connector

        # Create IRC bot connection
        server = "irc.chat.twitch.tv"
        port = 6667
        print("Connecting to " + server + " on port " + str(port) + "...")
        irc.bot.SingleServerIRCBot.__init__(
            self, [(server, port, self.token)], self.bot_name, self.bot_name
        )

    def on_welcome(self, connection, event):
        print("Joining " + self.channel)

        # You must request specific capabilities before you can use them
        connection.cap("REQ", ":twitch.tv/membership")
        connection.cap("REQ", ":twitch.tv/tags")
        connection.cap("REQ", ":twitch.tv/commands")
        connection.join(self.channel)
        connection.privmsg(self.channel, text="Hello, I am the bot")

    @staticmethod
    def structure_message(event) -> Dict[str, str]:
        keys_to_retain = ["color", "display-name", "badges"]
        data = {"message": event.arguments[0]}

        # TODO: find a way to rename the keys in a not so fucky way.
        for tag in event.tags:
            if tag["key"] in keys_to_retain:
                if tag["key"] == "display-name":
                    tag["key"] = "user_name"
                data.update({tag["key"]: tag["value"]})

        return data

    @staticmethod
    def process_badges(badges: str) -> List[str]:
        # TODO: maybe we shove it in to a class and let the constructor take care of the magic
        if badges is not None:
            _badges = badges.split(",")
            final_badges = []
            for badge in _badges:
                match = re.match(r"^(\w+)/(\d+)", badge)
                if match:
                    # the second element is the badge version which we throw away for now.
                    badge_name, _ = match.groups()
                    final_badges.append(badge_name)
            return final_badges

    @staticmethod
    def generate_badge_string(badges: List[str]) -> Optional[str]:
        badge_mapping: Dict[str, str] = {"founder": "[#7F45E9] 1st [/#7F45E9]"}
        badges_str = []
        for badge in badges:
            badges_str.append(badge_mapping.get(badge, ""))
        print(badges_str)
        if badges_str:
            return "".join(badges_str)
        return None

    def on_pubmsg(self, connection, event):
        event_data = self.structure_message(event)
        message_text = event_data["message"]
        user_name = event_data["user_name"]
        user_colour = event_data["color"]
        user_badges = self.process_badges(event_data["badges"])
        # add a placeholder that gets filled in later on if needed
        event_data["command_input"] = ""
        badges_str = self.generate_badge_string(user_badges)
        # printing to the terminal stuff
        if not user_colour:
            user_colour = "#fff44f"
        console.print(
            f"{badges_str}[{user_colour}]{user_name}[/{user_colour}]: [#00BFFF]{message_text} [/#00BFFF]"
        )

        command_match = re.match(r"^!(?P<command_name>\w+)\s?(?P<command_text>.*)", message_text)
        if command_match is None:
            return

        command_name, command_input = command_match.groups()

        command = commands_factory(command_name)

        if command_input:
            event_data.update({"command_input": command_input})
        if command:
            command_output = ""
            command = command(self.db_connector, **event_data)  # type: ignore
            if command.is_restricted and not set(user_badges).intersection(self.ELEVATED_BADGES):
                pass
            else:
                command_output = command.run()
            if command_output:
                send_message(connection=connection, channel=self.channel, text=command_output)
        elif not command and command_name not in COMMANDS_TO_IGNORE:
            command_output = (
                f"Looks like the bot doesn't know {command_name}. "
                "Do !commands to find out what it can do."
            )
            # TODO: add the unknown command to a db table of non-imple commands
            # so that we can, maybe, add it later.
            send_message(connection=connection, channel=self.channel, text=command_output)


def main():
    config = Config()
    db_connector = DbConnector()
    bot = Bot(config, db_connector=db_connector)
    bot.start()


if __name__ == "__main__":
    main()
