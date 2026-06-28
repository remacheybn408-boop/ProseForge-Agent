# Developer Guide — Writing Extensions

Extensions let you add providers, prompts, memory backends, gates, and more
**without modifying the core**. They are opt-in, versioned, and isolated: a
failing extension is disabled and its error recorded, never crashing an
unrelated command.

## Extension points

An extension declares the points it implements via its `capabilities`:

| Point | Purpose |
| --- | --- |
| `provider` | A model provider implementation |
| `memory_backend` | An alternative durable memory store |
| `retriever` | A retrieval/index strategy |
| `workflow_step` | A custom step in a workflow |
| `report_renderer` | An additional report output format |
| `gate` | A quality gate over chapter text |
| `prompt_pack` | A bundle of role prompts |
| `market_analyzer` | Market-fit analysis |
| `export_target` | An export destination/format |

## Contract

Every extension is an `Extension` (see
`src/proseforge_agent/extensions/base.py`):

```python
@dataclass
class Extension:
    id: str
    version: str = "0.1.0"
    compatible_agent_range: str = "*"   # version range, see below
    capabilities: tuple[str, ...] = ()  # subset of the extension points
    enabled: bool = True
```

### Compatibility ranges

`compatible_agent_range` is a comma-separated list of clauses. Each clause is an
optional comparator (`>=`, `<=`, `==`, `>`, `<`; default `>=`) plus a dotted
version. Empty, `*`, or `any` matches every agent version.

```
">=0.1.0"          # 0.1.0 and newer
">=0.1,<1.0"       # 0.1.x up to but not including 1.0
"*"                # any version
```

Registering an extension whose range excludes the running agent version raises
`ExtensionError` (the message contains "not compatible"). Declaring an unknown
extension point, or a duplicate id, also raises `ExtensionError`.

## Error isolation

Call extension behavior through the registry's `safe_invoke`:

```python
result = registry.safe_invoke(extension, "evaluate", text)
```

If the extension raises, `safe_invoke` returns `None`, disables that extension,
and records the reason in `registry.errors()`. Other extensions and commands are
unaffected.

## Discovery

The registry loads an extension from a module file that exposes a top-level
`EXTENSION` instance:

```python
registry = ExtensionRegistry(agent_version="0.1.0")
extension = registry.load_module("samples/extensions/sample_gate.py")
registry.register(extension)
```

## Worked example

`samples/extensions/sample_gate.py` is a complete, deterministic gate extension:

```python
from proseforge_agent.extensions.base import GateExtension

@dataclass
class SampleGate(GateExtension):
    def evaluate(self, text: str) -> dict:
        if not text.strip():
            return {"gate": self.id, "passed": False, "detail": "draft is empty"}
        if "TODO" in text:
            return {"gate": self.id, "passed": False, "detail": "draft has a TODO"}
        return {"gate": self.id, "passed": True, "detail": "no blocking issues"}

EXTENSION = SampleGate(
    id="sample_gate",
    compatible_agent_range=">=0.1.0",
    capabilities=("gate",),
)
```

It is validated by `tests/test_extensions.py`. Copy it as your starting point.
