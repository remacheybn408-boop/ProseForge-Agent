# Task 199: Harden fs.edit + ToolRegistry Stubs / 加固 fs.edit 与工具注册表

## Goal

Two correctness/security fixes on the internal tool layer:

1. **`_fs_edit` empty-`old` prepend** — `fs.edit(path=…, old="", new=…)`
   currently succeeds and **prepends** `new` to the file, because `"" in text`
   is always `True` and `text.replace("", new, 1)` inserts at the head. Refuse
   empty `old`.
2. **`ToolRegistry` stub tools** — `default_tool_registry()` declares tools like
   `memory.search`, `workflow.start`, `chapter.run` whose `callable` is the
   stub `_ok(name)` returning `{"ok": True, …}` with no real work. Any caller
   that reaches `registry.invoke(name, …)` gets a NO-OP that looks like success.
   Either wire real callables or mark stubs `enabled=False` so `invoke` refuses.

## Architecture Notes

Fixes **findings 1.7** (High · Security) and **1.9** (High · Correctness) of
`docs/review/core-review-2026-07-01.md`. Ordering: land **after 196** — a wired
middleware could otherwise rewrite `arguments` to `old=""` and weaponize the
prepend.

Verified current code:

- `agent/tools.py:175` `_fs_edit`: reads file, `old = str(payload["old"])`,
  `if old not in text: return ok=False`, else
  `text.replace(old, new, 1)`. Empty `old` bypasses the not-found guard and
  prepends.
- `agent/tools.py:88` `ToolRegistry.invoke`: validates payload, calls
  `tool.invoke`. `AgentTool.enabled` exists (default `True`) but `invoke` does
  not check it. `_ok(name)` (line 122) is the stub factory.

Design:

1. In `_fs_edit`, first line after resolving the path:
   `if not old: return ToolResult(ok=False, error="old must be non-empty",
   provenance="workspace")`. (Do the check before reading/replacing.)
2. In `ToolRegistry.invoke`, refuse disabled tools:
   `if not tool.enabled: raise ConfigurationError(f"tool {name!r} is disabled")`
   (or return a structured error consistent with the surrounding contract).
3. For `default_tool_registry`: mark the stub-backed tools `enabled=False`
   (preferred, minimal, honest) OR wire thin delegates to the real CLI handler
   functions. Pick **`enabled=False`** for stubs that have no real
   implementation yet, and document that the CLI handlers are the real
   execution path. Keep genuinely-real tools (`fs.*`) `enabled=True`.

Read before starting:

- `docs/review/core-review-2026-07-01.md` (findings 1.7, 1.9; note 1.4)
- 71-agent-tools-and-workspace-containment.md (or the fs.* tool card)
- `src/proseforge_agent/agent/tools.py`

## Files

- Modify `src/proseforge_agent/agent/tools.py` (`_fs_edit` guard;
  `ToolRegistry.invoke` enabled check; `default_tool_registry` stub flags).
- Add tests in `tests/test_fs_edit_and_registry_hardening.py`.

## Interfaces / Contracts

- `fs.edit` with `old=""` returns `ToolResult(ok=False, error="old must be
  non-empty")` and does NOT modify the file.
- `ToolRegistry.invoke` on a disabled tool raises/returns a clear "disabled"
  error instead of executing the stub.
- Real tools (`fs.read/write/edit`) remain enabled and behave as before.

## Data Flow

1. A crafted/rewritten request reaches `fs.edit(old="")`.
2. `_fs_edit` returns `ok=False` before touching the file.
3. A caller does `registry.invoke("chapter.run", …)` on a stub → disabled
   error, not a false `{"ok": True}`.

## TDD Steps

- [ ] **Step 1: Write failing test
  `tests/test_fs_edit_and_registry_hardening.py::test_fs_edit_rejects_empty_old_without_modifying_file`**

```python
def test_fs_edit_rejects_empty_old_without_modifying_file(tmp_path):
    ctx = ToolContext(workspace_root=tmp_path, ...)
    target = tmp_path / "canon.md"
    target.write_text("ORIGINAL\n", encoding="utf-8")

    result = _fs_edit({"path": "canon.md", "old": "", "new": "<INJECTED>"}, ctx)

    assert result.ok is False
    assert "non-empty" in result.error
    assert target.read_text(encoding="utf-8") == "ORIGINAL\n"   # unchanged
```

- [ ] **Step 2: Run the targeted test and confirm failure** (today it prepends
  `<INJECTED>` and returns ok=True).

- [ ] **Step 3: Add the empty-`old` guard, the `enabled` check in `invoke`, and
  flag stub tools `enabled=False`.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Companion tests**

```text
test_registry_invoke_refuses_disabled_stub_tool
test_registry_invoke_still_runs_enabled_real_tool
test_default_registry_marks_stub_tools_disabled
test_fs_edit_still_replaces_when_old_is_present
```

- [ ] **Step 6: Subsystem verification**

```powershell
python -m pytest tests/test_fs_edit_and_registry_hardening.py tests/test_agent_tools*.py -q
```

- [ ] **Step 7: Full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Commit boundary**

```powershell
git add src/proseforge_agent/agent/tools.py tests/test_fs_edit_and_registry_hardening.py
git commit -m "fix: reject empty fs.edit old and disable stub tools"
```

## Failure Modes To Prove

- `fs.edit(old="")` never modifies a file.
- `registry.invoke` on a stub tool does not return a fake success.
- Enabled real tools and normal `fs.edit` replacements are unaffected.

## Verification

```powershell
python -m pytest tests/test_fs_edit_and_registry_hardening.py -q
python -m pytest -q
```

## Acceptance

- Empty-`old` `fs.edit` is refused with the file unchanged.
- Stub tools are `enabled=False` and `invoke` refuses them; real tools work.
- Full suite green; new tests added.

## Commit Boundary

Commit only the `tools.py` hardening and its tests. Do not bundle the middleware
wiring (196) or redaction (198) changes.
