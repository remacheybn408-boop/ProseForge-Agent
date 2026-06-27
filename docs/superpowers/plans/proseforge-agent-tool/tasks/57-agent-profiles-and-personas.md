# Task 57: Agent Profiles And Personas

## Goal

Support user-selectable agent profiles for professional writing, editing, operator help, and general chat.

## Agent Product Requirement

The agent should feel coherent in conversation without mixing roles or permissions.

## Architecture Notes

`agent.profiles` defines named profiles that preset a coherent bundle: default chat mode, tone, provider role preferences, memory scope, permission ceiling, and prompt pack reference. A profile is configuration consumed by the Agent Kernel (Task 31) and prompt protocol (Task 36); it executes nothing itself. A profile may lower but never raise the permission ceiling beyond what config/flags allow, so personas cannot escalate privileges.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/08-agent-runtime-and-chat.md (Product Modes, Permissions)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/profiles.py`
- Create `tests/test_agent_profiles_personas.py`
- Create `tests/fixtures/agent-profiles-and-personas/profiles.yaml`

## Interfaces / Contracts

- `AgentProfileRegistry.default(name) -> AgentProfile` for built-in profiles `writer`, `editor`, `operator`, `general`.
- `AgentProfile` fields: `name`, `mode`, `tone`, `provider_roles`, `memory_scope`, `permission_ceiling`, `prompt_pack`.
- `permission_ceiling` is clamped to the session's allowed maximum; a profile never raises it.
- Unknown profile name raises `ConfigurationError`.

## Data Flow

1. Load built-in and user-defined profiles.
2. Resolve the requested profile by name.
3. Clamp its permission ceiling to the session maximum.
4. Provide mode, tone, roles, and prompt-pack reference to the kernel.
5. Return the resolved `AgentProfile`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_agent_profiles_personas.py::test_writer_profile_presets_mode_roles_and_clamped_ceiling`**

```python
def test_writer_profile_presets_mode_roles_and_clamped_ceiling():
    profile = AgentProfileRegistry.default("writer")
    assert profile.mode == "project_chat"
    assert profile.provider_roles  # e.g. drafter/reviewer roles
    assert profile.permission_ceiling in {"read_only", "draft_write", "project_write"}
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_agent_profiles_personas.py::test_writer_profile_presets_mode_roles_and_clamped_ceiling -q
```

Expected: FAIL because `AgentProfileRegistry` and `AgentProfile` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `AgentProfileRegistry`, `AgentProfile`, built-in profiles, and ceiling clamping.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_agent_profiles_personas.py::test_writer_profile_presets_mode_roles_and_clamped_ceiling -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_profile_cannot_raise_permission_above_session_maximum
test_operator_profile_defaults_to_operator_chat_mode
test_unknown_profile_raises_configuration_error
test_user_defined_profile_overrides_builtin_by_name
test_profile_tone_supports_utf8_chinese_text
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_agent_profiles_personas.py -q
pf-agent chat --message "你好" --profile writer --provider fake
```

Expected: tests pass and chat adopts the writer profile's mode and tone without escalating permissions.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_agent_profiles_personas.py -q
```

Expected: PASS for the simulated profile-loading cases in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/profiles.py tests/test_agent_profiles_personas.py tests/fixtures/agent-profiles-and-personas
git commit -m "feat: add agent profiles personas"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Profiles are YAML/data, no platform-specific paths.
- Tone and persona text are UTF-8 and round-trip Chinese.
- Built-in profiles need no machine-specific configuration.

## Failure Modes To Prove

- A profile cannot raise the permission ceiling above the session maximum.
- Unknown profile name raises `ConfigurationError`.
- A user-defined profile overrides a built-in of the same name predictably.
- Profiles execute nothing on their own.

## Verification

```powershell
python -m pytest tests/test_agent_profiles_personas.py -q
pf-agent chat --message "你好" --profile writer --provider fake
```

## Acceptance

- Built-in writer/editor/operator/general profiles exist.
- Profiles preset mode, tone, roles, memory scope, and ceiling.
- Profiles cannot escalate permissions.
- User-defined profiles are supported.

## Commit Boundary

Commit only profile files and tests after verification passes. Do not add kernel execution logic here.
