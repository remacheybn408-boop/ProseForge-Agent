import json

from proseforge_agent.cli import main


def test_cli_lists_required_command_groups(capsys):
    code = main(["--help"])
    out = capsys.readouterr().out
    assert code == 0
    for name in ["provider", "memory", "chapter", "workflow", "report"]:
        assert name in out


def test_cli_no_args_prints_help_and_exits_zero(capsys):
    code = main([])
    out = capsys.readouterr().out
    assert code == 0
    assert "usage" in out.lower()


def test_cli_version_returns_zero(capsys):
    code = main(["--version"])
    assert code == 0


def test_group_help_names_inputs_and_artifacts(capsys):
    code = main(["chapter", "--help"])
    out = capsys.readouterr().out.lower()
    assert code == 0
    assert "input" in out
    assert "artifact" in out


def test_filesystem_command_offers_dry_run(capsys):
    code = main(["report", "--help"])
    out = capsys.readouterr().out
    assert code == 0
    assert "--dry-run" in out
    assert "--write" in out


def test_report_command_reference_writes_file(tmp_path, capsys):
    code = main(["report", "command-reference", "--write", "--out", str(tmp_path)])
    assert code == 0
    written = list(tmp_path.glob("command-reference*"))
    assert written


def test_report_json_format_is_stable(capsys):
    code = main(["report", "command-reference", "--format", "json"])
    out_a = capsys.readouterr().out
    assert code == 0
    payload = json.loads(out_a)
    assert payload["status"]
    assert payload["next_action"]

    main(["report", "command-reference", "--format", "json"])
    out_b = capsys.readouterr().out
    assert out_a == out_b


def test_provider_routes_writes_report(tmp_path):
    code = main(
        [
            "provider",
            "routes",
            "--all-policies",
            "--write-report",
            "--out",
            str(tmp_path),
        ]
    )
    assert code == 0
    assert list(tmp_path.glob("provider-routes*"))


def test_unknown_command_errors_nonzero(capsys):
    code = main(["bogus"])
    assert code != 0
