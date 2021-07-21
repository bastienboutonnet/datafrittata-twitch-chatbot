# TODO:
# - [ ] set up a commands table
# - [ ] set up some select capability
# - [ ] set up some stuff that allows us to update the commands table.


import os
from typing import Optional

from sqlalchemy import Column, MetaData, String, Table, create_engine, insert, select, update
from sqlalchemy.exc import IntegrityError


# TODO: we might want to have a list of available commands somewhere in the class so that we can
# quickly check before updating so that we don't crash.
class DbConnector:
    def __init__(self, db_path: str = "../db/prod"):

        # if is_test:
        # db_name = "test_bot_db"
        # else:
        # db_name = "bot_database"

        os.makedirs(db_path, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}/bot_database.db")
        self.metadata = MetaData()
        self.create_db()

    def create_db(self):
        self.commands = Table(
            "commands",
            self.metadata,
            Column("command_name", String(), primary_key=True),
            Column("command_response", String()),
        )
        self.metadata.create_all(self.engine)

        self.add_new_command("today", "today is not set yet")
        self.add_new_command("source", "no source code or repo provided yet")

    def add_new_command(self, command_name: str, command_response: str) -> None:
        print("Inserting {command_name} with: {command_response}")
        try:
            stmt = insert(self.commands).values((command_name, command_response))
            self.conn = self.engine.connect()
            self.conn.execute(stmt)
        except IntegrityError:
            print("command already exists")
        return

    def update_command(self, command_name: str, command_response: str) -> None:
        print("Updating {command_name} with: {command_response}")
        stmt = (
            update(self.commands)
            .where(self.commands.c.command_name == command_name)
            .values(command_response=command_response)
        )
        self.conn = self.engine.connect()
        self.conn.execute(stmt)
        return

    def retrive_command_response(self, command_name: str) -> Optional[str]:
        stmt = select(self.commands.c.command_response).where(
            self.commands.c.command_name == command_name
        )
        self.conn = self.engine.connect()
        result = self.conn.execute(stmt)
        if result:
            row = result.fetchone()
            return row[0]
        return None
