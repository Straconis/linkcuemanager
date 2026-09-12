from app.queue_move_worker import (
    QueueMoveWorker,
)


class FakeClient:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def move_queue_item(
        self,
        item_id,
        target_position,
    ):
        self.calls.append(
            (item_id, target_position)
        )

        if self.error is not None:
            raise self.error

        return {
            "id": item_id,
            "position": target_position,
        }


def test_queue_move_worker_emits_completion():
    client = FakeClient()
    worker = QueueMoveWorker(client, 7, 2)
    completed = []

    worker.completed.connect(
        lambda item_id, position, result:
        completed.append(
            (item_id, position, result)
        )
    )

    worker._run()

    assert client.calls == [(7, 2)]
    assert completed == [
        (
            7,
            2,
            {
                "id": 7,
                "position": 2,
            },
        )
    ]


def test_queue_move_worker_emits_failure():
    error = RuntimeError("network unavailable")
    client = FakeClient(error)
    worker = QueueMoveWorker(client, 8, 4)
    failures = []

    worker.failed.connect(
        lambda item_id, position, caught:
        failures.append(
            (item_id, position, caught)
        )
    )

    worker._run()

    assert client.calls == [(8, 4)]
    assert failures == [(8, 4, error)]
