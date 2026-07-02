from proseforge_agent import cli


def test_cli_help_returns_zero():
    # Task 15 changed main() to catch argparse's SystemExit and return the code,
    # so --help yields an integer 0 rather than raising.
    assert cli.main(["--help"]) == 0


def test_cli_no_args_with_no_default_returns_zero():
    # Task 186: bare `pf-agent` now launches the default chat REPL / first-run
    # routing. `--no-default` preserves the pre-186 print-help behavior.
    assert cli.main(["--no-default"]) == 0
