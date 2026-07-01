"""Shared slash-command registry for chat surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..agent.permissions import PERMISSION_LEVELS


_PERMISSION_ORDER = {name: index for index, name in enumerate(PERMISSION_LEVELS)}


@dataclass(frozen=True)
class SlashCommandContext:
    permission_ceiling: str = "read_only"
    mode: str = "general_chat"
    project_slug: str | None = None


@dataclass(frozen=True)
class SlashCommandSpec:
    name: str
    action_type: str
    help: str
    required_permission: str = "read_only"
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class SlashCommandAction:
    name: str
    action_type: str
    status: str
    args: dict[str, str] = field(default_factory=dict)
    message: str = ""
    required_permission: str = "read_only"

    def to_dict(self) -> dict:
        return asdict(self)


class SlashCommandRegistry:
    """Resolve slash commands into typed surface actions."""

    def __init__(self, commands: list[SlashCommandSpec] | None = None) -> None:
        self._commands = {command.name: command for command in commands or _default_commands()}
        self._aliases = {
            alias: command.name
            for command in self._commands.values()
            for alias in command.aliases
        }

    @classmethod
    def default(cls) -> "SlashCommandRegistry":
        return cls()

    def resolve(self, text: str, context: SlashCommandContext) -> SlashCommandAction | None:
        stripped = text.strip()
        if not stripped.startswith("/"):
            return None
        command_token, _, argument = stripped[1:].partition(" ")
        name = self._aliases.get(command_token, command_token)
        spec = self._commands.get(name)
        if spec is None:
            return SlashCommandAction(
                name=command_token,
                action_type="error",
                status="error",
                message=f"Unknown slash command: /{command_token}. Use /help.",
            )
        if not self._allowed(context.permission_ceiling, spec.required_permission):
            return SlashCommandAction(
                name=spec.name,
                action_type=spec.action_type,
                status="denied",
                message=f"/{spec.name} requires {spec.required_permission}; session has {context.permission_ceiling}.",
                required_permission=spec.required_permission,
            )
        if spec.name == "help":
            return SlashCommandAction(
                name=spec.name,
                action_type=spec.action_type,
                status="ok",
                message=self.render_help(),
                required_permission=spec.required_permission,
            )
        return SlashCommandAction(
            name=spec.name,
            action_type=spec.action_type,
            status="ok",
            args={"value": argument.strip()} if argument.strip() else {},
            message=spec.help,
            required_permission=spec.required_permission,
        )

    def render_help(self) -> str:
        lines = ["Slash Commands"]
        for command in self._commands.values():
            aliases = f" (aliases: {', '.join('/' + alias for alias in command.aliases)})" if command.aliases else ""
            lines.append(f"/{command.name}{aliases} - {command.help}")
        return "\n".join(lines)

    @staticmethod
    def _allowed(ceiling: str, required: str) -> bool:
        return _PERMISSION_ORDER.get(ceiling, -1) >= _PERMISSION_ORDER.get(required, 0)


def _default_commands() -> list[SlashCommandSpec]:
    return [
        SlashCommandSpec("new", "new_session", "Start a new chat session."),
        SlashCommandSpec("reset", "reset_session", "Reset the current session draft state.", required_permission="draft_write"),
        SlashCommandSpec("retry", "retry_turn", "Retry the last assistant turn.", required_permission="draft_write"),
        SlashCommandSpec("undo", "undo_turn", "Soft-delete the last turn.", required_permission="draft_write"),
        SlashCommandSpec("compress", "compress_session", "Summarize earlier context.", required_permission="draft_write"),
        SlashCommandSpec("usage", "show_usage", "Show local usage statistics."),
        SlashCommandSpec("model", "switch_model", "Switch model for this surface."),
        SlashCommandSpec("mode", "switch_mode", "Switch conversation mode."),
        SlashCommandSpec("project", "switch_project", "Switch project binding."),
        SlashCommandSpec("skills", "list_skills", "List available local skills."),
        SlashCommandSpec("resume", "resume_session", "Resume a session by id."),
        SlashCommandSpec("help", "show_help", "Show slash command help.", aliases=("h", "?")),
    ]


__all__ = [
    "SlashCommandAction",
    "SlashCommandContext",
    "SlashCommandRegistry",
    "SlashCommandSpec",
]
