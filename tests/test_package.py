from proseforge_agent import __version__
from proseforge_agent.errors import ConfigurationError, ProseForgeAgentError


def test_package_exposes_version_and_errors():
    assert __version__ == "0.1.0"
    assert issubclass(ConfigurationError, ProseForgeAgentError)
