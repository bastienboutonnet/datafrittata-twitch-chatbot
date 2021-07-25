import os
from pathlib import Path

import pytest
from commands import (
    BotCommand,
    ListCommandsCommand,
    SayHelloCommand,
    SetSourceCommand,
    SetTodayCommand,
    SourceCommand,
    TodayCommand,
)
from db import DbConnector

# make sure to grab the paths where the db will live in the
# context of pytest, potentially create the folder if needed
FIXTURE_DIR = Path(__file__).resolve().parents[1].joinpath("db/test/")
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
    assert cmd.run() == "!hello !commands !today !settoday !bot !source !settsource"
    assert cmd.is_restricted is False


@pytest.mark.dependency()
@pytest.mark.datafiles(FIXTURE_DIR)
def test_TodayCommand(datafiles):
    connector = DbConnector(db_path=datafiles)
    cmd = TodayCommand(connector)
    assert cmd.run() == "today is not set yet"
    assert cmd.is_restricted is False


@pytest.mark.datafiles(FIXTURE_DIR)
def test_BotCommand(datafiles):
    expectation = (
        "We're writing the bot on stream, you can find the repo here: "
        "https://github.com/bastienboutonnet/datafrittata-twitch-chatbot"
    )

    connector = DbConnector(db_path=datafiles)
    cmd = BotCommand(connector)
    assert cmd.run() == expectation
    assert cmd.is_restricted is False


@pytest.mark.dependency()
@pytest.mark.datafiles(FIXTURE_DIR)
def test_SourceCommand(datafiles):
    expectation = "no source code or repo provided yet"
    connector = DbConnector(db_path=datafiles)
    cmd = SourceCommand(connector)
    assert cmd.run() == expectation
    assert cmd.is_restricted is False


@pytest.mark.dependency(depends=["test_TodayCommand"])
@pytest.mark.datafiles(FIXTURE_DIR)
def test_SetTodayCommand(datafiles):
    expectation = "this is the test today"
    connector = DbConnector(db_path=datafiles)

    set_cmd = SetTodayCommand(connector, command_input=expectation)
    set_cmd.run()

    today = TodayCommand(connector)
    today_text = today.run()

    assert today_text == expectation
    assert set_cmd.is_restricted == True


@pytest.mark.dependency(depends=["test_SourceCommand"])
@pytest.mark.datafiles(FIXTURE_DIR)
def test_SetSourceCommand(datafiles):
    expectation = "this is the source test text"
    connector = DbConnector(db_path=datafiles)

    set_cmd = SetSourceCommand(connector, command_input=expectation)
    set_cmd.run()

    today = SourceCommand(connector)
    source_text = today.run()

    assert source_text == expectation
    assert set_cmd.is_restricted == True
