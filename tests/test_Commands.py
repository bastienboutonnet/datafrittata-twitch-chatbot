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


def test_SayHelloCommand():
    connector = DbConnector(is_test=True)
    cmd = SayHelloCommand(connector, "DataFrittata")
    assert cmd.run() == "Welcome to the stream, DataFrittata"
    assert cmd.is_restricted is False


def test_ListCommandsCommand():
    connector = DbConnector(is_test=True)
    cmd = ListCommandsCommand(connector)
    assert cmd.run() == "!hello !commands !today !settoday !bot !source !settsource !reloadcommands"
    assert cmd.is_restricted is False


def test_TodayCommand():
    connector = DbConnector(is_test=True)
    cmd = TodayCommand(connector)
    assert cmd.run() == "today is not set yet 😭."
    assert cmd.is_restricted is False


def test_BotCommand():
    connector = DbConnector(is_test=True)
    cmd = BotCommand(connector)
    assert cmd.run() is None
    assert cmd.is_restricted is False


def test_SourceCommand():
    connector = DbConnector(is_test=True)
    cmd = SourceCommand(connector)
    assert cmd.run() == "source is not set yet."
    assert cmd.is_restricted is False
