import threading

from app.bot_hosting_restart_worker import (
    BotHostingRestartWorker,
)


class SuccessfulRestartService:
    def __init__(self):
        self.thread_id = None
        self.mode = None

    def restart(self, mode):
        self.thread_id = threading.get_ident()
        self.mode = mode

        return {
            "mode": mode,
            "health": {
                "status": "ok",
            },
        }


class FailingRestartService:
    def restart(self, mode):
        raise RuntimeError(
            "Host restart failed."
        )


class BlockingRestartService:
    def __init__(self):
        self.entered = threading.Event()
        self.release = threading.Event()

    def restart(self, mode):
        self.entered.set()
        self.release.wait(timeout=2.0)

        return {
            "mode": mode,
        }


def test_worker_runs_restart_off_main_thread(qtbot):
    service = SuccessfulRestartService()
    worker = BotHostingRestartWorker(
        service,
        "simulated",
    )

    main_thread_id = threading.get_ident()

    with qtbot.waitSignal(
        worker.completed,
        timeout=1000,
    ) as blocker:
        assert worker.start() is True

    assert service.mode == "simulated"
    assert service.thread_id != main_thread_id
    assert blocker.args == [
        {
            "mode": "simulated",
            "health": {
                "status": "ok",
            },
        }
    ]


def test_worker_emits_started_mode(qtbot):
    service = SuccessfulRestartService()
    worker = BotHostingRestartWorker(
        service,
        "direct",
    )

    with qtbot.waitSignal(
        worker.started,
        timeout=1000,
    ) as blocker:
        assert worker.start() is True

    assert blocker.args == ["direct"]


def test_worker_emits_failure_message(qtbot):
    worker = BotHostingRestartWorker(
        FailingRestartService(),
        "direct",
    )

    with qtbot.waitSignal(
        worker.failed,
        timeout=1000,
    ) as blocker:
        assert worker.start() is True

    assert blocker.args == [
        "Host restart failed."
    ]


def test_worker_rejects_second_start_while_running():
    service = BlockingRestartService()
    worker = BotHostingRestartWorker(
        service,
        "simulated",
    )

    try:
        assert worker.start() is True
        assert service.entered.wait(
            timeout=1.0
        )

        assert worker.is_running() is True
        assert worker.start() is False

    finally:
        service.release.set()
