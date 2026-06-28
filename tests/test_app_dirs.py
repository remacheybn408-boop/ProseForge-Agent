import json
from pathlib import Path

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.app_dirs import AppDirs


FIXTURE = Path(__file__).parent / "fixtures" / "cross-platform-app-directories" / "expected_paths.json"


def test_windows_uses_appdata_for_config_and_localappdata_for_data():
    dirs = AppDirs.for_platform(
        "windows",
        {"APPDATA": "C:/Users/A/AppData/Roaming", "LOCALAPPDATA": "C:/Users/A/AppData/Local"},
    )
    assert dirs.config_dir == Path("C:/Users/A/AppData/Roaming/ProseForge Agent")
    assert dirs.data_dir == Path("C:/Users/A/AppData/Local/ProseForge Agent")


def test_macos_uses_application_support_and_library_caches():
    dirs = AppDirs.for_platform("macos", {"HOME": "/Users/alice"})
    assert dirs.config_dir == Path("/Users/alice/Library/Application Support/ProseForge Agent")
    assert dirs.cache_dir == Path("/Users/alice/Library/Caches/ProseForge Agent")


def test_linux_honours_xdg_overrides():
    dirs = AppDirs.for_platform(
        "linux",
        {
            "HOME": "/home/alice",
            "XDG_CONFIG_HOME": "/cfg",
            "XDG_DATA_HOME": "/data",
            "XDG_CACHE_HOME": "/cache",
            "XDG_STATE_HOME": "/state",
        },
    )
    assert dirs.config_dir == Path("/cfg/proseforge-agent")
    assert dirs.log_dir == Path("/state/proseforge-agent/logs")


def test_portable_mode_roots_everything_under_pf_agent():
    dirs = AppDirs.for_platform("windows", {"HOME": "C:/Users/A"}, portable=True)
    assert dirs.config_dir == Path(".pf-agent/config")
    assert dirs.data_dir == Path(".pf-agent/data")
    assert dirs.cache_dir == Path(".pf-agent/cache")
    assert dirs.log_dir == Path(".pf-agent/logs")


def test_missing_home_raises_configuration_error():
    with pytest.raises(ConfigurationError):
        AppDirs.for_platform("linux", {})


def test_resolved_paths_preserve_utf8_user_names():
    dirs = AppDirs.for_platform("linux", {"HOME": "/home/作者"})
    assert "作者" in str(dirs.config_dir)


def test_expected_paths_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["portable"]["config_dir"] == ".pf-agent/config"
