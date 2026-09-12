from __future__ import annotations

import csv
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog


def read_csv_ingestion_items(
    file_path: str | Path,
) -> tuple[list[dict], str]:
    path = Path(file_path)

    with path.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError("CSV has no header.")

        headers = {
            header.strip().casefold(): header
            for header in reader.fieldnames
            if header is not None
        }

        # ----------------------------------------------------
        # Current LinkCue Manager queue export.
        # Preserve its optional metadata and queue position.
        # ----------------------------------------------------

        if "url" in headers:
            items: list[dict] = []
            positions: set[int] = set()

            for line_number, row in enumerate(
                reader,
                start=2,
            ):
                url = (
                    row.get(headers["url"]) or ""
                ).strip()

                if not url:
                    continue

                item: dict = {
                    "url": url,
                }

                for csv_name, item_name in (
                    ("title", "title"),
                    ("channel", "video_channel"),
                    ("submitted_by", "submitted_by"),
                ):
                    header = headers.get(csv_name)

                    if header is None:
                        continue

                    value = (
                        row.get(header) or ""
                    ).strip()

                    if value:
                        item[item_name] = value

                position_header = headers.get("position")

                if position_header is not None:
                    raw_position = (
                        row.get(position_header) or ""
                    ).strip()

                    if not raw_position:
                        raise ValueError(
                            f"line {line_number} has no position."
                        )

                    try:
                        position = int(raw_position)
                    except ValueError as exc:
                        raise ValueError(
                            f"line {line_number} has an invalid position."
                        ) from exc

                    if position < 1:
                        raise ValueError(
                            f"line {line_number} position must be positive."
                        )

                    if position in positions:
                        raise ValueError(
                            "duplicate positions found."
                        )

                    positions.add(position)
                    item["_position"] = position

                items.append(item)

            if "position" in headers:
                items.sort(
                    key=lambda item: item["_position"]
                )

                for item in items:
                    item.pop("_position", None)

            if not items:
                raise ValueError(
                    "CSV contains no video URLs."
                )

            return items, "Queue CSV import"

        # ----------------------------------------------------
        # LinkCue Legacy format.
        #
        # Only the Link column matters. Everything else is
        # intentionally ignored and normal ingestion resolves
        # current metadata.
        # ----------------------------------------------------

        if "link" in headers:
            items = []

            link_header = headers["link"]

            for row in reader:
                url = (
                    row.get(link_header) or ""
                ).strip()

                if not url:
                    continue

                items.append(
                    {
                        "url": url,
                    }
                )

            if not items:
                raise ValueError(
                    "Legacy CSV contains no links."
                )

            return items, "Legacy LinkCue CSV import"

        raise ValueError(
            "CSV must contain either a 'url' column "
            "or legacy LinkCue 'Link' column."
        )


class BulkIngestionWorker(QObject):
    item_started = Signal(
        int,
        int,
        str,
    )

    progress = Signal(
        int,
        int,
        str,
        int,
        int,
        int,
    )

    completed = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        bot_client,
        items: list[dict],
        *,
        default_submitted_by: str | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)

        self._bot_client = bot_client
        self._items = [
            dict(item)
            for item in items
        ]
        self._default_submitted_by = (
            default_submitted_by
        )

        self._cancel_event = threading.Event()
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def run(self) -> None:
        if self._running:
            return

        self._running = True
        self._run()

    def cancel(self) -> None:
        self._cancel_event.set()

    def _run(self) -> None:
        total = len(self._items)
        processed = 0
        added = 0
        already_queued = 0
        failed = 0

        try:
            for index, item in enumerate(
                self._items,
                start=1,
            ):
                if self._cancel_event.is_set():
                    break

                url = str(
                    item.get("url") or ""
                ).strip()

                self.item_started.emit(
                    index,
                    total,
                    url,
                )

                try:
                    submitted_by = (
                        item.get("submitted_by")
                        or self._default_submitted_by
                    )

                    self._bot_client.add_queue_item(
                        url,
                        title=item.get("title"),
                        video_channel=(
                            item.get("video_channel")
                        ),
                        submitted_by=submitted_by,
                    )

                    added += 1

                except Exception as exc:
                    if (
                        getattr(
                            exc,
                            "status_code",
                            None,
                        )
                        == 409
                    ):
                        already_queued += 1
                    else:
                        failed += 1

                processed += 1

                self.progress.emit(
                    processed,
                    total,
                    url,
                    added,
                    already_queued,
                    failed,
                )

            cancelled = max(
                0,
                total - processed,
            )

            self.completed.emit(
                {
                    "total": total,
                    "processed": processed,
                    "added": added,
                    "already_queued": already_queued,
                    "failed": failed,
                    "cancelled": cancelled,
                }
            )

        except Exception as exc:
            self.failed.emit(str(exc))

        finally:
            self._running = False


class BulkIngestionProgressDialog(QDialog):
    def __init__(
        self,
        cancel_callback,
        parent=None,
    ):
        super().__init__(parent)
        self._cancel_callback = cancel_callback
        self._work_active = True
        self.setObjectName("bulkIngestionProgressDialog")

    def mark_finished(self) -> None:
        self._work_active = False

    def reject(self) -> None:
        if self._work_active:
            self._cancel_callback()
            return

        super().reject()

    def closeEvent(self, event) -> None:
        if self._work_active:
            self._cancel_callback()
            event.ignore()
            return

        super().closeEvent(event)
