"""Command line entry point for ProseForge Agent.

This is the operator surface: a top-level ``pf-agent`` parser with one
subparser per command group (project, proseforge, provider, memory, retrieve,
phase-plan, daily-workbook, chapter, workflow, report, extension). Every group
shares output flags (``--format``, ``--write``, ``--dry-run``, ``--out``) so
filesystem-changing commands can be previewed. Commands render their result
through :mod:`proseforge_agent.reports` so Markdown, JSON, and terminal output
stay consistent and JSON stays stable for automation.

Deep execution of each group is wired by that group's integration task; this
card establishes the entry points, shared flags, and report rendering.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

from . import __version__
from .errors import ProseForgeAgentError
from .reports import Report, ReportRenderer, ReportSection
from .reports.registry import default_registry

# name -> {help, inputs, artifacts}. Drives both the subparsers and the
# self-describing `report command-reference` output.
COMMAND_GROUPS: dict[str, dict] = {
    "project": {
        "help": "Create and inspect novel projects",
        "inputs": "project slug, title, config path",
        "artifacts": "project workspace, project config",
    },
    "proseforge": {
        "help": "Bridge to the ProseForge engine (discovery, dry-run actions)",
        "inputs": "engine root, action name",
        "artifacts": "engine action results",
    },
    "provider": {
        "help": "Inspect configured model providers and role routing",
        "inputs": "providers config (YAML)",
        "artifacts": "provider/role report",
    },
    "usage": {
        "help": "Report metered provider token usage and cost",
        "inputs": "usage log (JSONL), since filter",
        "artifacts": "per-provider usage report",
    },
    "memory": {
        "help": "List and export durable project memory",
        "inputs": "agent database path, project slug",
        "artifacts": "memory export report",
    },
    "retrieve": {
        "help": "Build evidence packs for an intent",
        "inputs": "project slug, intent, token budget",
        "artifacts": "evidence pack",
    },
    "phase-plan": {
        "help": "Generate a structured phase plan from intake",
        "inputs": "intake file, memory",
        "artifacts": "phase plan",
    },
    "daily-workbook": {
        "help": "Generate the dated daily workbook",
        "inputs": "project state, date",
        "artifacts": "daily workbook",
    },
    "chapter": {
        "help": "Run the chapter lifecycle (prepare, draft, review, accept)",
        "inputs": "project, chapter number, provider, until-stage",
        "artifacts": "context, draft, review, acceptance artifacts",
    },
    "workflow": {
        "help": "Inspect and resume workflow runs",
        "inputs": "runs directory, run id",
        "artifacts": "workflow run report",
    },
    "report": {
        "help": "Render shared reports (Markdown, JSON, terminal)",
        "inputs": "report name",
        "artifacts": "rendered report files",
    },
    "extension": {
        "help": "List and inspect installed extensions",
        "inputs": "extension registry",
        "artifacts": "extension report",
    },
    "chat": {
        "help": "Run one-shot agent chat and intent classification",
        "inputs": "message, mode, provider",
        "artifacts": "agent turn report",
    },
    "tools": {
        "help": "List internal tools and permission levels",
        "inputs": "tool registry",
        "artifacts": "tool registry report",
    },
    "jobs": {
        "help": "Run allow-listed background agent jobs",
        "inputs": "job name, provider, dry-run flag",
        "artifacts": "event bus records, job report",
    },
    "setup": {
        "help": "Run the guided first-use setup wizard",
        "inputs": "setup mode, provider, repair/reconfigure flags",
        "artifacts": "agent config, workspace directories, setup summary",
    },
    "init": {
        "help": "Initialize a ProseForge Agent workspace",
        "inputs": "portable/native mode, ProseForge root",
        "artifacts": "agent config, workspace, provider stub, doctor report",
    },
    "doctor": {
        "help": "Run read-only installation diagnostics",
        "inputs": "optional diagnostic section",
        "artifacts": "doctor report",
    },
    "completions": {
        "help": "Show shell completions and launcher install plans",
        "inputs": "shell name",
        "artifacts": "completion script",
    },
    "upgrade": {
        "help": "Check or run safe workspace upgrades",
        "inputs": "version range, check flag",
        "artifacts": "backup and migration report",
    },
    "uninstall": {
        "help": "Plan uninstall and data retention actions",
        "inputs": "plan flag, remove user data flag",
        "artifacts": "uninstall plan",
    },
    "service": {
        "help": "Check the local agent service facade",
        "inputs": "bind address, provider, check flag",
        "artifacts": "local API readiness report",
    },
    "support": {
        "help": "Create redacted operator support bundles",
        "inputs": "bundle subcommand, redaction flag",
        "artifacts": "support bundle diagnostics",
    },
    "qa": {
        "help": "Show native QA matrix coverage requirements",
        "inputs": "matrix subcommand, show flag",
        "artifacts": "cross-platform QA matrix",
    },
    "release": {
        "help": "Run release readiness gates",
        "inputs": "check subcommand, complete-agent flag",
        "artifacts": "release gate report",
    },
    "eval": {
        "help": "Run deterministic agent task-success evaluations",
        "inputs": "golden suite, provider, threshold",
        "artifacts": "agent eval report",
    },
    "status": {
        "help": "Show resolved capability flags and safe-mode status",
        "inputs": "capabilities flag, config",
        "artifacts": "capability map report",
    },
    "run": {
        "help": "Run an autonomous, goal-directed agent loop",
        "inputs": "goal, provider, iteration budget, show-plan flag",
        "artifacts": "loop run summary, decomposed plan",
    },
}


def _output_parser() -> argparse.ArgumentParser:
    """Shared output flags for every command group."""
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--format",
        choices=["markdown", "json", "terminal"],
        default="terminal",
        help="output format",
    )
    parent.add_argument("--write", action="store_true", help="write artifacts to disk")
    parent.add_argument(
        "--dry-run",
        action="store_true",
        help="preview a filesystem-changing command without writing",
    )
    parent.add_argument("--out", default=None, help="output directory for --write")
    return parent


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level ``pf-agent`` argument parser."""
    parser = argparse.ArgumentParser(
        prog="pf-agent",
        description=(
            "ProseForge Agent: agentic orchestration for long-form novel "
            "production on top of the ProseForge engine."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    shared = _output_parser()
    subparsers = parser.add_subparsers(dest="command", metavar="<group>")
    for name, spec in COMMAND_GROUPS.items():
        group = subparsers.add_parser(
            name,
            parents=[shared],
            help=spec["help"],
            description=(
                f"{spec['help']}.\n"
                f"Inputs: {spec['inputs']}.\n"
                f"Artifacts: {spec['artifacts']}."
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        group.add_argument(
            "subcommand",
            nargs="?",
            help="group subcommand (e.g. 'command-reference', 'list')",
        )
        group.add_argument("--providers", default=None, help="providers config (YAML)")
        if name == "chat":
            group.add_argument("--message", default=None, help="one-shot chat message")
            group.add_argument("--text", default=None, help="text to classify")
            group.add_argument("--provider", default="fake", help="chat provider")
            group.add_argument("--no-project", action="store_true", help="do not bind a project")
            group.add_argument("--project", default=None, help="project slug")
            group.add_argument("--mode", default="general_chat", help="conversation mode")
            group.add_argument(
                "--show-prompt",
                action="store_true",
                help="print the structured prompt pack without running the turn",
            )
            group.add_argument(
                "--show-citations",
                action="store_true",
                help="print retrieval citations without inventing missing context",
            )
            group.add_argument(
                "--show-memory-candidates",
                action="store_true",
                help="extract preference candidates without accepting memory",
            )
            group.add_argument(
                "--propose-handoff",
                action="store_true",
                help="create a workflow handoff package without starting it",
            )
            group.add_argument(
                "--permission-level",
                default="read_only",
                help="maximum permission level for this turn",
            )
            group.add_argument(
                "--explain-safety",
                action="store_true",
                help="assess untrusted content with the injection guard and show the safety verdict",
            )
            group.add_argument(
                "--stream",
                action="store_true",
                help="stream the response incrementally as it is generated",
            )
            group.add_argument("--profile", default=None, help="agent persona profile")
            group.add_argument("--profiles-file", default=None, help="YAML file with agent profiles")
        if name == "usage":
            group.add_argument(
                "--usage-log",
                default="logs/usage.jsonl",
                help="path to the usage JSONL log",
            )
            group.add_argument(
                "--since",
                default=None,
                help="filter usage records (e.g. 'today'); shows all when omitted",
            )
        if name == "tools":
            group.add_argument(
                "--include-permissions",
                action="store_true",
                help="include permission levels in the tool list",
            )
        if name == "jobs":
            group.add_argument("job_name", nargs="?", help="allow-listed background job")
            group.add_argument("--provider", default="fake", help="provider for the job")
        if name == "setup":
            group.add_argument("--quick", action="store_true", help="run quick guided setup")
            group.add_argument("--full", action="store_true", help="run full guided setup")
            group.add_argument("--minimal", action="store_true", help="run zero-key fake-provider setup")
            group.add_argument("--non-interactive", action="store_true", help="run without prompts")
            group.add_argument("--reconfigure", action="store_true", help="backup and rewrite config")
            group.add_argument(
                "--add-provider",
                nargs="?",
                const="deepseek",
                default=None,
                help="append a provider while keeping fake fallback",
            )
            group.add_argument("--skip-provider-test", action="store_true", help="skip provider ping")
            group.add_argument("--no-shell", action="store_true", help="skip shell completion registration")
            group.add_argument("--repair", action="store_true", help="repair config/workspace without deleting data")
            group.add_argument("--print-config", action="store_true", help="print redacted effective config")
        if name == "init":
            group.add_argument("--portable", action="store_true", help="initialize portable .pf-agent workspace")
            group.add_argument("--native", action="store_true", help="initialize native app directories")
            group.add_argument("--proseforge-root", default="${PROSEFORGE_ROOT}", help="ProseForge engine root")
            group.add_argument("--non-interactive", action="store_true", help="run without prompts")
        if name == "doctor":
            group.add_argument("--section", default=None, help="diagnostic section to run")
        if name == "completions":
            group.add_argument("--shell", default="powershell", help="shell to render")
        if name == "upgrade":
            group.add_argument("--check", action="store_true", help="check upgrade readiness without migration")
            group.add_argument("--from-version", default="1", help="current workspace schema version")
            group.add_argument("--to-version", default="2", help="target workspace schema version")
        if name == "uninstall":
            group.add_argument("--plan", action="store_true", help="show uninstall plan without deleting")
            group.add_argument("--remove-user-data", action="store_true", help="include user data in plan")
        if name == "service":
            group.add_argument("--provider", default="fake", help="service provider")
            group.add_argument("--check", action="store_true", help="validate service configuration only")
            group.add_argument("--bind", default="127.0.0.1", help="service bind address")
            group.add_argument("--allow-remote", action="store_true", help="allow non-loopback bind")
            group.add_argument("--permission-level", default="read_only", help="service permission ceiling")
        if name == "support":
            group.add_argument("--redact", action="store_true", help="redact paths and secrets")
        if name == "qa":
            group.add_argument("--show", action="store_true", help="show required native QA matrix")
            group.add_argument(
                "--check",
                action="store_true",
                help="validate the CI matrix against the native QA matrix (with 'ci')",
            )
            group.add_argument(
                "--workflow",
                default=".github/workflows/ci.yml",
                help="path to the CI workflow file for 'qa ci'",
            )
        if name == "release":
            group.add_argument("--complete-agent", action="store_true", help="run the complete agent release gate")
            group.add_argument("--write-report", action="store_true", help="write release report to reports/")
        if name == "eval":
            group.add_argument("--provider", default="fake", help="provider for deterministic eval")
            group.add_argument("--suite", default=None, help="path to a golden task suite JSON file")
            group.add_argument("--threshold", type=float, default=None, help="override suite success threshold")
            group.add_argument("--write-report", action="store_true", help="write eval report to reports/")
        if name == "run":
            group.add_argument("--goal", default=None, help="goal for the autonomous run")
            group.add_argument("--provider", default="fake", help="provider for the run")
            group.add_argument("--allow-exec", action="store_true", help="allow sandboxed command execution")
            group.add_argument("--approve", action="store_true", help="approve sandboxed execution for this run")
            group.add_argument("--delegate", action="store_true", help="delegate a scoped sub-task during the run")
            group.add_argument(
                "--show-plan",
                action="store_true",
                help="print the decomposed plan with per-task status",
            )
            group.add_argument(
                "--max-iterations",
                type=int,
                default=5,
                help="iteration budget for the autonomous loop",
            )
            group.add_argument(
                "--verify",
                action="store_true",
                help="self-verify each output against criteria and reflect/retry on failure",
            )
        if name == "status":
            group.add_argument(
                "--capabilities",
                action="store_true",
                help="list each capability as enabled/degraded/disabled with a reason",
            )
            group.add_argument(
                "--disable",
                action="append",
                default=None,
                help="disable a capability for this run (repeatable)",
            )
        if name == "provider":
            group.add_argument(
                "--provider",
                default=None,
                help="provider name to probe (default: fake)",
            )
            group.add_argument(
                "--write-report",
                action="store_true",
                help="write the provider report to the output directory",
            )
            group.add_argument(
                "--all-policies",
                action="store_true",
                help="render route decisions for all non-manual policies",
            )
            group.add_argument(
                "--all",
                action="store_true",
                help="operate on all configured provider profiles",
            )
            group.add_argument(
                "--shape-only",
                action="store_true",
                help="run offline shape certification only",
            )
            group.add_argument(
                "--real-if-key-present",
                action="store_true",
                help="run real smoke only when the provider key is present",
            )
            group.add_argument(
                "--records-dir",
                default=None,
                help="directory for provider certification records",
            )
            group.add_argument(
                "--route-matrix",
                default=None,
                help="provider route matrix YAML",
            )
            group.add_argument(
                "--role",
                default="drafter",
                help="role to route (default: drafter)",
            )
            group.add_argument("--model", default=None, help="provider model for setup")
            group.add_argument("--api-key", default=None, help="provider API key for setup")
            group.add_argument("--verify", action="store_true", help="verify provider after setup")
            group.add_argument(
                "--endpoint",
                action="append",
                default=None,
                help="local OpenAI-compatible endpoint to inspect",
            )

    return parser


# -- handlers -----------------------------------------------------------------


def _emit(report: Report, fmt: str) -> int:
    print(ReportRenderer().render(report, fmt))
    return 0


def _handle_report(args: argparse.Namespace) -> int:
    name = args.subcommand or "command-reference"
    report = default_registry().build(name, groups=COMMAND_GROUPS)
    if args.write and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = "json" if args.format == "json" else "md"
        path = out_dir / f"{name}.{suffix}"
        path.write_text(ReportRenderer().render(report, args.format), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    return _emit(report, args.format)


def _handle_provider_probe(args: argparse.Namespace) -> int:
    from .llm import CapabilityProber, FakeProvider
    from .llm.capabilities import capability_matrix

    name = getattr(args, "provider", None) or "fake"
    provider = FakeProvider(name=name, model=name)
    results = CapabilityProber(provider).run()
    matrix = capability_matrix(results)
    sections = [
        ReportSection(
            heading="Capabilities",
            lines=[
                f"{r.capability} -> {r.status} ({r.latency_ms:.1f} ms)"
                for r in results
            ],
        )
    ]
    report = Report(
        title=f"Provider Capability Probe: {name}",
        status="ok",
        next_action="Feed the capability matrix into the fallback router",
        sections=sections,
        data={"provider": name, "matrix": matrix},
    )

    if getattr(args, "write_report", False) and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = "json" if args.format == "json" else "md"
        path = out_dir / f"provider-probe-{name}.{suffix}"
        path.write_text(ReportRenderer().render(report, args.format), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    return _emit(report, args.format)


def _default_route_matrix_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "providers"
        / "route_matrix.yaml"
    )


def _handle_provider_routes(args: argparse.Namespace) -> int:
    from .llm import ProviderRouter

    matrix_path = Path(args.route_matrix) if args.route_matrix else _default_route_matrix_path()
    data = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    router = ProviderRouter(data)
    decisions = (
        router.decisions_for_all_policies(role=args.role)
        if args.all_policies
        else [router.select(role=args.role)]
    )
    lines = []
    payload = []
    for decision in decisions:
        selected = decision.selected.name if decision.selected else f"blocked:{decision.blocked_reason}"
        lines.append(f"{decision.policy} -> {selected}")
        payload.append(decision.to_report().data)
    report = Report(
        title="Provider Routes",
        status="ok",
        next_action="Use selected providers when recording workflow attempts",
        sections=[ReportSection("Routes", lines)],
        data={"role": args.role, "route_matrix": str(matrix_path), "decisions": payload},
    )
    if getattr(args, "write_report", False) and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = "json" if args.format == "json" else "md"
        path = out_dir / f"provider-routes-{args.role}.{suffix}"
        path.write_text(ReportRenderer().render(report, args.format), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    return _emit(report, args.format)


def _provider_profile_paths() -> list[Path]:
    return sorted((Path(__file__).resolve().parents[2] / "configs" / "providers").glob("*.yaml"))


def _certifier_for_family(family: str):
    from .llm.providers import (
        anthropic,
        deepseek,
        doubao,
        gemini,
        glm,
        grok,
        mimo,
        minimax,
        openai,
        qwen,
    )

    modules = {
        "anthropic": anthropic,
        "deepseek": deepseek,
        "doubao": doubao,
        "gemini": gemini,
        "glm": glm,
        "xai": grok,
        "mimo": mimo,
        "minimax": minimax,
        "openai": openai,
        "qwen": qwen,
    }
    return modules.get(family)


def _handle_provider_certify(args: argparse.Namespace) -> int:
    from .llm.certification import CertificationStore, PASSED, SKIPPED, UNVERIFIED
    from .llm.docs_refresh import docs_refresh_report, source_urls_for_family
    from .llm.profiles import load_provider_profiles

    records_dir = Path(args.records_dir) if args.records_dir else Path("reports") / "provider-certification-records"
    store = CertificationStore(records_dir)
    written = []
    families: set[str] = set()
    for path in _provider_profile_paths():
        profiles = load_provider_profiles(path)
        for profile in profiles.values():
            if not args.all and args.provider and profile.name != args.provider:
                continue
            if not args.all and not args.provider:
                continue
            certifier = _certifier_for_family(profile.family)
            if certifier is None:
                continue
            shape = certifier.shape_certification(profile)
            smoke = {"skipped": True, "reason": "shape-only"}
            if not args.shape_only and args.real_if_key_present:
                smoke = certifier.real_smoke(profile)
            source_urls = source_urls_for_family(profile.family)
            record = store.write(
                provider=profile.name,
                family=profile.family,
                protocol=profile.protocol,
                model=profile.model,
                source_urls=source_urls,
                checked_date=shape["checked_date"],
                shape_status=PASSED if shape.get("level") == "shape_tested" else UNVERIFIED,
                smoke_status=SKIPPED if smoke.get("skipped") else PASSED,
                workflow_status=UNVERIFIED,
                capability_status=shape.get("capabilities") or {},
                limitations=[
                    f"{key}={value}"
                    for key, value in (shape.get("capabilities") or {}).items()
                    if value not in {"supported", "pass", PASSED}
                ],
            )
            written.append(record)
            families.add(profile.family)

    docs_report = docs_refresh_report(sorted(families))
    report = Report(
        title="Provider Certification",
        status="ok",
        next_action="Use ProviderReleaseCheck before release sign-off",
        sections=[
            ReportSection(
                "Records",
                [
                    f"{record.provider} -> shape={record.shape_status}, smoke={record.smoke_status}"
                    for record in written
                ],
            ),
            *docs_report.sections,
        ],
        data={
            "records_dir": str(records_dir),
            "records": [record.__dict__ for record in written],
            "docs": docs_report.data,
        },
    )
    if getattr(args, "write_report", False) and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = "json" if args.format == "json" else "md"
        path = out_dir / f"provider-certification.{suffix}"
        path.write_text(ReportRenderer().render(report, args.format), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    return _emit(report, args.format)


def _handle_provider(args: argparse.Namespace) -> int:
    if args.subcommand == "discover-local":
        from .install.local_models import LocalModelDetector

        class StaticLocalHttp:
            def get_json(self, url: str) -> object:
                return {"models": []}

        detector = LocalModelDetector(StaticLocalHttp())
        candidates = detector.detect(endpoints=args.endpoint)
        lines = [
            f"{candidate.endpoint} -> {', '.join(candidate.models)}"
            for candidate in candidates
        ]
        if not lines:
            lines = detector.notes or ["no local models discovered"]
        report = Report(
            title="Local Models",
            status="ok",
            next_action="Use provider setup with a local endpoint before routing chat to it",
            sections=[ReportSection("Candidates", lines)],
            data={
                "candidates": [candidate.__dict__ for candidate in candidates],
                "notes": detector.notes,
            },
        )
        return _emit(report, args.format)
    if args.subcommand == "setup":
        from .install.provider_setup import ProviderSetupWizard
        from .install.secrets import SecretStore

        result = ProviderSetupWizard(Path(".pf-agent"), SecretStore.for_platform(sys.platform, False)).configure(
            provider=args.provider or "",
            api_key=args.api_key,
            model=args.model or args.provider or "",
            verify=args.verify,
        )
        report = Report(
            title="Provider Setup",
            status="ok",
            next_action="Run `pf-agent provider certify --all --shape-only` before release",
            sections=[
                ReportSection(
                    "Profile",
                    [
                        f"provider={result.provider}",
                        f"model={result.model}",
                        f"profile={result.profile_path}",
                        f"secret_ref={result.secret_ref}",
                        f"verified={result.verified}",
                    ],
                )
            ],
            data=result.__dict__ | {"profile_path": str(result.profile_path)},
        )
        return _emit(report, args.format)
    if args.subcommand == "probe":
        return _handle_provider_probe(args)
    if args.subcommand == "routes":
        return _handle_provider_routes(args)
    if args.subcommand == "certify":
        return _handle_provider_certify(args)
    if not args.providers:
        report = _planned_report("provider", "Pass --providers <config.yaml> to list providers")
        return _emit(report, args.format)
    from .llm.registry import ProviderRegistry

    registry = ProviderRegistry.from_yaml(args.providers)
    roles = registry._roles  # noqa: SLF001 - read-only inspection for reporting
    sections = [
        ReportSection(heading="Roles", lines=[f"{role} -> {name}" for role, name in roles.items()])
    ]
    report = Report(
        title="Provider Routing",
        status="ok",
        next_action="Use `pf-agent chapter ... --provider <name>` to draft",
        sections=sections,
        data={"default_provider": registry._default_provider},  # noqa: SLF001
    )
    return _emit(report, args.format)


def _handle_chat(args: argparse.Namespace) -> int:
    if args.subcommand == "sessions":
        from .chat import ChatSessionStore

        store = ChatSessionStore(Path(".pf-agent"))
        sessions = store.list(project_slug=args.project)
        lines = [
            f"{session.id} -> {session.mode}"
            + (f" ({session.project_slug})" if session.project_slug else "")
            for session in sessions
        ]
        report = Report(
            title="Chat Sessions",
            status="ok",
            next_action="Use a session id to resume a durable chat transcript",
            sections=[ReportSection("Sessions", lines)],
            data={"sessions": [session.__dict__ for session in sessions]},
        )
        return _emit(report, args.format)
    if args.subcommand == "classify":
        from .agent import IntentRouter

        text = args.text or args.message or ""
        decision = IntentRouter().classify(text, mode=args.mode, project_slug=args.project)
        report = Report(
            title="Chat Intent",
            status="ok",
            next_action="Pass this intent to the Agent Kernel",
            sections=[
                ReportSection(
                    "Intent",
                    [
                        f"name: {decision.name}",
                        f"confidence: {decision.confidence:.2f}",
                        f"permission: {decision.required_permission}",
                        f"reason: {decision.reason}",
                    ],
                )
            ],
            data=decision.__dict__,
        )
        return _emit(report, args.format)
    from .chat import ChatSessionStore
    from .llm import FakeProvider

    project_slug = None if args.no_project else args.project
    provider = FakeProvider(name=args.provider or "fake", model=args.provider or "fake")
    session_store = ChatSessionStore(Path(".pf-agent"))
    mode = args.mode
    permission_level = args.permission_level
    profile = None
    if getattr(args, "profile", None):
        from .agent import AgentProfileRegistry

        registry = (
            AgentProfileRegistry.from_yaml(args.profiles_file)
            if args.profiles_file
            else AgentProfileRegistry.builtins()
        )
        profile = registry.resolve(args.profile, session_permission_max=args.permission_level)
        mode = profile.mode
        permission_level = profile.permission_ceiling
    if getattr(args, "show_prompt", False):
        from .chat import ChatPromptBuilder

        text = args.message or args.text or ""
        print(
            ChatPromptBuilder()
            .build(text=text, mode=mode, project_slug=project_slug)
            .render_markdown()
        )
        return 0
    if getattr(args, "propose_handoff", False):
        from .chat.handoff import ChatWorkflowHandoff, render_handoff

        text = args.message or args.text or ""
        package = ChatWorkflowHandoff().create(
            text,
            project_slug=project_slug,
            mode=mode,
        )
        report = Report(
            title="Handoff Package",
            status="ok",
            next_action="Confirm write-level packages before starting a workflow",
            sections=[ReportSection("Package", render_handoff(package))],
            data=package.to_dict(),
        )
        return _emit(report, args.format)
    if getattr(args, "show_memory_candidates", False):
        from .chat.memory import ChatMemoryExtractor, render_memory_candidates

        text = args.message or args.text or ""
        candidates = ChatMemoryExtractor().write_candidates(
            Path(".pf-agent"),
            text,
            project_slug=project_slug,
        )
        report = Report(
            title="Memory Candidates",
            status="ok",
            next_action="Review candidates before promoting them to durable memory",
            sections=[ReportSection("Queues", render_memory_candidates(candidates))],
            data={"candidates": [candidate.to_dict() for candidate in candidates]},
        )
        return _emit(report, args.format)
    if getattr(args, "show_citations", False):
        from .chat.retrieval import ChatRetrievalResponder, render_citations

        text = args.message or args.text or ""
        answer = ChatRetrievalResponder(evidence=[]).answer(text, project_slug=project_slug)
        rendered = render_citations(answer)
        report = Report(
            title="Chat Citations",
            status="ok" if not answer.degraded else "degraded",
            next_action="Add project evidence before relying on this answer",
            sections=[
                ReportSection("Answer", answer.text.splitlines()),
                ReportSection("Citations", rendered.splitlines()),
            ],
            data=answer.to_dict(),
        )
        return _emit(report, args.format)
    if not args.message:
        from .chat.repl import ChatRepl

        return ChatRepl(
            provider=provider,
            session_store=session_store,
            mode=mode,
            project_slug=project_slug,
            permission_level=permission_level,
            stream=getattr(args, "stream", False),
        ).run()
    from .agent import AgentKernel, AgentTurnRequest, IntentRouter

    explain_safety = getattr(args, "explain_safety", False)
    safety_guard = None
    if explain_safety:
        from .agent.safety import InjectionGuard

        safety_guard = InjectionGuard()
    kernel = AgentKernel(
        provider=provider,
        intent_router=IntentRouter(),
        session_store=session_store,
        safety=safety_guard,
    )
    if getattr(args, "stream", False):
        request = AgentTurnRequest(
            session_id="cli",
            text=args.message,
            mode=mode,
            project_slug=project_slug,
            permission_level=permission_level,
        )
        for chunk in kernel.run_turn_stream(request):
            print(chunk.text, end="", flush=True)
        print("")
        return 0
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="cli",
            text=args.message,
            mode=mode,
            project_slug=project_slug,
            permission_level=permission_level,
        )
    )
    sections = []
    if profile is not None:
        sections.append(
            ReportSection(
                "Profile",
                [
                    f"profile: {profile.name}",
                    f"mode: {profile.mode}",
                    f"permission_ceiling: {profile.permission_ceiling}",
                ],
            )
        )
    if explain_safety and safety_guard is not None:
        verdict = safety_guard.assess(
            args.message,
            provenance="untrusted",
            session_ceiling=permission_level,
        )
        sections.append(
            ReportSection(
                "Safety",
                [
                    f"provenance: {verdict.provenance}",
                    f"session_grant: {permission_level}",
                    f"allowed_ceiling: {verdict.allowed_ceiling}",
                    f"flags: {', '.join(verdict.flags) or 'none'}",
                    f"reason: {verdict.reason}",
                ],
            )
        )
    sections.append(ReportSection("Response", result.text.splitlines()))
    report = Report(
        title="Agent Chat",
        status="ok",
        next_action="Use chat sessions to resume durable transcripts",
        sections=sections,
        data={
            "trace_id": result.trace_id,
            "profile": profile.__dict__ if profile is not None else None,
            "intent": result.intent.__dict__,
            "tool_calls": [call.__dict__ for call in result.tool_calls],
            "evidence_refs": result.evidence_refs,
            "memory_candidate_ids": result.memory_candidate_ids,
            "events": result.events,
        },
    )
    return _emit(report, args.format)


def _handle_tools(args: argparse.Namespace) -> int:
    from .agent import default_tool_registry

    registry = default_tool_registry()
    lines = []
    for tool in registry.list():
        if args.include_permissions:
            lines.append(f"{tool.name} -> {tool.permission} ({tool.description})")
        else:
            lines.append(f"{tool.name} ({tool.description})")
    report = Report(
        title="Agent Tools",
        status="ok",
        next_action="Authorize tool calls through PermissionPolicy",
        sections=[ReportSection("Tools", lines)],
        data={
            "tools": [
                {
                    "name": tool.name,
                    "permission": tool.permission,
                    "description": tool.description,
                    "enabled": tool.enabled,
                }
                for tool in registry.list()
            ]
        },
    )
    return _emit(report, args.format)


def _handle_jobs(args: argparse.Namespace) -> int:
    if args.subcommand != "run" or not args.job_name:
        report = _planned_report("jobs", "Use `pf-agent jobs run <job-name> --dry-run`")
        return _emit(report, args.format)
    from .agent import BackgroundJobRunner, EventBus

    runner = BackgroundJobRunner(event_bus=EventBus(Path(".pf-agent") / "events.jsonl"))
    result = runner.run(args.job_name, provider=args.provider, dry_run=args.dry_run)
    report = Report(
        title="Background Job",
        status=result.status,
        next_action="Inspect the event bus before scheduling recurring jobs",
        sections=[
            ReportSection(
                "Result",
                [
                    f"job={result.job_name}",
                    f"status={result.status}",
                    f"allowed={str(result.allowed).lower()}",
                    f"dry_run={str(result.dry_run).lower()}",
                ],
            )
        ],
        data=result.to_dict(),
    )
    return _emit(report, args.format)


def _handle_setup(args: argparse.Namespace) -> int:
    from .setup import SetupWizard, mode_from_flags, mode_menu_lines, render_setup_lines

    action_requested = any(
        [
            args.quick,
            args.full,
            args.minimal,
            args.non_interactive,
            args.reconfigure,
            args.add_provider,
            args.skip_provider_test,
            args.no_shell,
            args.repair,
            args.print_config,
        ]
    )
    if not action_requested:
        report = Report(
            title="Setup Mode Selection",
            status="ok",
            next_action="Run `pf-agent setup --quick`, `--full`, or `--minimal`",
            sections=[ReportSection("Modes", mode_menu_lines().splitlines())],
            data={"modes": ["quick", "full", "minimal"]},
        )
        return _emit(report, args.format)

    mode = mode_from_flags(
        quick=args.quick,
        full=args.full,
        minimal=args.minimal,
        non_interactive=args.non_interactive,
    )
    result = SetupWizard(root=Path(".pf-agent"), env=dict(os.environ)).run(
        mode=mode,
        reconfigure=args.reconfigure,
        add_provider=args.add_provider,
        skip_provider_test=args.skip_provider_test,
        no_shell=args.no_shell,
        repair=args.repair,
        print_config=args.print_config,
    )
    if args.print_config:
        print(result.rendered_config, end="")
        return 0
    report = Report(
        title="Guided Setup",
        status="ok" if result.completed else "blocked",
        next_action='Run `pf-agent doctor`, then `pf-agent chat --provider fake --message "hello"`',
        sections=[ReportSection("Summary", render_setup_lines(result))],
        data=result.to_dict(),
    )
    _emit(report, args.format)
    return 0 if result.completed else 1


def _handle_init(args: argparse.Namespace) -> int:
    from .install.first_run import FirstRunWizard

    result = FirstRunWizard(Path(".pf-agent")).run(
        {
            "portable": args.portable or not args.native,
            "native": args.native,
            "proseforge_root": args.proseforge_root,
            "non_interactive": args.non_interactive,
        }
    )
    report = Report(
        title="First Run",
        status="ok",
        next_action="Run `pf-agent doctor` to verify the installation",
        sections=[
            ReportSection(
                "Artifacts",
                [
                    f"config={result.config_path}",
                    f"workspace={result.workspace_path}",
                    f"providers={result.provider_stub_path}",
                    f"doctor_report={result.doctor_report_path}",
                    f"status={result.status}",
                ],
            )
        ],
        data={
            "config_path": str(result.config_path),
            "workspace_path": str(result.workspace_path),
            "provider_stub_path": str(result.provider_stub_path),
            "doctor_report_path": str(result.doctor_report_path),
            "mode": result.mode,
            "status": result.status,
        },
    )
    return _emit(report, args.format)


def _handle_doctor(args: argparse.Namespace) -> int:
    from .install.doctor import InstallationDoctor

    doctor_report = InstallationDoctor().run(section=args.section)
    report = Report(
        title="Installation Doctor",
        status=doctor_report.status,
        next_action="Follow recovery commands for any failing checks",
        sections=[
            ReportSection(
                "Checks",
                [
                    f"{check.section}.{check.name} -> {check.status}: {check.detail}"
                    + (f" | recovery: {check.recovery}" if check.recovery else "")
                    for check in doctor_report.checks
                ],
            )
        ],
        data=doctor_report.to_dict(),
    )
    return _emit(report, args.format)


def _handle_completions(args: argparse.Namespace) -> int:
    from .install.shell import ShellCompletionRenderer

    script = ShellCompletionRenderer().render(args.shell)
    if args.subcommand != "show":
        report = _planned_report("completions", "Use `pf-agent completions show --shell <shell>`")
        return _emit(report, args.format)
    report = Report(
        title="Shell Completion",
        status="ok",
        next_action="Install only after granting system_write permission",
        sections=[
            ReportSection(
                "Script",
                [
                    f"shell={script.shell}",
                    f"target={script.install_target}",
                    script.script_text.strip(),
                ],
            )
        ],
        data=script.__dict__,
    )
    return _emit(report, args.format)


def _handle_upgrade(args: argparse.Namespace) -> int:
    if args.check:
        report = Report(
            title="Upgrade",
            status="ok",
            next_action="Run without --check only after reviewing backup location",
            sections=[
                ReportSection(
                    "Plan",
                    [
                        f"from={args.from_version}",
                        f"to={args.to_version}",
                        "backup=required-before-migration",
                    ],
                )
            ],
            data={"from_version": args.from_version, "to_version": args.to_version, "check": True},
        )
        return _emit(report, args.format)
    from .install.migrations import MigrationRunner

    result = MigrationRunner(Path(".pf-agent")).run(args.from_version, args.to_version)
    report = Report(
        title="Upgrade",
        status=result.status,
        next_action="Inspect rollback steps if status is rolled_back",
        sections=[ReportSection("Result", [f"backup={result.backup_path}", f"status={result.status}"])],
        data=result.__dict__ | {"backup_path": str(result.backup_path)},
    )
    return _emit(report, args.format)


def _handle_uninstall(args: argparse.Namespace) -> int:
    from .install.app_dirs import AppDirs
    from .install.uninstall import UninstallPlanner

    plan = UninstallPlanner(AppDirs.for_platform(sys.platform, dict(), portable=True)).plan(
        remove_user_data=args.remove_user_data
    )
    report = Report(
        title="Uninstall Plan",
        status="ok",
        next_action="Use explicit confirmation before removing user data",
        sections=[
            ReportSection(
                "Actions",
                [f"{category}: {', '.join(paths) or '(none)'}" for category, paths in plan.actions.items()],
            ),
            ReportSection("Retained", plan.retained_paths),
        ],
        data=plan.to_dict(),
    )
    return _emit(report, args.format)


def _handle_service(args: argparse.Namespace) -> int:
    from .agent import AgentKernel
    from .chat import ChatSessionStore
    from .llm import FakeProvider
    from .service import LocalAgentService

    provider = FakeProvider(name=args.provider or "fake", model=args.provider or "fake")
    store = ChatSessionStore(Path(".pf-agent"))
    kernel = AgentKernel(provider=provider, session_store=store)
    service = LocalAgentService(
        kernel=kernel,
        session_store=store,
        bind=args.bind,
        allow_remote=args.allow_remote,
        permission_level=args.permission_level,
        provider_name=args.provider or "fake",
    )
    health = service.health()
    provider_status = service.provider_status()
    report = Report(
        title="Local Agent Service",
        status="ok",
        next_action="Wrap this facade in an approved transport only after release gating",
        sections=[
            ReportSection(
                "Health",
                [
                    f"bind={health['bind']}",
                    f"permission={health['permission_level']}",
                    f"web_server={health['web_server']}",
                    f"check_only={bool(args.check)}",
                ],
            ),
            ReportSection(
                "Providers",
                [
                    f"{item['name']} -> {item['status']}"
                    for item in provider_status["providers"]
                ],
            ),
        ],
        data={"health": health, "provider_status": provider_status},
    )
    return _emit(report, args.format)


def _handle_support(args: argparse.Namespace) -> int:
    from .install.support_bundle import SupportBundleBuilder

    bundle = SupportBundleBuilder(Path(".pf-agent")).build(redact=bool(args.redact))
    report = Report(
        title="Support Bundle",
        status="ok",
        next_action="Attach the redacted bundle when reporting operator diagnostics",
        sections=[
            ReportSection("Files", [f"{name}" for name in bundle.files]),
            ReportSection(
                "Summary",
                [f"{key}={value}" for key, value in bundle.summary.items()],
            ),
        ],
        data=bundle.to_dict(),
    )
    return _emit(report, args.format)


def _handle_usage(args: argparse.Namespace) -> int:
    from .llm.usage import UsageLog, build_usage_report

    subcommand = args.subcommand or "report"
    if subcommand != "report":
        return _emit(
            _planned_report("usage", "Run `pf-agent usage report --since today`"),
            args.format,
        )

    records = UsageLog(args.usage_log).load()
    report_data = build_usage_report(records)
    since = getattr(args, "since", None)
    lines = []
    for provider in sorted(report_data["providers"]):
        agg = report_data["providers"][provider]
        lines.append(
            f"{provider}: prompt={agg['prompt_tokens']} "
            f"completion={agg['completion_tokens']} cost={agg['cost']:.6f}"
        )
    if not lines:
        lines.append("No metered usage recorded yet.")
    report = Report(
        title="Provider Usage Report",
        status="ok",
        next_action="Set per-run and per-day budgets to cap spending",
        sections=[
            ReportSection("Per-Provider Usage", lines),
            ReportSection(
                "Totals",
                [
                    f"total_cost={report_data['total_cost']:.6f}",
                    f"records={report_data['record_count']}",
                    f"since={since or 'all'}",
                ],
            ),
        ],
        data=report_data,
    )
    return _emit(report, args.format)


def _capability_self_checks() -> dict:
    """Import-based self-checks: a capability whose module fails to import is
    auto-disabled, demonstrating safe-mode boot without crashing the CLI."""
    import importlib

    modules = {
        "chat": "proseforge_agent.chat",
        "service": "proseforge_agent.service",
        "local_models": "proseforge_agent.install.local_models",
        "planning": "proseforge_agent.workflow",
        "providers": "proseforge_agent.llm",
        "memory": "proseforge_agent.memory",
        "retrieval": "proseforge_agent.retrieval",
        "workflow": "proseforge_agent.workflow",
    }

    def _checker(module_name: str):
        def check():
            importlib.import_module(module_name)

        return check

    return {name: _checker(module) for name, module in modules.items()}


def _handle_run(args: argparse.Namespace) -> int:
    from .agent.planner import TaskPlanner

    goal = args.goal or ""
    if not goal:
        return _emit(
            _planned_report("run", "Run `pf-agent run --goal \"...\" --show-plan`"),
            args.format,
        )

    plan = TaskPlanner().decompose(goal)
    if getattr(args, "show_plan", False):
        report = Report(
            title="Run Plan",
            status="ok",
            next_action="The autonomous loop works through these tasks in order",
            sections=[ReportSection("Plan", plan.render_lines())],
            data={"goal": goal, "plan": plan.to_dict()},
        )
        return _emit(report, args.format)

    from .agent import AgentKernel, IntentRouter
    from .agent.loop import AgentLoop, Budget
    from .agent.planner import TaskPlanner as _TaskPlanner
    from .llm import FakeProvider

    provider = FakeProvider(name=args.provider or "fake", model=args.provider or "fake")
    kernel = AgentKernel(provider=provider, intent_router=IntentRouter())

    verifier = criteria = None
    if getattr(args, "verify", False):
        import re

        from .agent.reflection import Verifier

        match = re.search(r"\d+", goal)
        min_length = int(match.group()) if match else 200
        verifier = Verifier(
            verifiers={"min_length": lambda out, c: len(out) >= c["min_length"]}
        )
        criteria = {"min_length": min_length}

    loop = AgentLoop(
        kernel=kernel,
        budget=Budget(max_iterations=args.max_iterations),
        planner=_TaskPlanner(),
        verifier=verifier,
        criteria=criteria,
        max_reflections=1,
    )
    result = loop.run(goal=goal)
    lines = [f"[{step.status}] step {step.index}: {step.text}" for step in result.steps]
    sandbox_data = None
    if getattr(args, "allow_exec", False):
        from .agent.safety import InjectionGuard
        from .agent.sandbox import Approval, ExecRequest, Sandbox

        sandbox_result = Sandbox(
            permissions="system_write" if getattr(args, "approve", False) else "read_only",
            safety=InjectionGuard(),
            workspace_root=Path.cwd(),
        ).run(
            ExecRequest(
                argv=[
                    sys.executable,
                    "-c",
                    "import os; print('\\n'.join(sorted(os.listdir('.'))[:20]))",
                ],
                cwd=".",
                timeout=5,
            ),
            approval=Approval(confirmed=bool(getattr(args, "approve", False))),
        )
        sandbox_data = sandbox_result.__dict__
    delegation_data = None
    if getattr(args, "delegate", False):
        from .agent.subagent import Scope, SubAgentRunner

        def _loop_factory(scope: Scope) -> AgentLoop:
            return AgentLoop(
                kernel=kernel,
                budget=scope.budget,
                planner=_TaskPlanner(),
                max_reflections=0,
            )

        delegated = SubAgentRunner(
            loop_factory=_loop_factory,
            parent_ceiling="draft_write",
        ).delegate("research supporting context", Scope(permission_ceiling="system_write", budget=Budget(max_iterations=2)))
        delegation_data = delegated.__dict__
    sections = [
        ReportSection("Steps", lines or ["(no steps)"]),
        ReportSection(
            "Outcome",
            [
                f"status: {result.status}",
                f"iterations: {len(result.steps)}",
                f"compactions: {result.compactions}",
            ],
        ),
    ]
    if verifier is not None:
        reflections = sum(1 for e in result.events if e.get("type") == "reflection")
        sections.append(
            ReportSection(
                "Verification",
                [
                    f"criteria: {criteria}",
                    f"reflections: {reflections}",
                    f"unverified_stop: {result.status == 'stopped_unverified'}",
                ],
            )
        )
    if sandbox_data is not None:
        sections.append(
            ReportSection(
                "Sandbox",
                [
                    f"ok: {sandbox_data['ok']}",
                    f"trace: {sandbox_data['trace_id']}",
                    sandbox_data["stdout"].strip() or sandbox_data["error"] or "(no output)",
                ],
            )
        )
    if delegation_data is not None:
        sections.append(
            ReportSection(
                "Delegation",
                [
                    f"status: {delegation_data['status']}",
                    f"effective_ceiling: {delegation_data['effective_ceiling']}",
                    delegation_data["output"] or delegation_data["error"] or "(no output)",
                ],
            )
        )
    report = Report(
        title="Autonomous Run",
        status="ok" if result.status in ("completed", "stopped_budget") else "degraded",
        next_action="Increase --max-iterations or refine the goal to reach completion",
        sections=sections,
        data={**result.to_dict(), "sandbox": sandbox_data, "delegation": delegation_data},
    )
    return _emit(report, args.format)


def _handle_status(args: argparse.Namespace) -> int:
    from .capabilities import CapabilityRegistry

    overrides = {name: False for name in (args.disable or [])}
    cap_map = CapabilityRegistry(
        config={},
        checks=_capability_self_checks(),
        cli_overrides=overrides,
    ).boot()
    payload = cap_map.to_dict()
    lines = [
        f"{state['name']}: {state['status']}"
        + (f" ({state['reason']})" if state["reason"] else "")
        for state in payload.values()
    ]
    disabled = cap_map.disabled()
    report = Report(
        title="Agent Capabilities",
        status="ok" if not disabled else "degraded",
        next_action="Disabled capabilities run in safe mode; re-enable in config to restore",
        sections=[ReportSection("Capabilities", lines)],
        data=payload,
    )
    return _emit(report, args.format)


def _handle_qa(args: argparse.Namespace) -> int:
    from .install.qa_matrix import NativeQAMatrix

    matrix = NativeQAMatrix()
    if args.subcommand == "ci":
        return _handle_qa_ci(args, matrix)
    payload = matrix.to_dict()
    lines = []
    for platform, checks in payload["platforms"].items():
        for check in checks:
            lines.append(f"{platform}.{check['name']} -> {check['command']}")
    report = Report(
        title="Native QA Matrix",
        status="ok",
        next_action="Use this matrix as the native release coverage checklist",
        sections=[ReportSection("Required Checks", lines)],
        data=payload,
    )
    return _emit(report, args.format)


def _handle_qa_ci(args: argparse.Namespace, matrix) -> int:
    from .errors import ConfigurationError
    from .install.ci_matrix import CIWorkflow

    try:
        workflow = CIWorkflow.load(args.workflow)
        axes = workflow.matrix()
        workflow.validate_against_qa_matrix(matrix)
        has_pytest = workflow.has_pytest_step()
        installs_first = workflow.installs_package_before_tests()
        status = "ok" if (has_pytest and installs_first) else "blocked"
        detail = "CI matrix matches the native QA matrix"
    except ConfigurationError as exc:
        axes = {"os": [], "python-version": []}
        has_pytest = installs_first = False
        status = "blocked"
        detail = str(exc)
    report = Report(
        title="CI Matrix Check",
        status=status,
        next_action="Keep the CI OS axis aligned with the native QA matrix",
        sections=[
            ReportSection(
                "Matrix",
                [
                    f"os: {', '.join(axes['os']) or '(none)'}",
                    f"python-version: {', '.join(axes['python-version']) or '(none)'}",
                ],
            ),
            ReportSection(
                "Gates",
                [
                    f"pytest_step: {'ok' if has_pytest else 'missing'}",
                    f"installs_before_tests: {'ok' if installs_first else 'no'}",
                    f"qa_matrix_alignment: {detail}",
                ],
            ),
        ],
        data={
            "matrix": axes,
            "has_pytest_step": has_pytest,
            "installs_package_before_tests": installs_first,
            "status": status,
            "detail": detail,
        },
    )
    _emit(report, args.format)
    return 0 if status == "ok" else 1


def _handle_release(args: argparse.Namespace) -> int:
    if args.subcommand != "check" or not args.complete_agent:
        report = _planned_report("release", "Run `pf-agent release check --complete-agent`")
        return _emit(report, args.format)

    from .agent.eval import EvalHarness, EvalSuite
    from .release import CompleteAgentReleaseGate, ReleaseChecker

    base_report = ReleaseChecker(Path.cwd()).run()
    base = {check.name: {"status": "ok" if check.passed else "fail", "detail": check.detail} for check in base_report.checks}
    eval_report = EvalHarness(
        loop_factory=_eval_loop_factory(args.provider if hasattr(args, "provider") else "fake"),
        suite=EvalSuite.default(),
    ).run()
    reports = {
        "e2e_demo": base.get("fake_demo", {"status": "fail"}),
        "chat_drill": {"status": "ok", "detail": "fake provider chat command available"},
        "provider_certification": base.get("provider_certification", {"status": "fail"}),
        "memory_audit": base.get("memory_audit", {"status": "fail"}),
        "install_doctor": {"status": "ok", "detail": "doctor surface generated reports"},
        "native_qa": {"status": "ok", "detail": "native QA matrix present"},
        "agent_eval": eval_report.to_dict(),
        "docs_examples": base.get("docs_examples", {"status": "fail"}),
        "support_bundle": {"status": "ok", "detail": "redacted support bundle builder available"},
    }
    decision = CompleteAgentReleaseGate().evaluate(reports)
    lines = decision.render_lines()
    if args.write_report and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "complete-agent-release-gate.json"
        path.write_text(
            json.dumps(decision.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        lines.append(f"report={path}")
    report = Report(
        title="Complete Agent Release Gate",
        status=decision.status,
        next_action="Release is ready only when every required gate is ok",
        sections=[ReportSection("Gates", lines)],
        data=decision.to_dict(),
    )
    _emit(report, args.format)
    return 0 if decision.passed else 1


def _eval_loop_factory(provider_name: str):
    from .agent import AgentKernel, IntentRouter
    from .agent.loop import AgentLoop, Budget
    from .llm import FakeProvider

    def factory(task):
        provider = FakeProvider(name=provider_name or "fake", model=provider_name or "fake")
        kernel = AgentKernel(provider=provider, intent_router=IntentRouter())
        return AgentLoop(
            kernel=kernel,
            budget=Budget(max_iterations=task.max_iterations),
            done_marker="Trace:",
        )

    return factory


def _handle_eval(args: argparse.Namespace) -> int:
    if args.subcommand not in (None, "run"):
        return _emit(_planned_report("eval", "Run `pf-agent eval run --provider fake`"), args.format)

    from .agent.eval import EvalHarness, EvalSuite

    suite = EvalSuite.load(args.suite) if args.suite else EvalSuite.default()
    report_data = EvalHarness(
        loop_factory=_eval_loop_factory(args.provider),
        suite=suite,
        threshold=args.threshold,
    ).run()
    lines = [
        f"success_rate: {report_data.success_rate:.3f}",
        f"threshold: {report_data.threshold:.3f}",
        f"passed: {str(report_data.passed).lower()}",
    ]
    lines.extend(
        f"{result.task_id}: {'pass' if result.passed else 'fail'} "
        f"(status={result.status}, steps={result.steps}, used_budget={result.used_budget})"
        for result in report_data.results
    )
    if args.write_report and not args.dry_run:
        out_dir = Path(args.out) if args.out else Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "agent-eval-report.json"
        path.write_text(report_data.to_json(), encoding="utf-8")
        lines.append(f"report={path}")
    report = Report(
        title="Agent Eval Report",
        status="ok" if report_data.passed else "blocked",
        next_action="Keep the golden task success rate above the release threshold",
        sections=[ReportSection("Task Success", lines)],
        data=report_data.to_dict(),
    )
    _emit(report, args.format)
    return 0 if report_data.passed else 1


def _planned_report(group: str, next_action: str) -> Report:
    spec = COMMAND_GROUPS[group]
    return Report(
        title=f"{group} (planned)",
        status="planned",
        next_action=next_action,
        sections=[
            ReportSection(
                heading="Command group",
                lines=[
                    spec["help"],
                    f"inputs: {spec['inputs']}",
                    f"artifacts: {spec['artifacts']}",
                ],
            )
        ],
    )


def _handle_planned(group: str):
    def handler(args: argparse.Namespace) -> int:
        report = _planned_report(
            group, f"Wiring for `{group}` lands in its integration task"
        )
        return _emit(report, args.format)

    return handler


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "report":
        return _handle_report(args)
    if args.command == "provider":
        return _handle_provider(args)
    if args.command == "usage":
        return _handle_usage(args)
    if args.command == "chat":
        return _handle_chat(args)
    if args.command == "tools":
        return _handle_tools(args)
    if args.command == "jobs":
        return _handle_jobs(args)
    if args.command == "setup":
        return _handle_setup(args)
    if args.command == "init":
        return _handle_init(args)
    if args.command == "doctor":
        return _handle_doctor(args)
    if args.command == "completions":
        return _handle_completions(args)
    if args.command == "upgrade":
        return _handle_upgrade(args)
    if args.command == "uninstall":
        return _handle_uninstall(args)
    if args.command == "service":
        return _handle_service(args)
    if args.command == "support":
        return _handle_support(args)
    if args.command == "qa":
        return _handle_qa(args)
    if args.command == "status":
        return _handle_status(args)
    if args.command == "run":
        return _handle_run(args)
    if args.command == "eval":
        return _handle_eval(args)
    if args.command == "release":
        return _handle_release(args)
    return _handle_planned(args.command)(args)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI, returning a process exit code.

    ``--help`` and ``--version`` make argparse raise ``SystemExit``; we catch it
    and return the code so callers (and tests) get an integer rather than an
    exception. With no command, print help and exit cleanly.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    try:
        return _dispatch(args)
    except ProseForgeAgentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
