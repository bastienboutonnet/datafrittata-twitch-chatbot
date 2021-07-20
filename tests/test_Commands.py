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
    cmd = SayHelloCommand(DbConnector(is_test=True), "DataFrittata")
    assert cmd.run() == "Welcome to the stream, DataFrittata"
    assert cmd.is_restricted is False


def test_ListCommandsCommand():
    cmd = ListCommandsCommand(DbConnector(is_test=True))
    assert cmd.run() == "!hello !commands !today !settoday !bot !source !settsource !reloadcommands"
    assert cmd.is_restricted is False


def test_TodayCommand():
    cmd = TodayCommand(DbConnector(is_test=True))
    assert cmd.run() == "today is not set yet 😭."
    assert cmd.is_restricted is False


def test_BotCommand():
    cmd = BotCommand(DbConnector(is_test=True))
    assert cmd.run() is None
    assert cmd.is_restricted is False


def test_SourceCommand():
    cmd = SourceCommand(DbConnector(is_test=True))
    assert cmd.run() == "source is not set yet."
    assert cmd.is_restricted is False
