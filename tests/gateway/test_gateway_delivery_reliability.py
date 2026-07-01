"""Gateway delivery reliability tests (Task 161)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.gateway import DeliveryManager, OutboundMessage, SendResult
from proseforge_agent.gateway.platforms.base import AdapterCapabilities


class RecordingAdapter:
    platform = "fake"

    def __init__(self, *, fail_sequences: set[int] | None = None, retry_sequences: set[int] | None = None) -> None:
        self.capabilities = AdapterCapabilities(threads=True, max_message_size=5)
        self.calls: list[OutboundMessage] = []
        self.fail_sequences = set(fail_sequences or set())
        self.retry_sequences = set(retry_sequences or set())
        self.attempts: dict[int, int] = {}

    def send(self, message: OutboundMessage) -> SendResult:
        self.calls.append(message)
        sequence = int(message.continuation_id.rsplit("-", 1)[-1])
        self.attempts[sequence] = self.attempts.get(sequence, 0) + 1
        if sequence in self.retry_sequences and self.attempts[sequence] == 1:
            return SendResult(delivered=False, retryable=True, reason="temporary token=secret")
        if sequence in self.fail_sequences:
            return SendResult(delivered=False, retryable=False, reason="hard token=secret")
        return SendResult(delivered=True, message_ids=[f"msg-{sequence}"], continuation_ids=[message.continuation_id])


def test_chunked_delivery_requires_all_continuations():
    adapter = RecordingAdapter(fail_sequences={1})
    manager = DeliveryManager(adapter=adapter, max_retries=1)

    result = manager.deliver(
        "session-1",
        OutboundMessage(platform="fake", chat_id="chat", thread_id="thread", text="hello world"),
    )

    assert result.delivered is False
    assert result.chunk_count == 3
    assert result.continuation_ids == ["session-1-0", "session-1-2"]
    assert result.errors == ["hard token=[redacted]"]


def test_delivery_retries_retryable_chunks_and_suppresses_duplicates():
    adapter = RecordingAdapter(retry_sequences={1})
    manager = DeliveryManager(adapter=adapter, max_retries=2)
    outbound = OutboundMessage(platform="fake", chat_id="chat", thread_id="thread", text="hello world")

    first = manager.deliver("session-1", outbound)
    second = manager.deliver("session-1", outbound)

    assert first.delivered is True
    assert first.retry_count == 1
    assert first.continuation_ids == ["session-1-0", "session-1-1", "session-1-2"]
    assert second.duplicate is True
    assert len(adapter.calls) == 4


def test_gateway_delivery_cli_check(capsys):
    assert main(["gateway", "delivery", "check", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Gateway Delivery" in out
    assert "delivered=true" in out
