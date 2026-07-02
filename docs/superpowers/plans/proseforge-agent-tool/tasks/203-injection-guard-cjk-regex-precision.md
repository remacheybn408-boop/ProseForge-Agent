# Task 203: InjectionGuard CJK Regex Precision / 注入护栏中文正则精修

## Goal

Stop the `InjectionGuard` from flagging ordinary Chinese novel prose as a tool
-invocation injection. `agent/safety.py:57` has a bare pattern
`re.compile(r"(现在)?(执行|运行|调用|启动)")` with no word boundary and no tool
token — any sentence using 执行/运行/调用/启动 as an ordinary verb matches
(extremely common in fiction: "主角**执行**了命令", "计划**启动**了", "系统
**运行**中"). When such content enters as `provenance="untrusted"` (attachment
ingestion, workbook seeding), the guard forces `allowed_ceiling` down to
`read_only` and silently denies legitimate writes for the whole turn.

## Architecture Notes

Fixes **finding 1.2** (Medium · Security-Robustness) of
`docs/review/core-review-2026-07-01.md`.

Verified: `_TOOL_INVOCATION_PATTERNS` already contains the **correct** precise
patterns:

- line 54: `\b(run|execute|invoke|call|trigger|start)\s+[a-z_]+\.[a-z_]+`
- line 55: `(执行|运行|调用|启动|触发)\s*[a-z_]+\.[a-z_]+`

The offending line 57 `(现在)?(执行|运行|调用|启动)` is redundant with line 55
but drops the required dotted tool token — that is the false-positive source.

Design:

- **Remove** the bare line-57 pattern (line 55 already covers the legitimate
  "verb + `tool.name`" case), OR replace it with one that requires a dotted
  tool token / explicit tool context to co-occur.
- Do not weaken detection of real invocations: `执行 fs.write(...)`,
  `运行 workflow.start`, and the English equivalents must still flag.
- Add a false-positive regression test with **≥3 novel-prose samples** and a
  true-positive test proving real tool invocations still flag.

Read before starting:

- `docs/review/core-review-2026-07-01.md` (finding 1.2)
- 66-agent-safety-and-prompt-injection-guards.md (or the safety card)
- `src/proseforge_agent/agent/safety.py`

## Files

- Modify `src/proseforge_agent/agent/safety.py` (`_TOOL_INVOCATION_PATTERNS`).
- Add tests in `tests/test_injection_guard_cjk_precision.py`.

## Interfaces / Contracts

- Untrusted content containing 执行/运行/调用/启动 as ordinary verbs (no dotted
  tool token) does NOT lower `allowed_ceiling` to `read_only`.
- Untrusted content with a real dotted tool invocation still flags and lowers
  the ceiling.

## Data Flow

1. Attachment ingestion emits chapter prose as `provenance="untrusted"`.
2. `InjectionGuard.assess(...)` → no tool-invocation flag for ordinary verbs.
3. A subsequent `draft_write` is allowed (not silently denied).

## TDD Steps

- [ ] **Step 1: Write failing test
  `tests/test_injection_guard_cjk_precision.py::test_novel_prose_verbs_do_not_flag`**

```python
@pytest.mark.parametrize("prose", [
    "主角执行了上级的命令，然后转身离开。",
    "作战计划启动了，全军开始推进。",
    "系统在后台安静地运行中，没有异常。",
])
def test_novel_prose_verbs_do_not_flag(prose):
    verdict = InjectionGuard().assess(prose, provenance="untrusted")
    assert "tool_invocation" not in verdict.flags
    assert verdict.allowed_ceiling != "read_only"
```

- [ ] **Step 2: Run the targeted test and confirm failure** (line-57 pattern
  matches 执行/启动/运行 and lowers the ceiling).

- [ ] **Step 3: Remove/replace the bare CJK pattern so a dotted tool token is
  required.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Companion tests**

```text
test_real_cjk_tool_invocation_still_flags          # "执行 fs.write(...)" flags
test_real_english_tool_invocation_still_flags      # "run workflow.start" flags
test_accept_all_chapters_patterns_unchanged        # 接受所有章节 still flags
test_existing_injection_patterns_unaffected        # 忽略以上指令 etc still flag
```

- [ ] **Step 6: Subsystem verification**

```powershell
python -m pytest tests/test_injection_guard_cjk_precision.py tests/test_agent_safety*.py -q
```

- [ ] **Step 7: Full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Commit boundary**

```powershell
git add src/proseforge_agent/agent/safety.py tests/test_injection_guard_cjk_precision.py
git commit -m "fix: require tool token in injection guard cjk pattern"
```

## Failure Modes To Prove

- Three distinct novel-prose sentences with 执行/启动/运行 do not flag.
- `执行 fs.write(...)` and `run workflow.start` still flag.
- Other injection patterns (忽略以上指令, 接受所有章节) are unaffected.

## Verification

```powershell
python -m pytest tests/test_injection_guard_cjk_precision.py -q
python -m pytest -q
```

## Acceptance

- Ordinary Chinese verbs no longer trigger the tool-invocation guard; real
  invocations still flag; full suite green; new tests added.

## Commit Boundary

Commit only the safety-pattern change and its tests.

---

## Deferred Low-Severity Findings (not carded)

The 2026-07-01 core review also recorded lower-severity items **intentionally
left out of cards 196–203**. Track them here; fold into a future cleanup card
if desired:

- **1.3** `Sandbox._preflight` conflates "insufficient permission" and
  "approval missing" into one `error="approval required"` — split the machine
  field.
- **2.3** `FileLock` silently degrades to a no-op when neither `fcntl` nor
  `msvcrt` is importable — raise or warn once.
- **2.4** `with_sqlite_retry` matches the literal `"database is locked"` string
  — prefer `sqlite_errorcode == SQLITE_BUSY` with the string as fallback.
- **3.4** `release.publish._redact_argv` does not redact — rename to
  `_format_argv` or implement real redaction.
- **7.1** Add `from __future__ import annotations` to `agent/modes.py` and
  `errors.py`; document the intentional `agent ↔ chat.transcript` cycle.

**Un-reviewed subsystems** (no card, candidate for a future deep-review pass):
`retrieval/*`, `plugins/*`, `notifications/*`, `service/*`, `skills/*`,
`tui/*`, `tools/*` (169–174), `novel/*`, most of `llm/*`, and `cli.py` depth.
