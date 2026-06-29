"""Novel project manifest tests (Task 81)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore


def test_novel_project_manifest_contract(tmp_path):
    store = NovelProjectStore(tmp_path)
    manifest = store.init_project(
        slug="demo_novel",
        title="示例小说",
        author="Author",
        language="zh-CN",
    )
    payload = yaml.safe_load(manifest.path.read_text(encoding="utf-8"))
    assert manifest.path.name == "project.manifest.yaml"
    assert payload["project"]["slug"] == "demo_novel"
    assert payload["project"]["title"] == "示例小说"
    assert payload["project"]["author"] == "Author"
    assert payload["project"]["language"] == "zh-CN"
    assert payload["structure"]["volumes"] == []
    assert payload["assets"]["bible"] == []
    assert payload["assets"]["rules"] == []
    assert payload["metadata"] == {}


def test_manifest_load_and_validate(tmp_path):
    store = NovelProjectStore(tmp_path)
    store.init_project(slug="demo_novel")
    manifest = store.load("demo_novel")
    validation = store.validate("demo_novel")
    assert manifest.project["slug"] == "demo_novel"
    assert validation["status"] == "ok"
    assert validation["errors"] == []


def test_project_init_cli_writes_manifest(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["project", "init", "--slug", "demo_novel", "--title", "Demo Novel"])
    out = capsys.readouterr().out
    path = tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "project.manifest.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert code == 0
    assert "Project Manifest" in out
    assert payload["project"]["slug"] == "demo_novel"


def test_project_manifest_and_validate_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert main(["project", "manifest", "--slug", "demo_novel"]) == 0
    assert main(["project", "validate", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "demo_novel" in out
    assert "valid" in out.lower()
