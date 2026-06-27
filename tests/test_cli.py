from proseforge_agent import cli


def test_cli_help_returns_zero():
    # Task 15 changed main() to catch argparse's SystemExit and return the code,
    # so --help yields an integer 0 rather than raising.
    assert cli.main(["--help"]) == 0


def test_cli_no_args_returns_zero():
    assert cli.main([]) == 0
