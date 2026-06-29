"""Tests for the cross-platform CI pipeline validator (Task 64)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.ci_matrix import CIWorkflow
from proseforge_agent.install.qa_matrix import NativeQAMatrix

WORKFLOW_PATH = Path(".github/workflows/ci.yml")
FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "cross-platform-ci-pipeline"
    / "expected_matrix.json"
)

_MISSING_MACOS = """
name: CI
on: [push]
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.10"]
    steps:
      - run: pip install -e .
      - run: python -m pytest -q
"""


def test_ci_matrix_covers_three_operating_systems():
    matrix = CIWorkflow.load(WORKFLOW_PATH).matrix()
    os_axis = " ".join(matrix["os"]).lower()
    assert "windows" in os_axis
    assert "macos" in os_axis
    assert "ubuntu" in os_axis


def test_workflow_has_a_pytest_step():
    assert CIWorkflow.load(WORKFLOW_PATH).has_pytest_step() is True


def test_python_version_axis_includes_minimum_supported():
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    matrix = CIWorkflow.load(WORKFLOW_PATH).matrix()
    assert expected["minimum_python"] in matrix["python-version"]


def test_validate_against_qa_matrix_flags_missing_os():
    workflow = CIWorkflow.from_text(_MISSING_MACOS)
    with pytest.raises(ConfigurationError):
        workflow.validate_against_qa_matrix(NativeQAMatrix())


def test_validate_against_qa_matrix_passes_for_full_matrix():
    workflow = CIWorkflow.load(WORKFLOW_PATH)
    # Should not raise: the real workflow covers all required platforms.
    workflow.validate_against_qa_matrix(NativeQAMatrix())


def test_workflow_installs_package_before_tests():
    assert CIWorkflow.load(WORKFLOW_PATH).installs_package_before_tests() is True


def test_workflow_file_is_valid_yaml():
    loaded = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    assert "jobs" in loaded
