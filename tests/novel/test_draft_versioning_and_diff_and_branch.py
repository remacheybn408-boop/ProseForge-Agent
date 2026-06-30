"""Draft versioning / diff / branch / rollback tests (Task 104)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import DraftVersionStore, NovelProjectStore


def test_draft_versioning_and_diff_and_branch_contract(tmp_path):
    """After a rewrite, versions can be diffed and rolled back (with approval)."""
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    store = DraftVersionStore(tmp_path, slug="demo_novel")

    v1 = store.commit("ch_001", "原始文本。", provider="fake", prompt="draft")
    v2 = store.commit("ch_001", "修改后的文本。", provider="fake", prompt="rewrite")

    assert v1.id != v2.id
    assert v1.checksum != v2.checksum
    assert v2.provider == "fake" and v2.prompt == "rewrite"
    assert [version.id for version in store.list_versions("ch_001")] == [v1.id, v2.id]

    diff = store.diff(v1.id, v2.id)
    assert diff.changed
    assert diff.diff

    pending = store.rollback("ch_001", to=v1.id)
    assert pending.status == "pending_approval"
    assert pending.approved is False

    rolled = store.rollback("ch_001", to=v1.id, approve=True)
    assert rolled.status == "rolled_back"
    chapter = tmp_path / "projects" / "demo_novel" / "chapters" / "ch_001.md"
    assert chapter.read_text(encoding="utf-8") == "原始文本。"


def test_checksum_is_stable_for_identical_text(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    store = DraftVersionStore(tmp_path, slug="demo_novel")

    a = store.commit("ch_001", "同样的文本。")
    b = store.commit("ch_001", "同样的文本。")

    assert a.id != b.id
    assert a.checksum == b.checksum


def test_metadata_persists_across_instances(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    DraftVersionStore(tmp_path, slug="demo_novel").commit("ch_001", "x", provider="deepseek", prompt="rewrite")

    reloaded = DraftVersionStore(tmp_path, slug="demo_novel").list_versions("ch_001")

    assert reloaded[0].provider == "deepseek"
    assert reloaded[0].prompt == "rewrite"
    assert reloaded[0].checksum


def test_rollback_without_approval_keeps_chapter(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    store = DraftVersionStore(tmp_path, slug="demo_novel")
    store.commit("ch_001", "第一版。")
    store.commit("ch_001", "第二版。")
    chapter = tmp_path / "projects" / "demo_novel" / "chapters" / "ch_001.md"
    chapter.parent.mkdir(parents=True, exist_ok=True)
    chapter.write_text("当前内容。", encoding="utf-8")

    store.rollback("ch_001", to="draft_v1")

    assert chapter.read_text(encoding="utf-8") == "当前内容。"


def test_unknown_version_raises(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    store = DraftVersionStore(tmp_path, slug="demo_novel")
    store.commit("ch_001", "x")

    for call in (
        lambda: store.diff("draft_v1", "draft_v99"),
        lambda: store.rollback("ch_001", to="draft_v99", approve=True),
    ):
        try:
            call()
        except ValueError as exc:
            assert "draft_v99" in str(exc)
        else:
            raise AssertionError("unknown version should fail")


def test_branch_forks_from_a_version(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    store = DraftVersionStore(tmp_path, slug="demo_novel")
    base = store.commit("ch_001", "主线文本。", provider="fake")

    branch = store.branch("ch_001", name="alt-ending")

    assert branch.base_version == base.id
    assert branch.head_version != base.id
    head = {version.id: version for version in store.list_versions("ch_001")}[branch.head_version]
    assert head.branch == "alt-ending"


def test_draft_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    store = DraftVersionStore(tmp_path / ".pf-agent" / "workspace", slug="demo_novel")
    store.commit("ch_001", "原始。", provider="fake", prompt="draft")
    store.commit("ch_001", "修改。", provider="fake", prompt="rewrite")

    assert main(["draft", "version", "list", "--slug", "demo_novel", "--chapter", "ch_001"]) == 0
    assert "draft_v1" in capsys.readouterr().out

    assert main(["draft", "diff", "draft_v1", "draft_v2", "--slug", "demo_novel"]) == 0
    assert "Draft Diff" in capsys.readouterr().out

    assert main(["draft", "rollback", "--slug", "demo_novel", "--chapter", "ch_001", "--to", "draft_v1", "--approve"]) == 0
    assert "rolled_back" in capsys.readouterr().out
