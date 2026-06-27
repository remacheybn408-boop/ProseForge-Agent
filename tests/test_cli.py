import pytest

from proseforge_agent import cli


def test_cli_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0


def test_cli_no_args_returns_zero():
    assert cli.main([]) == 0
