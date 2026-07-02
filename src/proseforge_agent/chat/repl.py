"""stdin/stdout chat REPL."""

from __future__ import annotations

from .. import _bootstrap  # noqa: F401  # UTF-8 + path hardening, must run early

import sys
from typing import TextIO

from ..agent import AgentKernel, AgentTurnRequest, IntentRouter
from .session import ChatSessionStore
from .slash import SlashCommandContext, SlashCommandRegistry


class ChatRepl:
    """Small command-loop wrapper around the injected Agent Kernel."""

    def __init__(
        self,
        *,
        provider,
        session_store: ChatSessionStore,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
        mode: str = "general_chat",
        project_slug: str | None = None,
        permission_level: str = "read_only",
        session_id: str = "cli",
        stream: bool = False,
    ) -> None:
        self.provider = provider
        self.session_store = session_store
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout
        self.mode = mode
        self.project_slug = project_slug
        self.permission_level = permission_level
        self.session_id = session_id
        self.stream = stream
        self.slash_registry = SlashCommandRegistry.default()
        self.kernel = AgentKernel(
            provider=provider,
            session_store=session_store,
            intent_router=IntentRouter(),
        )

    def run(self) -> int:
        """Run until /exit or EOF."""
        self.session_store.ensure_session(self.session_id, self.mode, self.project_slug)
        self._write("Chat REPL")
        for raw_line in self.input_stream:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("/"):
                should_exit = self._handle_command(line)
                if should_exit:
                    return 0
                continue
            request = AgentTurnRequest(
                session_id=self.session_id,
                text=line,
                mode=self.mode,
                project_slug=self.project_slug,
                permission_level=self.permission_level,
            )
            if self.stream:
                self._write_stream(self.kernel.run_turn_stream(request))
            else:
                result = self.kernel.run_turn(request)
                self._write(result.text)
        return 0

    def _write_stream(self, chunks) -> None:
        """Print stream chunks incrementally, then a terminating newline."""
        wrote_any = False
        for chunk in chunks:
            print(chunk.text, end="", file=self.output_stream, flush=True)
            wrote_any = True
        if wrote_any:
            print("", file=self.output_stream, flush=True)

    def _handle_command(self, line: str) -> bool:
        action = self.slash_registry.resolve(
            line,
            SlashCommandContext(
                permission_ceiling=self.permission_level,
                mode=self.mode,
                project_slug=self.project_slug,
            ),
        )
        command, _, argument = line.partition(" ")
        argument = argument.strip()
        if command == "/exit":
            return True
        if command == "/help":
            self._write(action.message if action else self.slash_registry.render_help())
            return False
        if command == "/mode":
            if argument:
                self.mode = argument
            self._write(f"mode: {self.mode}")
            return False
        if command == "/project":
            if argument:
                self.project_slug = None if argument == "none" else argument
            self._write(f"project: {self.project_slug or '(none)'}")
            return False
        if command == "/sessions":
            self._write("Sessions")
            for session in self.session_store.list(project_slug=self.project_slug):
                suffix = f" ({session.project_slug})" if session.project_slug else ""
                self._write(f"- {session.id} -> {session.mode}{suffix}")
            return False
        if command == "/undo":
            result = self.session_store.rewind(self.session_id, reason="undo")
            self._write(f"undo: soft_deleted_steps={result.soft_deleted_steps}")
            return False
        if command == "/retry":
            result = self.session_store.retry(self.session_id)
            self._write(f"retry: source_step={result.source_step or '(none)'}")
            return False
        if command == "/compress":
            result = self.session_store.compress(self.session_id)
            self._write(f"compress: source_steps={result.source_steps}")
            return False
        if command == "/usage":
            usage = self.session_store.usage(self.session_id)
            self._write(f"usage: messages={usage.message_count} words={usage.word_count}")
            return False
        if command == "/resume":
            if argument:
                session = self.session_store.resume(argument)
                self.session_id = session.id
                self.mode = session.mode
                self.project_slug = session.project_slug
            self._write(f"session: {self.session_id}")
            return False
        self._write(action.message if action else f"unknown command: {command}")
        return False

    def _write(self, text: str) -> None:
        print(text, file=self.output_stream)


def run_repl(
    argv: list[str] | None = None,
    *,
    provider: str = "fake",
    root: str = ".pf-agent",
    mode: str = "general_chat",
    project_slug: str | None = None,
    stream: bool = False,
) -> int:
    """Programmatic entry point for the interactive chat REPL.

    Builds a fake-provider-backed REPL over a durable session store and runs
    it until ``/exit`` or EOF. This is the callable the bare ``pf-agent``
    command dispatches to when the workspace is already configured.
    """
    from pathlib import Path

    from ..llm import FakeProvider
    from .session import ChatSessionStore

    fake = FakeProvider(name=provider or "fake", model=provider or "fake")
    session_store = ChatSessionStore(Path(root))
    repl = ChatRepl(
        provider=fake,
        session_store=session_store,
        mode=mode,
        project_slug=project_slug,
        stream=stream,
    )
    return repl.run()


def main(argv: list[str] | None = None) -> int:
    """``python -m proseforge_agent.chat.repl`` entry point."""
    return run_repl(argv)


__all__ = ["ChatRepl", "run_repl", "main"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
