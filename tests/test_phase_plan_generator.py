from pathlib import Path

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.llm import FakeProvider
from proseforge_agent.llm.base import ProviderResult, Usage
from proseforge_agent.memory import MemoryItem, MemoryStore
from proseforge_agent.planning import (
    PhasePlanGenerator,
    ProjectIntake,
    load_intake,
)

FIXTURE = Path(__file__).parent / "fixtures" / "planning" / "intake.yaml"


class StubProvider:
    """Provider stub that returns a fixed text payload."""

    def __init__(self, text):
        self.name = "stub"
        self.model = "stub-model"
        self._text = text

    def generate(self, request):
        return ProviderResult(
            provider=self.name, model=self.model, text=self._text, usage=Usage()
        )

    def generate_stream(self, request):  # pragma: no cover - unused
        yield from ()


@pytest.fixture
def fake_provider():
    return FakeProvider(name="fake", model="fake-planner")


@pytest.fixture
def memory_store(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    store.add(MemoryItem(project_slug="demo", type="canon_fact", text="World has two moons.", source="bible:1"))
    store.add(MemoryItem(project_slug="demo", type="reader_promise", text="The throne is reclaimed.", source="outline:1"))
    return store


def _intake():
    return ProjectIntake(slug="demo", title="Demo", genre="fantasy", target_chapters=12)


def test_phase_plan_contains_gates_and_chapter_ranges(fake_provider, memory_store):
    plan = PhasePlanGenerator(fake_provider, memory_store).generate(
        ProjectIntake(slug="demo", title="Demo", genre="fantasy", target_chapters=12)
    )
    assert plan.volumes[0].chapter_start == 1
    assert plan.acceptance_gates
    assert plan.source_references is not None


def test_volumes_are_contiguous_and_cover_all_chapters(fake_provider, memory_store):
    plan = PhasePlanGenerator(fake_provider, memory_store).generate(
        ProjectIntake(slug="demo", title="Demo", genre="fantasy", target_chapters=30)
    )
    assert len(plan.volumes) > 1
    for prev, nxt in zip(plan.volumes, plan.volumes[1:]):
        assert nxt.chapter_start == prev.chapter_end + 1
    assert plan.volumes[-1].chapter_end == 30


def test_plan_has_deliverables_and_gates(fake_provider, memory_store):
    plan = PhasePlanGenerator(fake_provider, memory_store).generate(_intake())
    assert plan.deliverables
    assert plan.acceptance_gates
    assert all(v.deliverables for v in plan.volumes)


def test_source_references_cite_intake_and_memory(fake_provider, memory_store):
    plan = PhasePlanGenerator(fake_provider, memory_store).generate(_intake())
    assert "intake:demo" in plan.source_references
    assert any("bible:1" == ref or "outline:1" == ref for ref in plan.source_references)


def test_invalid_intake_rejected(fake_provider, memory_store):
    with pytest.raises(ConfigurationError):
        PhasePlanGenerator(fake_provider, memory_store).generate(
            ProjectIntake(slug="demo", title="Demo", genre="fantasy", target_chapters=0)
        )


def test_invalid_model_output_rejected_with_parse_report(memory_store):
    gen = PhasePlanGenerator(StubProvider("not json"), memory_store)
    plan = gen.generate(_intake())
    assert plan.parse_report.ok is False
    assert plan.parse_report.reasons
    assert plan.volumes  # structure still complete


def test_valid_model_output_enriches_theme(memory_store):
    gen = PhasePlanGenerator(
        StubProvider('{"volumes": [{"theme": "血海沉冤"}]}'), memory_store
    )
    plan = gen.generate(_intake())
    assert plan.parse_report.ok is True
    assert plan.volumes[0].theme == "血海沉冤"


def test_load_intake_fixture():
    intake = load_intake(FIXTURE)
    assert intake.slug
    assert intake.target_chapters > 0


def test_render_markdown_lists_volumes_and_sources(fake_provider, memory_store):
    gen = PhasePlanGenerator(fake_provider, memory_store)
    plan = gen.generate(_intake())
    md = gen.render_markdown(plan)
    assert "intake:demo" in md
    assert "Volume" in md
