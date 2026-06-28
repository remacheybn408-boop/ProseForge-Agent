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
        if name == "tools":
            group.add_argument(
                "--include-permissions",
                action="store_true",
                help="include permission levels in the tool list",
            )
        if name == "jobs":
            group.add_argument("job_name", nargs="?", help="allow-listed background job")
            group.add_argument("--provider", default="fake", help="provider for the job")
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
    if getattr(args, "show_prompt", False):
        from .chat import ChatPromptBuilder

        text = args.message or args.text or ""
        print(
            ChatPromptBuilder()
            .build(text=text, mode=args.mode, project_slug=project_slug)
            .render_markdown()
        )
        return 0
    if getattr(args, "propose_handoff", False):
        from .chat.handoff import ChatWorkflowHandoff, render_handoff

        text = args.message or args.text or ""
        package = ChatWorkflowHandoff().create(
            text,
            project_slug=project_slug,
            mode=args.mode,
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
            mode=args.mode,
            project_slug=project_slug,
            permission_level=args.permission_level,
        ).run()
    from .agent import AgentKernel, AgentTurnRequest, IntentRouter

    kernel = AgentKernel(
        provider=provider,
        intent_router=IntentRouter(),
        session_store=session_store,
    )
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="cli",
            text=args.message,
            mode=args.mode,
            project_slug=project_slug,
            permission_level=args.permission_level,
        )
    )
    report = Report(
        title="Agent Chat",
        status="ok",
        next_action="Use chat sessions to resume durable transcripts",
        sections=[ReportSection("Response", result.text.splitlines())],
        data={
            "trace_id": result.trace_id,
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
    if args.command == "chat":
        return _handle_chat(args)
    if args.command == "tools":
        return _handle_tools(args)
    if args.command == "jobs":
        return _handle_jobs(args)
    if args.command == "init":
        return _handle_init(args)
    if args.command == "doctor":
        return _handle_doctor(args)
    if args.command == "completions":
        return _handle_completions(args)
    if args.command == "upgrade":
        return _handle_upgrade(args)
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
