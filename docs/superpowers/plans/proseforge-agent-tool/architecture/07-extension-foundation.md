# Extension Foundation

## Goal

Make future expansion cheap. New providers, retrievers, workflow steps, renderers, and templates should be registered rather than hard-wired into every subsystem.

## Extension Categories

- `provider`
- `workflow_step`
- `retriever`
- `memory_classifier`
- `report_renderer`
- `template_loader`
- `guard_bridge`
- `host_surface`

## Registry Shape

```python
registry.register("provider", "fake", lambda spec: FakeProvider(...))
registry.register("workflow_step", "chapter_pre", ChapterPreStep)
registry.register("report_renderer", "markdown", MarkdownRenderer)
```

## First Release Extension API

```python
class WorkflowStep(Protocol):
    name: str

    def run(self, context: dict) -> dict:
        ...


class Retriever(Protocol):
    name: str

    def search(self, query: str, context: dict) -> list[dict]:
        ...


class ReportRenderer(Protocol):
    name: str

    def render(self, payload: dict) -> str:
        ...
```

## Plugin Readiness

The first release does not need to ship a full Codex plugin, but it must keep command contracts plugin-friendly:

- Commands return JSON when `--json` is passed.
- Commands write artifacts to predictable paths.
- Commands accept explicit config path.
- Commands accept explicit project slug.
- Commands avoid interactive prompts.

## Acceptance Criteria

- `ExtensionRegistry.register()` stores factories by category and name.
- `ExtensionRegistry.get()` retrieves a factory.
- `ExtensionRegistry.names()` lists registered names.
- Tests prove providers can be registered without editing workflow code.
