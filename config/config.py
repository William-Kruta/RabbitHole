import os
import json


FILE_DIR = os.path.dirname(__file__)
RESEARCH_CONFIG_PATH = os.path.join(FILE_DIR, "research_config.json")
TOOLS_CONFIG_PATH = os.path.join(FILE_DIR, "tools_config.json")
SETTINGS_PATH = os.path.join(FILE_DIR, "settings.json")


def read_tools_config() -> dict:
    with open(TOOLS_CONFIG_PATH, "r") as f:
        return json.load(f)


def read_research_config() -> dict:
    with open(RESEARCH_CONFIG_PATH, "r") as f:
        return json.load(f)


def get_research_output_path() -> str:
    file = read_research_config()
    path = file["research_output"]
    return path


def read_settings():
    with open(SETTINGS_PATH, "r") as f:
        file = json.load(f)
    return file


def write_settings(data):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=4)
