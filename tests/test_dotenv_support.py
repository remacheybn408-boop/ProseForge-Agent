"""`.env` support tests (Task 191)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from proseforge_agent.dotenv import RECOGNIZED_KEYS, DotenvLoader
from proseforge_agent.errors import ConfigurationError


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dotenv_loader_populates_env_without_overriding(monkeypatch, tmp_path):
    monkeypatch.setenv("EXISTING", "keep-me")
    monkeypatch.delenv("NEW_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING=override\nNEW_KEY=hello\n", encoding="utf-8")

    audit = DotenvLoader([env_file]).load()

    assert os.environ["EXISTING"] == "keep-me"
    assert os.environ["NEW_KEY"] == "hello"
    assert audit["NEW_KEY"].endswith(".env")


def test_dotenv_parser_handles_quoted_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'DQ="value with spaces"\nSQ=\'literal $x\'\nBARE=plain\n',
        encoding="utf-8",
    )
    parsed = DotenvLoader([env_file]).parse_one(env_file)
    assert parsed["DQ"] == "value with spaces"
    assert parsed["SQ"] == "literal $x"
    assert parsed["BARE"] == "plain"


def test_dotenv_parser_handles_comments_blank_lines_and_export(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# a comment\n\nexport KEY=value\n   \n# trailing\n",
        encoding="utf-8",
    )
    parsed = DotenvLoader([env_file]).parse_one(env_file)
    assert parsed == {"KEY": "value"}


def test_dotenv_parser_preserves_trailing_hash_in_unquoted_value(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("URL=http://x/#frag\n", encoding="utf-8")
    parsed = DotenvLoader([env_file]).parse_one(env_file)
    assert parsed["URL"] == "http://x/#frag"


def test_dotenv_precedence_prefers_env_local_over_env(monkeypatch, tmp_path):
    monkeypatch.delenv("KEY", raising=False)
    env = tmp_path / ".env"
    env_local = tmp_path / ".env.local"
    env.write_text("KEY=fromenv\n", encoding="utf-8")
    env_local.write_text("KEY=fromlocal\n", encoding="utf-8")

    # paths are ordered low-to-high precedence
    DotenvLoader([env, env_local]).load()
    assert os.environ["KEY"] == "fromlocal"


def test_dotenv_machine_env_is_lowest_precedence(monkeypatch, tmp_path):
    monkeypatch.delenv("KEY", raising=False)
    machine = tmp_path / "machine.env"
    env = tmp_path / ".env"
    machine.write_text("KEY=machine\n", encoding="utf-8")
    env.write_text("KEY=fromenv\n", encoding="utf-8")

    DotenvLoader([machine, env]).load()
    assert os.environ["KEY"] == "fromenv"


def test_dotenv_missing_files_are_silent(tmp_path):
    audit = DotenvLoader([tmp_path / "nope.env"]).load()
    assert audit == {}


def test_dotenv_bad_syntax_reports_line_but_does_not_raise(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("GOOD=1\nthis-has-no-equals\nALSO_GOOD=2\n", encoding="utf-8")
    loader = DotenvLoader([env_file])
    parsed = loader.parse_one(env_file)
    assert parsed == {"GOOD": "1", "ALSO_GOOD": "2"}
    assert any("no-equals" in w or "line" in w.lower() for w in loader.warnings)


def test_dotenv_nul_bytes_rejected(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"KEY=val\x00ue\n")
    with pytest.raises(ConfigurationError):
        DotenvLoader([env_file]).parse_one(env_file)


def test_env_example_exists_and_covers_recognized_keys():
    example = REPO_ROOT / ".env.example"
    assert example.exists()
    text = example.read_text(encoding="utf-8")
    for key in RECOGNIZED_KEYS:
        assert key in text, f".env.example missing documented key: {key}"


def test_gitignore_excludes_env_files():
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in text
