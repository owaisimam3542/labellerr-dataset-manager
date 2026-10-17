import pytest
from src.config import Settings, ConfigurationError


def test_missing_environment_variable():
    with pytest.raises(ConfigurationError, match="LABELLERR_API_KEY"):
        Settings.from_env({"LABELLERR_API_SECRET": "secret", "LABELLERR_CLIENT_ID": "client"})


def test_settings_load_successfully():
    settings = Settings.from_env({"LABELLERR_API_KEY": "key", "LABELLERR_API_SECRET": "secret", "LABELLERR_CLIENT_ID": "client"})
    assert settings.api_key == "key"
    assert settings.client_id == "client"
