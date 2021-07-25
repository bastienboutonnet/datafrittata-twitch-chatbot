import os
from pathlib import Path

import pytest

from commands import BotCommand, ListCommandsCommand, SayHelloCommand, SourceCommand, TodayCommand
from db import DbConnector

# make sure to grab the paths where the db will live in the
# context of pytest, potentially create the folder if needed
FIXTURE_DIR = Path(__file__).resolve().parents[1].joinpath("db/test")
os.makedirs(FIXTURE_DIR, exist_ok=True)


@pytest.mark.datafiles(FIXTURE_DIR)
def test_SayHelloCommand(datafiles):
    connector = DbConnector(db_path=datafiles)
    cmd = SayHelloCommand(connector, "DataFrittata")
    assert cmd.run() == "Welcome to the stream, DataFrittata"
    assert cmd.is_restricted is False


@pytest.mark.datafiles(FIXTURE_DIR)
def test_ListCommandsCommand(datafiles):
    connector = DbConnector(db_path=datafiles)
    cmd = ListCommandsCommand(connector)
    assert cmd.run() == "!hello !commands !today !settoday !bot !source !settsource !reloadcommands"
    assert cmd.is_restricted is False


@pytest.mark.datafiles(FIXTURE_DIR)
def test_TodayCommand(datafiles):
    connector = DbConnector(db_path=datafiles)
    cmd = TodayCommand(connector)
    assert cmd.run() == "today is not set yet"
    assert cmd.is_restricted is False


@pytest.mark.datafiles(FIXTURE_DIR)
def test_BotCommand(datafiles):
    connector = DbConnector(db_path=datafiles)
    cmd = BotCommand(connector)
    assert cmd.run() is None
    assert cmd.is_restricted is False


@pytest.mark.datafiles(FIXTURE_DIR)
def test_SourceCommand(datafiles):
    connector = DbConnector(db_path=datafiles)
    cmd = SourceCommand(connector)
    assert cmd.run() == "source is not set yet."
    assert cmd.is_restricted is False
