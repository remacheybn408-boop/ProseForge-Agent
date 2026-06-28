"""Shell completion rendering and install planning."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import ConfigurationError


_SCRIPTS = {
    "powershell": (
        "profile.d/proseforge-agent.ps1",
        "Register-ArgumentCompleter -Native -CommandName pf-agent -ScriptBlock { param($wordToComplete) 'init','doctor','provider','chat' | Where-Object { $_ -like \"$wordToComplete*\" } }\n",
    ),
    "bash": ("bash_completion.d/pf-agent", 'complete -W "init doctor provider chat" pf-agent\n'),
    "zsh": ("zsh/site-functions/_pf-agent", "#compdef pf-agent\n_arguments '1:command:(init doctor provider chat)'\n"),
    "fish": ("fish/completions/pf-agent.fish", "complete -c pf-agent -f -a 'init doctor provider chat'\n"),
}


@dataclass(frozen=True)
class CompletionScript:
    """Rendered shell completion script."""

    shell: str
    script_text: str
    install_target: str
    install_action: str = "system_write"


@dataclass(frozen=True)
class InstallPlan:
    """A read-only plan for installing/removing managed shell snippets."""

    shell: str
    action: str
    script: CompletionScript
    permission: str = "system_write"
    managed_marker: str = "# BEGIN PROSEFORGE AGENT COMPLETION"


class ShellCompletionRenderer:
    """Render completion snippets for supported shells."""

    def render(self, shell: str) -> CompletionScript:
        normalized = shell.lower()
        if normalized not in _SCRIPTS:
            raise ConfigurationError(f"unknown shell {shell!r}")
        target, text = _SCRIPTS[normalized]
        return CompletionScript(shell=normalized, script_text=text, install_target=target)


class ShellInstaller:
    """Plan shell completion install/uninstall actions without mutating profiles."""

    def __init__(self, platform_io=None) -> None:
        self.platform_io = platform_io

    def plan(self, shell: str, install: bool) -> InstallPlan:
        script = ShellCompletionRenderer().render(shell)
        return InstallPlan(shell=script.shell, action="install" if install else "remove", script=script)


__all__ = ["CompletionScript", "InstallPlan", "ShellCompletionRenderer", "ShellInstaller"]
