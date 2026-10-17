import sys
from types import ModuleType, SimpleNamespace

import pytest

from src.config import Settings, ConfigurationError
from src.client import LabellerrGateway, SDKIntegrationError


def test_missing_environment_variable():
    with pytest.raises(ConfigurationError, match="LABELLERR_API_KEY"):
        Settings.from_env({
            "LABELLERR_API_SECRET": "secret",
            "LABELLERR_CLIENT_ID": "client",
        })


def test_settings_load_successfully():
    settings = Settings.from_env({
        "LABELLERR_API_KEY": "key",
        "LABELLERR_API_SECRET": "secret",
        "LABELLERR_CLIENT_ID": "client",
    })
    assert settings.api_key == "key"
    assert settings.client_id == "client"


def test_sdk_client_initialization_success(monkeypatch):
    expected_client = object()
    received = {}

    def fake_client(**kwargs):
        received.update(kwargs)
        return expected_client

    labellerr_module = ModuleType("labellerr")
    core_module = ModuleType("labellerr.core")
    core_module.LabellerrClient = fake_client
    labellerr_module.core = core_module

    monkeypatch.setitem(sys.modules, "labellerr", labellerr_module)
    monkeypatch.setitem(sys.modules, "labellerr.core", core_module)

    settings = Settings.from_env({
        "LABELLERR_API_KEY": "test-key",
        "LABELLERR_API_SECRET": "test-secret",
        "LABELLERR_CLIENT_ID": "test-client",
    })

    gateway = LabellerrGateway.from_settings(settings)

    assert gateway.client is expected_client
    assert received == {
        "api_key": "test-key",
        "api_secret": "test-secret",
        "client_id": "test-client",
    }


def test_sdk_client_initialization_failure_is_friendly(monkeypatch):
    def failing_client(**kwargs):
        raise RuntimeError("internal SDK details")

    labellerr_module = ModuleType("labellerr")
    core_module = ModuleType("labellerr.core")
    core_module.LabellerrClient = failing_client
    labellerr_module.core = core_module

    monkeypatch.setitem(sys.modules, "labellerr", labellerr_module)
    monkeypatch.setitem(sys.modules, "labellerr.core", core_module)

    settings = Settings.from_env({
        "LABELLERR_API_KEY": "test-key",
        "LABELLERR_API_SECRET": "test-secret",
        "LABELLERR_CLIENT_ID": "test-client",
    })

    with pytest.raises(
        SDKIntegrationError,
        match="Labellerr client initialization failed",
    ) as exc_info:
        LabellerrGateway.from_settings(settings)

    assert "internal SDK details" not in str(exc_info.value)