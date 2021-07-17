import json
from typing import Dict

BOT_DATA: Dict[str, Dict[str, str]] = {
    "commands": {
        "today": "today is not set yet 😭.",
        "source": "source is not set yet.",
    }
}


def load_bot_data():
    with open("bot_data.json", "r") as f:
        data = json.loads(f.read())
        print(data)
        global BOT_DATA
        BOT_DATA = data


def save_bot_data(data: Dict[str, Dict[str, str]]):
    with open("bot_data.json", "w") as f:
        json.dump(data, f, indent=4)


def update_bot_data(
    data_dict: Dict[str, Dict[str, str]], data_part: str, data_content: Dict[str, str]
):
    if data_dict.get(data_part):
        data_dict[data_part].update(data_content)
        save_bot_data(data_dict)
        global BOT_DATA
        BOT_DATA = data_dict
