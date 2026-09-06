import threading

from PySide6.QtCore import QObject, Signal

from app.bot_hosting_restart import (
    BotHostingRestartService,
)


class BotHostingRestartWorker(QObject):
    started = Signal(str)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        service: BotHostingRestartService,
        mode: str,
    ) -> None:
        super().__init__()

        self.service = service
        self.mode = mode
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> bool:
        with self._lock:
            if (
                self._thread is not None
                and self._thread.is_alive()
            ):
                return False

            self._thread = threading.Thread(
                target=self._run,
                daemon=True,
                name="LinkCueManagerBotRestart",
            )

            self._thread.start()

        return True

    def is_running(self) -> bool:
        with self._lock:
            return (
                self._thread is not None
                and self._thread.is_alive()
            )

    def _run(self) -> None:
        self.started.emit(self.mode)

        try:
            result = self.service.restart(
                self.mode
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self.completed.emit(result)
