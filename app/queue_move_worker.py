import threading

from PySide6.QtCore import QObject, Signal

from app.bot_client import BotClient


class QueueMoveWorker(QObject):
    completed = Signal(int, int, dict)
    failed = Signal(int, int, object)

    def __init__(
        self,
        client: BotClient,
        item_id: int,
        target_position: int,
    ) -> None:
        super().__init__()

        self.client = client
        self.item_id = int(item_id)
        self.target_position = int(target_position)
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
                name="LinkCueManagerQueueMove",
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
        try:
            result = self.client.move_queue_item(
                self.item_id,
                self.target_position,
            )
        except Exception as exc:
            self.failed.emit(
                self.item_id,
                self.target_position,
                exc,
            )
            return

        self.completed.emit(
            self.item_id,
            self.target_position,
            result,
        )
