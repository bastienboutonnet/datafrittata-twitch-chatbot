import re
from datetime import datetime
from typing import Dict, List, Optional

import irc.bot
from rich.console import Console
from rich.emoji import EMOJI

from chatbot.commands import COMMANDS_TO_IGNORE, commands_factory, send_message
from chatbot.config import Config
from chatbot.db import DbConnector

console = Console()

START_TIME = datetime.now()

# TODO: DOn't forget to thank wOrd2vect for the tip on irc.bot


class Bot(irc.bot.SingleServerIRCBot):
    ELEVATED_BADGES = {"broadcaster"}

    def __init__(self, config: Config, db_connector: DbConnector):
        self._config = config
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
        keys_to_retain = ["color", "display-name", "badges", "user-id"]
        data = {"message": event.arguments[0]}

        # TODO: find a way to rename the keys in a not so fucky way.
        for tag in event.tags:
            if tag["key"] in keys_to_retain:
                if tag["key"] == "display-name":
                    data.update({"user_name": tag["value"]})
                elif tag["key"] == "user-id":
                    data.update({"user_id": tag["value"]})
                else:
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
        else:
            return []

    # consider parsing the other versions of the sub badges and having the start symbol fill up
    # 紐and 留and 硫
    @staticmethod
    def generate_badge_string(badges: List[str]) -> Optional[str]:
        badge_mapping: Dict[str, str] = {
            "founder": "[#7F45E9] [/#7F45E9]",
            "subscriber": "[#FD3E81]六[/#FD3E81]",
            "broadcaster": "[#BBD5ED] [/#BBD5ED]",
            "vip": "[#008DD5] [/#008DD5]",
            "premium": "[#a9f0ee] [/#a9f0ee]",
        }
        badges_str = []
        for badge in badges:
            badges_str.append(badge_mapping.get(badge, ""))
        if badges_str:
            return "".join(badges_str)
        return None

    def on_pubmsg(self, connection, event):
        event_data = self.structure_message(event)
        message_text = event_data["message"]
        user_name = event_data["user_name"]
        user_id = event_data["user_id"]
        user_colour = event_data["color"]
        user_badges = self.process_badges(event_data["badges"])
        # add a placeholder that gets filled in later on if needed
        event_data["command_input"] = ""
        badges_str = self.generate_badge_string(user_badges)

        # do the country emoji thingie
        user_country_emoji = self.db_connector.get_user_country(user_id=user_id)
        if user_country_emoji is not None:
            user_country_emoji = user_country_emoji.strip(":")
            if user_country_emoji in list(EMOJI.keys()):
                user_country_emoji = f":{user_country_emoji}: "
        else:
            user_country_emoji = ""

        # printing to the terminal stuff
        if not user_colour:
            user_colour = "#fff44f"
        console.print(
            f"{badges_str}[{user_colour}][bold]{user_name}[/bold][/{user_colour}] "
            f"{user_country_emoji}: "
            f"[#00BFFF]{message_text}[/#00BFFF]"
        )
        # attempt to add the uer to the database.
        self.db_connector.add_new_user(user_id=user_id, user_name=user_name)
        command_match = re.match(r"^!(?P<command_name>\w+)\s?(?P<command_text>.*)", message_text)
        if command_match is None:
            return

        command_name, command_input = command_match.groups()

        command = commands_factory(command_name)

        if command_input:
            event_data.update({"command_input": command_input})
        if command:
            command_output = ""
            command = command(self.db_connector, self._config, **event_data)  # type: ignore
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
