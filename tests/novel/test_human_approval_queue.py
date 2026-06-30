"""Human approval queue tests (Task 106)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import ApprovalQueue, NovelProjectStore


def test_human_approval_queue_contract(tmp_path):
    """High-risk actions enter the queue as pending and are only resolved by a human decision."""
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    queue = ApprovalQueue(tmp_path, slug="demo_novel")

    req = queue.submit("overwrite_draft", summary="overwrite ch_001", payload={"chapter": "ch_001"})
    assert req.status == "pending"
    assert req.id in {item.id for item in queue.list()}
    assert [item.id for item in queue.list(status="pending")] == [req.id]

    approved = queue.approve(req.id)
    assert approved.status == "approved"

    other = queue.submit("export_final")
    rejected = queue.reject(other.id)
    assert rejected.status == "rejected"
    assert [item.id for item in queue.list(status="pending")] == []


def test_submit_rejects_unknown_action(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    queue = ApprovalQueue(tmp_path, slug="demo_novel")

    try:
        queue.submit("rename_file")
    except ValueError as exc:
        assert "rename_file" in str(exc)
    else:
        raise AssertionError("non high-risk action should not enter the queue")


def test_decisions_on_unknown_or_decided_requests_fail(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    queue = ApprovalQueue(tmp_path, slug="demo_novel")
    req = queue.submit("rollback_version")
    queue.approve(req.id)

    for call in (lambda: queue.show("approval_999"), lambda: queue.approve("approval_999"), lambda: queue.approve(req.id)):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid decision should fail")


def test_queue_persists_across_instances(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    req = ApprovalQueue(tmp_path, slug="demo_novel").submit("delete_artifact", summary="drop graph node")

    reloaded = ApprovalQueue(tmp_path, slug="demo_novel").show(req.id)

    assert reloaded.action == "delete_artifact"
    assert reloaded.status == "pending"
    assert reloaded.summary == "drop graph node"


def test_approval_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    req = ApprovalQueue(tmp_path / ".pf-agent" / "workspace", slug="demo_novel").submit(
        "modify_global_rules", summary="ban em dash"
    )

    assert main(["approval", "list", "--slug", "demo_novel"]) == 0
    assert req.id in capsys.readouterr().out

    assert main(["approval", "show", req.id, "--slug", "demo_novel"]) == 0
    assert "ban em dash" in capsys.readouterr().out

    assert main(["approval", "approve", req.id, "--slug", "demo_novel"]) == 0
    assert "approved" in capsys.readouterr().out
