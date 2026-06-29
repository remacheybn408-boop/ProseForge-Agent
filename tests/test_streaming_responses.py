"""Tests for streaming responses (Task 63)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from proseforge_agent.agent import AgentTurnRequest
from proseforge_agent.agent.kernel import AgentKernel
from proseforge_agent.chat.repl import ChatRepl
from proseforge_agent.llm import FakeProvider, Message, ProviderRequest
from proseforge_agent.llm.base import ProviderResult, StreamChunk
from proseforge_agent.llm.streaming import (
    NonStreamingAdapter,
    aggregate_text,
    as_streaming,
    iter_stream,
)

FIXTURE = (
    Path(__file__).parent / "fixtures" / "streaming-responses" / "chunks.json"
)


def _request(text: str = "hi") -> ProviderRequest:
    return ProviderRequest(role="drafter", messages=[Message(role="user", content=text)])


def _turn(text: str) -> AgentTurnRequest:
    return AgentTurnRequest(
        session_id="s",
        text=text,
        mode="general_chat",
        project_slug=None,
        permission_level="read_only",
    )


@pytest.fixture
def fake_streaming_provider() -> FakeProvider:
    return FakeProvider(name="fake", model="fake-novelist")


class GenerateOnlyProvider:
    """A provider that implements only the one-shot channel."""

    name = "legacy"
    model = "legacy-1"

    def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(provider=self.name, model=self.model, text="one shot only")


class RecordingStream(io.StringIO):
    """Capture each individual write so incremental output is observable."""

    def __init__(self) -> None:
        super().__init__()
        self.writes: list[str] = []

    def write(self, s: str) -> int:  # type: ignore[override]
        self.writes.append(s)
        return super().write(s)


class _FakeSessionStore:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str, str]] = []

    def ensure_session(self, session_id, mode, project_slug):
        return None

    def append_message(self, session_id, role, content):
        self.messages.append((session_id, role, content))

    def record_event(self, event):
        return None


class _BrokenStreamProvider:
    name = "broken"
    model = "broken-1"

    def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(provider=self.name, model=self.model, text="full text")

    def generate_stream(self, request: ProviderRequest):
        yield StreamChunk(text="partial ", done=False, index=0)
        raise RuntimeError("connection dropped")


def test_aggregated_stream_equals_full_text(fake_streaming_provider):
    chunks = list(fake_streaming_provider.generate_stream(_request()))
    assert chunks[-1].done is True
    assert aggregate_text(chunks) == fake_streaming_provider.generate(_request()).text


def test_non_streaming_provider_yields_single_done_chunk():
    provider = GenerateOnlyProvider()
    adapted = as_streaming(provider)
    assert isinstance(adapted, NonStreamingAdapter)
    chunks = list(adapted.generate_stream(_request()))
    assert len(chunks) == 1
    assert chunks[0].done is True
    assert chunks[0].text == provider.generate(_request()).text


def test_repl_prints_chunks_incrementally(fake_streaming_provider):
    output = RecordingStream()
    repl = ChatRepl(
        provider=fake_streaming_provider,
        session_store=_FakeSessionStore(),
        input_stream=io.StringIO("hello there friend\n/exit\n"),
        output_stream=output,
        stream=True,
    )
    repl.run()
    # The streamed turn produced several separate writes (more than one chunk),
    # proving the output was incremental rather than one final blob.
    content_writes = [w for w in output.writes if w not in ("", "\n")]
    assert len(content_writes) > 1


def test_transcript_saved_text_matches_non_streaming_result(fake_streaming_provider):
    text = "讲一个安静的开头"
    non_stream_store = _FakeSessionStore()
    AgentKernel(provider=fake_streaming_provider, session_store=non_stream_store).run_turn(
        _turn(text)
    )
    stream_store = _FakeSessionStore()
    list(
        AgentKernel(provider=fake_streaming_provider, session_store=stream_store).run_turn_stream(
            _turn(text)
        )
    )

    def _assistant(store):
        saved = [c for sid, role, c in store.messages if role == "assistant"][0]
        # Trace ids differ per run; compare the content before the trace line.
        return saved.rsplit("\nTrace:", 1)[0]

    assert _assistant(stream_store) == _assistant(non_stream_store)


def test_stream_interruption_saves_partial_with_marker():
    store = _FakeSessionStore()
    kernel = AgentKernel(provider=_BrokenStreamProvider(), session_store=store)
    chunks = list(kernel.run_turn_stream(_turn("go")))
    assert chunks[-1].done is True
    saved = [c for sid, role, c in store.messages if role == "assistant"][0]
    assert "partial " in saved
    assert "stream-interrupted" in saved


def test_stream_chunks_round_trip_utf8_chinese_text(fake_streaming_provider):
    chinese = json.loads(FIXTURE.read_text(encoding="utf-8"))["chinese"]
    request = _request(chinese)
    chunks = list(iter_stream(fake_streaming_provider, request))
    assert aggregate_text(chunks) == fake_streaming_provider.generate(request).text
    # Chinese content survives the round trip unaltered.
    assert chinese in aggregate_text(chunks)
