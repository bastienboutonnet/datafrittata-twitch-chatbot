# TODO:
# - [ ] set up a commands table
# - [ ] set up some select capability
# - [ ] set up some stuff that allows us to update the commands table.


import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    ForeignKey,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError


# TODO: we might want to have a list of available commands somewhere in the class so that we can
# quickly check before updating so that we don't crash.
class DbConnector:
    def __init__(self, db_path: str = os.path.join(os.path.dirname(__file__), "../db/prod/")):

        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path}bot_database.db")
        self.metadata = MetaData()
        self.create_db()

    def create_db(self):
        self.commands = Table(
            "commands",
            self.metadata,
            Column("command_name", String(), primary_key=True),
            Column("command_response", String()),
        )

        self.users = Table(
            "users",
            self.metadata,
            Column("user_id", String(), primary_key=True),
            Column("user_name", String()),
            Column("country", String()),
            Column("first_chatted_at", DateTime()),
        )

        self.not_implemented_commands = Table(
            "not_implemented_commands",
            self.metadata,
            Column("command_name", String(), primary_key=True),
            Column("user_id", String(), ForeignKey("users.user_id")),
        )

        self.metadata.create_all(self.engine)

        self.add_new_command("today", "today is not set yet")
        self.add_new_command("source", "no source code or repo provided yet")
        self.add_new_command(
            "bot",
            "We're writing the bot on stream, you can find the repo here: "
            "https://github.com/bastienboutonnet/datafrittata-twitch-chatbot",
        )

    def add_new_user(self, user_id: str, user_name: str) -> None:
        try:
            stmt = insert(self.users).values(
                user_id=user_id, user_name=user_name, first_chatted_at=datetime.now()
            )
            self.conn = self.engine.connect()
            self.conn.execute(stmt)
        except IntegrityError:
            return None

    def add_not_implemented_command(self, command_name: str, user_id: str) -> None:
        try:
            stmt = insert(self.not_implemented_commands).values(
                command_name=command_name, user_id=user_id
            )
            self.conn = self.engine.connect()
            self.conn.execute(stmt)
        except IntegrityError:
            return None

    def update_user_country(self, user_id: str, user_country: str) -> None:
        try:
            stmt = (
                update(self.users)
                .where(self.users.c.user_id == user_id)
                .values(country=user_country)
            )
            self.conn = self.engine.connect()
            self.conn.execute(stmt)
        except Exception as e:
            logging.error(f"Could not update user country: {e}")
        return None

    def get_user_country(self, user_id: str) -> Optional[str]:
        stmt = select(self.users.c.country).where(self.users.c.user_id == user_id)
        self.conn = self.engine.connect()
        result = self.conn.execute(stmt)
        if result:
            row = result.fetchone()
            if row:
                return row[0]
            else:
                return None
        else:
            return None

    def add_new_command(self, command_name: str, command_response: str) -> None:
        print(f"Inserting {command_name} with: {command_response}")
        try:
            stmt = insert(self.commands).values((command_name, command_response))
            self.conn = self.engine.connect()
            self.conn.execute(stmt)
        except IntegrityError:
            print("command already exists, use a set<command> if you want to change its content")
        return

    def update_command(self, command_name: str, command_response: str) -> None:
        print(f"Updating {command_name} with: {command_response}")
        try:
            stmt = (
                update(self.commands)
                .where(self.commands.c.command_name == command_name)
                .values(command_response=command_response)
            )
            self.conn = self.engine.connect()
            self.conn.execute(stmt)
        except Exception as e:
            logging.error(f"Could not update command: {e}")
        return

    def retrive_command_response(self, command_name: str) -> Optional[str]:
        stmt = select(self.commands.c.command_response).where(
            self.commands.c.command_name == command_name
        )
        self.conn = self.engine.connect()
        result = self.conn.execute(stmt)
        if result:
            row = result.fetchone()
            if row:
                return row[0]
        return None
