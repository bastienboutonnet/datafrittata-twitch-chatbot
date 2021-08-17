import os
import re
from pathlib import Path

import pytest
import respx
from dateutil import parser
from httpx import Response

from chatbot.commands import (
    AddTextCommand,
    AddZodiacSignCommand,
    BotCommand,
    HoroscopeCommand,
    ListCommandsCommand,
    RemoveTextCommand,
    SayHelloCommand,
    SetSourceCommand,
    SetTextCommand,
    SetTodayCommand,
    SetUserCountryCommand,
    ShoutoutCommand,
    SourceCommand,
    TextCommand,
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
        == "!bot !source !today !hello !commands !uptime !setcountry !set !add !remove !so !addzodiacsign !horoscope"
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
    assert set_cmd.is_restricted is True


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
    assert set_cmd.is_restricted is True


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


@pytest.mark.parametrize(
    "mock_response, user_name, expectation",
    [
        pytest.param(
            {"data": [{"display_name": "DataFrittata", "broadcaster_login": "datafrittata"}]},
            "@DataFrittata",
            "You should check out DataFrittata or give them a follow here: https://twitch.tv/datafrittata <3",
            id="user exists and is provided with @",
        ),
        pytest.param(
            {"data": [{"display_name": "DataFrittata", "broadcaster_login": "datafrittata"}]},
            "DataFrittata",
            "You should check out DataFrittata or give them a follow here: https://twitch.tv/datafrittata <3",
            id="user exists and is provided without @",
        ),
        pytest.param(
            {"data": []},
            "doesntexistuser",
            "doesntexistuser doesn't seem to exist",
            id="user does not exists",
        ),
        pytest.param(
            {"data": [{"display_name": "DataFrittata", "broadcaster_login": "datafrittata"}]},
            "DataFritat",
            "DataFritat is not a valid user",
            id="is not a valid user",
        ),
    ],
)
@pytest.mark.datafiles(FIXTURE_DIR)
@respx.mock
def test_ShoutoutCommand(datafiles, mock_response, user_name, expectation):
    connector = DbConnector(db_path=datafiles)
    response = Response(status_code=200, json=mock_response)
    url_pattern = re.compile(r"^https://api.twitch.tv/helix/search/channels.*$")
    respx.get(url_pattern).mock(return_value=response)

    cmd = ShoutoutCommand(db_connector=connector, config=CONFIG, command_input=user_name)
    shoutout_response = cmd.run()
    assert shoutout_response == expectation


@pytest.mark.datafiles(FIXTURE_DIR)
def test_SetTextCommand(datafiles):
    expectation = "today this is the new today text set in the test"
    connector = DbConnector(db_path=datafiles)

    set_cmd = SetTextCommand(connector, CONFIG, command_input=expectation)
    set_result = set_cmd.run()

    today_cmd = TodayCommand(connector, CONFIG)
    today_text = today_cmd.run()

    assert set_result == "today command successfully updated"
    assert today_text.split("|")[1].strip() == "this is the new today text set in the test"


@pytest.mark.datafiles(FIXTURE_DIR)
def test_SetTextCommandNotFound(datafiles):
    expectation = "not_implemented_command dummy text"
    connector = DbConnector(db_path=datafiles)

    set_cmd = SetTextCommand(connector, CONFIG, command_input=expectation)
    set_result = set_cmd.run()

    assert set_cmd.is_restricted is True
    assert set_result == "not_implemented_command does not exist yet"


@pytest.mark.datafiles(FIXTURE_DIR)
def test_TextCommand(datafiles):
    expectation = "this is today's text set in the text command"
    connector = DbConnector(db_path=datafiles)

    SetTextCommand(connector, CONFIG, command_input=f"today {expectation}").run()

    command_response = TextCommand(connector, CONFIG, command_name="today").run()

    assert command_response == expectation


@pytest.mark.datafiles(FIXTURE_DIR)
def test_AddTextCommand(datafiles):
    expected_response = "this is the new command response"
    connector = DbConnector(db_path=datafiles)

    cmd = AddTextCommand(connector, CONFIG, "new_command this is the new command response")
    cmd.run()

    command_response = TextCommand(
        db_connector=connector, config=CONFIG, command_name="new_command"
    ).run()
    assert cmd.is_restricted is True
    assert command_response == expected_response


@pytest.mark.datafiles(FIXTURE_DIR)
def test_RemoveTextCommand(datafiles):
    connector = DbConnector(db_path=datafiles)

    AddTextCommand(connector, CONFIG, command_input="to_remove_command dummy text").run()
    cmd = RemoveTextCommand(connector, CONFIG, command_input="to_remove_command")
    cmd.run()

    command_response = TextCommand(connector, CONFIG, command_name="to_remove_command").run()
    assert command_response == "to_remove_command does not exist"


@pytest.mark.datafiles(FIXTURE_DIR)
def test_AddZodiacCommand(datafiles):
    sign = "taurus"
    connector = DbConnector(db_path=datafiles)

    connector.add_new_user(user_id="999", user_name="test_user")

    AddZodiacSignCommand(connector, CONFIG, command_input=sign, user_id="999").run()
    user_sign = connector.get_user_sign(user_id="999")

    assert user_sign == sign


@pytest.mark.datafiles(FIXTURE_DIR)
@respx.mock
def test_HoroscopeCommand(datafiles):
    exp = "It's hard to be a Taurus"
    connector = DbConnector(db_path=datafiles)
    connector.add_new_user(user_id="999", user_name="test_user")
    AddZodiacSignCommand(connector, CONFIG, command_input="taurus", user_id="999").run()

    response = Response(status_code=200, json={"horoscope": exp})
    respx.get("https://ohmanda.com/api/horoscope/taurus").mock(return_value=response)

    horoscope_text = HoroscopeCommand(connector, CONFIG, user_id="999").run()
    assert horoscope_text == f"Taurus: {exp}"
