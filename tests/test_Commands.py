from commands import (
    BotCommand,
    ListCommandsCommand,
    SayHelloCommand,
    SetSourceCommand,
    SetTodayCommand,
    SourceCommand,
    TodayCommand,
)


def test_SayHelloCommand():
    cmd = SayHelloCommand("DataFrittata")
    assert cmd.run() == "Welcome to the stream, DataFrittata"
    assert cmd.is_restricted is False


def test_ListCommandsCommand():
    cmd = ListCommandsCommand()
    assert cmd.run() == "!hello !commands !today !settoday !bot !source !settsource !reloadcommands"
    assert cmd.is_restricted is False


def test_TodayCommand():
    cmd = TodayCommand()
    assert cmd.run() == "today is not set yet 😭."
    assert cmd.is_restricted is False


# FIXME: find a way to test if "today" actually has been updated
def test_SetTodayCommand():
    cmd = SetTodayCommand(r"Today we're doing tests!")
    assert cmd.is_restricted is True
    assert cmd.today_text == r"Today we're doing tests!"


def test_BotCommand():
    cmd = BotCommand()
    assert cmd.run() is None
    assert cmd.is_restricted is False


def test_SourceCommand():
    cmd = SourceCommand()
    assert cmd.run() == "source is not set yet."
    assert cmd.is_restricted is False


# FIXME: find a way to test if "source" actually has been updated
def test_SetSourceCommand():
    cmd = SetSourceCommand(r"https://github.com/bastienboutonnet/datafrittata-twitch-chatbot")
    assert cmd.is_restricted is True
    assert cmd.source_text == r"https://github.com/bastienboutonnet/datafrittata-twitch-chatbot"
