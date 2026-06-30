"""Manuscript search tests (Task 102)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import ManuscriptSearch, NovelProjectStore


def _seed(root, slug, rel, text):
    path = root / "projects" / slug / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_manuscript_search_contract(tmp_path):
    """Searching a character name returns the chapters and line snippets where it appears."""
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    _seed(tmp_path, "demo_novel", "chapters/ch_001.md", "林夜走进房间。\n他看见了影子。")
    _seed(tmp_path, "demo_novel", "chapters/ch_002.md", "第二天，林夜离开了。")
    searcher = ManuscriptSearch(tmp_path, slug="demo_novel")

    result = searcher.search("林夜")

    chapters = {hit.chapter for hit in result.hits}
    assert {"ch_001", "ch_002"} <= chapters
    assert all(hit.snippet for hit in result.hits)
    assert all(hit.line >= 1 for hit in result.hits)
    assert all(hit.path for hit in result.hits)
    assert result.count == len(result.hits)
    data = result.to_dict()
    assert data["hits"] and data["query"] == "林夜"


def test_manuscript_search_exact_phrase(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    _seed(tmp_path, "demo_novel", "chapters/ch_001.md", "林夜走进房间。")
    _seed(tmp_path, "demo_novel", "chapters/ch_002.md", "第二天，林夜离开了。")
    searcher = ManuscriptSearch(tmp_path, slug="demo_novel")

    result = searcher.search("林夜离开", exact=True)

    assert {hit.chapter for hit in result.hits} == {"ch_002"}


def test_manuscript_search_scope_controls_domains(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    _seed(tmp_path, "demo_novel", "chapters/ch_001.md", "林夜走进房间。")
    _seed(tmp_path, "demo_novel", "bible/world.md", "林夜是主角。")
    searcher = ManuscriptSearch(tmp_path, slug="demo_novel")

    manuscript = searcher.search("林夜", scope="manuscript")
    assert "bible" not in {hit.domain for hit in manuscript.hits}

    everything = searcher.search("林夜", scope="all")
    assert "bible" in {hit.domain for hit in everything.hits}


def test_manuscript_search_no_match_is_empty(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    _seed(tmp_path, "demo_novel", "chapters/ch_001.md", "林夜走进房间。")
    searcher = ManuscriptSearch(tmp_path, slug="demo_novel")

    result = searcher.search("不存在的人")

    assert result.hits == []
    assert result.count == 0


def test_manuscript_search_unknown_scope_raises(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    searcher = ManuscriptSearch(tmp_path, slug="demo_novel")

    try:
        searcher.search("林夜", scope="weird")
    except ValueError as exc:
        assert "weird" in str(exc)
    else:
        raise AssertionError("unknown scope should fail")


def test_manuscript_search_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    chapter = tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "chapters" / "ch_001.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("林夜走进房间。", encoding="utf-8")

    assert main(["search", "林夜", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Manuscript Search" in out
    assert "ch_001" in out
