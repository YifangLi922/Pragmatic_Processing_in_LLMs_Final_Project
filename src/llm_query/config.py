"""Load config/models.yaml into plain Python objects."""

from pathlib import Path

import yaml

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "models.yaml"


def load_config(path: Path | str = _DEFAULT_CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_model(config: dict, name: str) -> dict:
    for m in config["models"]:
        if m["name"] == name:
            return m
    raise KeyError(f"model '{name}' not found in config")
