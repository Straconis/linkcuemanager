from pathlib import Path

from app.bulk_ingestion import (
    BulkIngestionProgressDialog,
    BulkIngestionWorker,
    read_csv_ingestion_items,
)


class FakeError(RuntimeError):
    def __init__(self, status_code: int):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


class FakeClient:
    def __init__(self):
        self.calls = []

    def add_queue_item(
        self,
        url,
        *,
        title=None,
        video_channel=None,
        submitted_by=None,
    ):
        self.calls.append(
            {
                "url": url,
                "title": title,
                "video_channel": video_channel,
                "submitted_by": submitted_by,
            }
        )

        if "duplicate" in url:
            raise FakeError(409)

        if "failure" in url:
            raise FakeError(500)

        return {"id": len(self.calls)}


def test_legacy_csv_extracts_only_link_column(tmp_path):
    path = tmp_path / "legacy.csv"

    path.write_text(
        "Link,Video Title,Channel,Custom Note\n"
        "https://youtu.be/one,Old One,Channel A,note\n"
        "\n"
        "https://www.tiktok.com/@x/video/2,Old Two,Channel B,note\n",
        encoding="utf-8",
    )

    items, label = read_csv_ingestion_items(path)

    assert label == "Legacy LinkCue CSV import"
    assert items == [
        {"url": "https://youtu.be/one"},
        {"url": "https://www.tiktok.com/@x/video/2"},
    ]


def test_current_csv_preserves_position_order_and_metadata(tmp_path):
    path = tmp_path / "queue.csv"

    path.write_text(
        "position,url,title,channel,submitted_by\n"
        "2,https://example.com/two,Two,Creator 2,Rose\n"
        "1,https://example.com/one,One,Creator 1,Steve\n",
        encoding="utf-8",
    )

    items, label = read_csv_ingestion_items(path)

    assert label == "Queue CSV import"
    assert [item["url"] for item in items] == [
        "https://example.com/one",
        "https://example.com/two",
    ]

    assert items[0]["title"] == "One"
    assert items[0]["video_channel"] == "Creator 1"
    assert items[0]["submitted_by"] == "Steve"


def test_worker_preserves_order_and_continues_after_item_failures():
    client = FakeClient()

    items = [
        {"url": "https://example.com/one"},
        {"url": "https://example.com/duplicate"},
        {"url": "https://example.com/failure"},
        {"url": "https://example.com/four"},
    ]

    worker = BulkIngestionWorker(
        client,
        items,
        default_submitted_by="ManagerUser",
    )

    results = []
    worker.completed.connect(results.append)

    worker._running = True
    worker._run()

    assert [call["url"] for call in client.calls] == [
        item["url"]
        for item in items
    ]

    assert all(
        call["submitted_by"] == "ManagerUser"
        for call in client.calls
    )

    assert results == [
        {
            "total": 4,
            "processed": 4,
            "added": 2,
            "already_queued": 1,
            "failed": 1,
            "cancelled": 0,
        }
    ]


def test_worker_cancel_leaves_remaining_items_unprocessed():
    client = FakeClient()

    worker = BulkIngestionWorker(
        client,
        [
            {"url": "https://example.com/one"},
            {"url": "https://example.com/two"},
        ],
        default_submitted_by="ManagerUser",
    )

    results = []
    worker.completed.connect(results.append)

    worker.cancel()
    worker._running = True
    worker._run()

    assert client.calls == []

    assert results[0]["processed"] == 0
    assert results[0]["cancelled"] == 2


def test_progress_dialog_reject_cancels_without_closing(qtbot):
    cancel_calls = []
    dialog = BulkIngestionProgressDialog(
        lambda: cancel_calls.append("cancel")
    )
    qtbot.addWidget(dialog)

    dialog.show()
    qtbot.waitExposed(dialog)

    dialog.reject()

    assert cancel_calls == ["cancel"]
    assert dialog.isVisible()


def test_progress_dialog_can_close_after_work_finishes(qtbot):
    dialog = BulkIngestionProgressDialog(lambda: None)
    qtbot.addWidget(dialog)

    dialog.show()
    qtbot.waitExposed(dialog)

    dialog.mark_finished()
    dialog.reject()

    assert not dialog.isVisible()
