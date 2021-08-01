import os
from pathlib import Path

import pytest
import respx
from httpx import Response

from chatbot.commands import (
    BotCommand,
    ListCommandsCommand,
    SayHelloCommand,
    SetSourceCommand,
    SetTodayCommand,
    SetUserCountryCommand,
    SourceCommand,
    TodayCommand,
    UptimeCommand,
)
from chatbot.db import DbConnector

# make sure to grab the paths where the db will live in the
# context of pytest, potentially create the folder if needed
FIXTURE_DIR = Path(__file__).resolve().parents[1].joinpath("../db/test/")
os.makedirs(FIXTURE_DIR, exist_ok=True)


class Config:
    def __init__(self) -> None:
        self.client_id = ""
        self.client_secret = ""
        self.oauth_token = ""
        self.bot_name = ""
        self.channel = "datafrittata"
        self.oauth_token_api = ""
        self.client_id_api = ""
        self.bot_api_token = ""


def init_connectors_and_config(datafiles) -> Config:
    config = Config()
    return config


CONFIG = init_connectors_and_config(FIXTURE_DIR)


@pytest.mark.datafiles(FIXTURE_DIR)
def test_SayHelloCommand(datafiles):
    connector = DbConnector(db_path=datafiles)
    cmd = SayHelloCommand(connector, CONFIG, "DataFrittata")
    assert cmd.run() == "Welcome to the stream, DataFrittata"
    assert cmd.is_restricted is False


@pytest.mark.datafiles(FIXTURE_DIR)
def test_ListCommandsCommand(datafiles):
    connector = DbConnector(db_path=datafiles)
    cmd = ListCommandsCommand(connector, CONFIG)
    assert (
        cmd.run()
        == "!hello !commands !today !settoday !bot !source !settsource !uptime !setcountry"
    )
    assert cmd.is_restricted is False


@pytest.mark.dependency()
@pytest.mark.datafiles(FIXTURE_DIR)
def test_TodayCommand(datafiles):
    connector = DbConnector(db_path=datafiles)
    cmd = TodayCommand(connector, CONFIG)
    cmd_resp = cmd.run()
    assert cmd_resp is not None
    assert cmd_resp.split("|")[1].strip() == "today is not set yet"
    assert cmd.is_restricted is False


@pytest.mark.datafiles(FIXTURE_DIR)
def test_BotCommand(datafiles):
    expectation = (
        "We're writing the bot on stream, you can find the repo here: "
        "https://github.com/bastienboutonnet/datafrittata-twitch-chatbot"
    )

    # connector = DbConnector(db_path=datafiles)
    connector = DbConnector(db_path=datafiles)
    cmd = BotCommand(connector, CONFIG)
    assert cmd.run() == expectation
    assert cmd.is_restricted is False


@pytest.mark.dependency()
@pytest.mark.datafiles(FIXTURE_DIR)
def test_SourceCommand(datafiles):
    expectation = "no source code or repo provided yet"
    connector = DbConnector(db_path=datafiles)
    cmd = SourceCommand(connector, CONFIG)
    assert cmd.run() == expectation
    assert cmd.is_restricted is False


@pytest.mark.dependency(depends=["test_TodayCommand"])
@pytest.mark.datafiles(FIXTURE_DIR)
def test_SetTodayCommand(datafiles):
    expectation = "this is the test today"

    connector = DbConnector(db_path=datafiles)
    set_cmd = SetTodayCommand(connector, CONFIG, command_input=expectation)
    set_cmd.run()

    today = TodayCommand(connector, CONFIG)
    today_text = today.run()

    assert today_text is not None
    assert today_text.split("|")[1].strip() == expectation
    assert set_cmd.is_restricted == True


@pytest.mark.datafiles(FIXTURE_DIR)
def test_SetUserCountryCommand(datafiles):
    expectation = "france"
    # connector = DbConnector(db_path=datafiles)
    connector = DbConnector(db_path=datafiles)
    connector.add_new_user(user_id="999", user_name="test_user")

    set_cmd = SetUserCountryCommand(connector, CONFIG, command_input=expectation, user_id="999")
    set_cmd.run()

    user_country = connector.get_user_country(user_id="999")
    assert user_country == expectation


@pytest.mark.dependency(depends=["test_SourceCommand"])
@pytest.mark.datafiles(FIXTURE_DIR)
def test_SetSourceCommand(datafiles):
    expectation = "this is the source test text"
    connector = DbConnector(db_path=datafiles)

    set_cmd = SetSourceCommand(connector, CONFIG, command_input=expectation)
    set_cmd.run()

    today = SourceCommand(connector, CONFIG)
    source_text = today.run()

    assert source_text == expectation
    assert set_cmd.is_restricted == True


@pytest.mark.parametrize(
    "mock_response, time_offset, expectation",
    [
        pytest.param(
            {},
            "2021-08-01T12:59:25Z",
            f"{CONFIG.channel} is not currently streaming",
            id="channel is not live",
        ),
        pytest.param(
            {"data": [{"started_at": "2021-08-01T12:57:25Z"}]},
            "2021-08-01T12:59:25Z",
            "We've been online for 2 minutes and 0 seconds",
            id="channel is live for < 1 hour",
        ),
        pytest.param(
            {"data": [{"started_at": "2021-08-01T12:57:25Z"}]},
            "2021-08-01T14:57:25Z",
            "We've been online for 2 hours, 0 minutes and 0 seconds",
            id="channel is live for > 1 hour",
        ),
    ],
)
@pytest.mark.datafiles(FIXTURE_DIR)
@respx.mock
@pytest.mark.freeze_time
def test_UptimeCommand(datafiles, mock_response, time_offset, expectation, freezer):
    connector = DbConnector(db_path=datafiles)

    respx.get(f"https://api.twitch.tv/helix/streams?user_login={CONFIG.channel}").mock(
        return_value=Response(status_code=200, json=mock_response)
    )

    freezer.move_to(time_offset)
    cmd = UptimeCommand(db_connector=connector, config=CONFIG)
    uptime_response = cmd.run()
    assert uptime_response == expectation
