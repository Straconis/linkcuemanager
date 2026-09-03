from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_linkcue_settings(monkeypatch, tmp_path):
    import app.settings_store as settings_store

    linkcue_root = tmp_path / "LinkCue"
    shared_dir = linkcue_root / "shared"
    manager_dir = linkcue_root / "Manager"

    monkeypatch.setattr(
        settings_store,
        "LINKCUE_DATA_DIR",
        linkcue_root,
    )
    monkeypatch.setattr(
        settings_store,
        "SHARED_DATA_DIR",
        shared_dir,
    )
    monkeypatch.setattr(
        settings_store,
        "MANAGER_DATA_DIR",
        manager_dir,
    )
    monkeypatch.setattr(
        settings_store,
        "SHARED_CONFIG_PATH",
        shared_dir / "config.json",
    )
    monkeypatch.setattr(
        settings_store,
        "MANAGER_CONFIG_PATH",
        manager_dir / "config.json",
    )

    # window.py imported these functions directly, but the functions
    # themselves resolve the patched path globals from settings_store.
    yield
