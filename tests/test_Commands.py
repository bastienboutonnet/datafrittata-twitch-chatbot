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


connector = DbConnector(is_test=True)


def test_SayHelloCommand():
    cmd = SayHelloCommand(connector, "DataFrittata")
    assert cmd.run() == "Welcome to the stream, DataFrittata"
    assert cmd.is_restricted is False


def test_ListCommandsCommand():
    cmd = ListCommandsCommand(connector)
    assert cmd.run() == "!hello !commands !today !settoday !bot !source !settsource !reloadcommands"
    assert cmd.is_restricted is False


def test_TodayCommand():
    cmd = TodayCommand(connector)
    assert cmd.run() == "today is not set yet 😭."
    assert cmd.is_restricted is False


def test_BotCommand():
    cmd = BotCommand(connector)
    assert cmd.run() is None
    assert cmd.is_restricted is False


def test_SourceCommand():
    cmd = SourceCommand(connector)
    assert cmd.run() == "source is not set yet."
    assert cmd.is_restricted is False
