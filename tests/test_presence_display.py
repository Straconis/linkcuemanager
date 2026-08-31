from types import SimpleNamespace

from app.window import ManagerWindow


def test_update_presence_counts_updates_both_labels():
    window = SimpleNamespace(
        player_count_label=SimpleNamespace(setText=lambda value: setattr(
            window.player_count_label, "text", value
        )),
        manager_count_label=SimpleNamespace(setText=lambda value: setattr(
            window.manager_count_label, "text", value
        )),
    )

    ManagerWindow._update_presence_counts(
        window,
        {
            "type": "connected",
            "player_count": 2,
            "manager_count": 3,
        },
    )

    assert window.player_count_label.text == "Players Connected: 2"
    assert window.manager_count_label.text == "Managers Connected: 3 (including this instance)"


def test_presence_event_updates_only_matching_count():
    player_updates = []
    manager_updates = []

    window = SimpleNamespace(
        player_count_label=SimpleNamespace(
            setText=player_updates.append
        ),
        manager_count_label=SimpleNamespace(
            setText=manager_updates.append
        ),
    )

    ManagerWindow.refresh_queue(
        window,
        {
            "type": "player_presence_changed",
            "player_count": 4,
        },
    )

    assert player_updates == ["Players Connected: 4"]
    assert manager_updates == []


def test_manager_presence_event_updates_only_manager_count():
    player_updates = []
    manager_updates = []

    window = SimpleNamespace(
        player_count_label=SimpleNamespace(
            setText=player_updates.append
        ),
        manager_count_label=SimpleNamespace(
            setText=manager_updates.append
        ),
    )

    ManagerWindow.refresh_queue(
        window,
        {
            "type": "manager_presence_changed",
            "manager_count": 2,
        },
    )

    assert player_updates == []
    assert manager_updates == ["Managers Connected: 2 (including this instance)"]


def test_presence_signal_updates_player_count(qtbot, monkeypatch):
    monkeypatch.setattr(
        "app.window.QueueEventListener.start",
        lambda self: None,
    )

    window = ManagerWindow()
    qtbot.addWidget(window)

    window.queue_refresh_requested.emit(
        {
            "type": "player_presence_changed",
            "player_count": 4,
        }
    )

    assert window.player_count_label.text() == "Players Connected: 4"
