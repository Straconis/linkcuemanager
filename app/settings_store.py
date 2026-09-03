import json
import os
from pathlib import Path
from typing import Any


def _appdata_root() -> Path:
    appdata = os.getenv("APPDATA")

    if appdata:
        return Path(appdata) / "LinkCue"

    # Fallback mainly for development/testing on non-Windows systems.
    return Path.home() / ".config" / "LinkCue"


LINKCUE_DATA_DIR = _appdata_root()
SHARED_DATA_DIR = LINKCUE_DATA_DIR / "shared"
MANAGER_DATA_DIR = LINKCUE_DATA_DIR / "Manager"

SHARED_CONFIG_PATH = SHARED_DATA_DIR / "config.json"
MANAGER_CONFIG_PATH = MANAGER_DATA_DIR / "config.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def _save_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )


def load_shared_settings() -> dict[str, Any]:
    return _load_json(SHARED_CONFIG_PATH)


def save_shared_settings(
    settings: dict[str, Any],
) -> None:
    _save_json(
        SHARED_CONFIG_PATH,
        settings,
    )


def load_manager_settings() -> dict[str, Any]:
    return _load_json(MANAGER_CONFIG_PATH)


def save_manager_settings(
    settings: dict[str, Any],
) -> None:
    _save_json(
        MANAGER_CONFIG_PATH,
        settings,
    )

