"""Unit tests for configuration providers.

Tests verify:
1. Config loading from JSON files
2. Field validation
3. Value retrieval
4. Error handling
5. SessionFactory and ExporterFactory integration
"""
from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch

from bda.application.interfaces.config.i_config_provider import (
    IConfigProvider,
)
from bda.config.global_config import GlobalConfig

from bda.infrastructure.adapters.analytical_software.config_providers.csi_config_provider import CSIBridgeConfigProvider
from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider
from bda.infrastructure.adapters.analytical_software.exporters.exporter_factory import ExporterFactory
from bda.infrastructure.adapters.analytical_software.session_managers.session_factory import SessionFactory
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession
from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession
from bda.domain.enums import OutputSoftware


@pytest.fixture(scope="session", autouse=True)
def setup_global_config():
    GlobalConfig.reset()
    config_path = Path(__file__).parent / "fixtures" / "appsettings_tests.json"
    config_path = config_path.resolve()

    GlobalConfig(appsettings_path=str(config_path))


class TestMidasConfigProvider:
    """Test suite for MidasConfigProvider."""

    def test_loads_config_successfully(self):
        """Test that MIDAS config is loaded without errors."""
        provider = MidasConfigProvider()
        config = provider.load_config()

        assert isinstance(config, dict)
        assert len(config) > 0

    def test_has_required_fields(self):
        """Test that MIDAS config has all required fields."""
        provider = MidasConfigProvider()
        config = provider.load_config()

        assert "base_url" in config
        assert "mapi_key" in config
        assert "program_path" in config

    def test_get_config_value(self):
        """Test retrieving specific config values."""
        provider = MidasConfigProvider()

        base_url = provider.get_config_value("base_url")
        assert base_url is not None
        assert isinstance(base_url, str)
        assert "midas" in base_url.lower() or "moa" in base_url.lower()

        mapi_key = provider.get_config_value("mapi_key")
        assert mapi_key is not None
        assert isinstance(mapi_key, str)

        program_path = provider.get_config_value("program_path")
        assert program_path is not None
        assert "CVLw.exe" in program_path

    def test_get_nonexistent_field_returns_default(self):
        """Test that accessing non-existent field returns default value."""
        provider = MidasConfigProvider()

        result = provider.get_config_value("nonexistent_field", default="default_value")
        assert result == "default_value"

        result = provider.get_config_value("nonexistent_field")
        assert result is None


class TestCSIBridgeConfigProvider:
    """Test suite for CSIBridgeConfigProvider."""

    def test_loads_config_successfully(self):
        """Test that CSI Bridge config is loaded without errors."""
        provider = CSIBridgeConfigProvider()
        config = provider.load_config()

        assert isinstance(config, dict)
        assert len(config) > 0

    def test_has_required_fields(self):
        """Test that CSI Bridge config has all required fields."""
        provider = CSIBridgeConfigProvider()
        config = provider.load_config()

        assert "helper_object" in config
        assert "program_id" in config
        assert "program_path" in config

    def test_has_optional_fields(self):
        """Test that CSI Bridge config has optional fields."""
        provider = CSIBridgeConfigProvider()
        config = provider.load_config()

        # These are optional but should be present in our config
        assert "headless_mode" in config
        assert "attach_to_instance_by_default" in config

    def test_get_config_value(self):
        """Test retrieving specific config values."""
        provider = CSIBridgeConfigProvider()

        helper_object = provider.get_config_value("helper_object")
        assert helper_object is not None
        assert "Helper" in helper_object

        program_id = provider.get_config_value("program_id")
        assert program_id is not None
        assert "CSI" in program_id

        program_path = provider.get_config_value("program_path")
        assert program_path is not None
        assert "CSiBridge" in program_path

        headless_mode = provider.get_config_value("headless_mode")
        assert isinstance(headless_mode, bool)

        attach_by_default = provider.get_config_value("attach_to_instance_by_default")
        assert isinstance(attach_by_default, bool)

    def test_get_optional_field_with_default(self):
        """Test getting optional field with default value."""
        provider = CSIBridgeConfigProvider()

        # Field exists, should return actual value
        result = provider.get_config_value("headless_mode", default=True)
        assert isinstance(result, bool)

        # Non-existent field with default
        result = provider.get_config_value("nonexistent", default=True)
        assert result is True


class TestFactoriesWithConfig:
    """Test suite for session_manager and exporter factories with config injection."""

    @pytest.fixture
    def mock_csi_initialization(self):
        """Mock CSI Bridge initialization to avoid COM errors."""
        with patch("bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session.comtypes.client.CreateObject") as mock_create, \
             patch("bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session.comtypes.gen") as mock_gen:

            mock_helper = MagicMock()
            mock_sap_object = MagicMock()
            mock_sap_model = MagicMock()

            # Setup mock chain
            mock_helper_interface = MagicMock()
            mock_helper.QueryInterface.return_value = mock_helper_interface
            mock_create.return_value = mock_helper
            mock_gen.CSiBridge1.cHelper = MagicMock()

            # Setup SAP object hierarchy
            mock_sap_object.SapModel = mock_sap_model
            mock_sap_model.BridgeModeler_1 = MagicMock()
            mock_sap_model.InitializeNewModel.return_value = 0
            mock_sap_model.File.NewBlank.return_value = 0

            mock_helper_interface.GetObject.return_value = mock_sap_object
            mock_helper_interface.CreateObjectProgID.return_value = mock_sap_object

            yield

    def test_session_factory_builds_csi_session(self, mock_csi_initialization):
        session = SessionFactory.get_session(OutputSoftware.CSIBRIDGE)
        assert isinstance(session, CSIBridgeSession)
        assert session.software_name == "CSI Bridge"
        assert isinstance(session.config, CSIBridgeConfigProvider)

    def test_session_factory_builds_midas_session(self):
        session = SessionFactory.get_session(OutputSoftware.MIDAS)
        assert isinstance(session, MidasCivilSession)
        assert session.software_name == "MIDAS Civil"
        assert isinstance(session.base_url, str)
        assert isinstance(session.mapi_key, str)
        assert isinstance(session.program_path, str)

    def test_exporter_factory_uses_session(self, mock_csi_initialization):
        session = SessionFactory.get_session(OutputSoftware.CSIBRIDGE)
        exporter = ExporterFactory.get_exporter(OutputSoftware.CSIBRIDGE, session)
        assert exporter.software_name == "CSI Bridge"


class TestJsonConfigProviderInterface:
    """Test that providers implement IExporterConfigProvider correctly."""

    def test_midas_provider_implements_interface(self):
        """Test that MidasConfigProvider is instance of IExporterConfigProvider."""
        provider = MidasConfigProvider()
        assert isinstance(provider, IConfigProvider)

    def test_csi_provider_implements_interface(self):
        """Test that CSIBridgeConfigProvider is instance of IExporterConfigProvider."""
        provider = CSIBridgeConfigProvider()
        assert isinstance(provider, IConfigProvider)

    def test_interface_methods_exist(self):
        """Test that both providers have required interface methods."""
        midas_provider = MidasConfigProvider()
        csi_provider = CSIBridgeConfigProvider()

        for provider in [midas_provider, csi_provider]:
            assert callable(getattr(provider, "load_config"))
            assert callable(getattr(provider, "get_config_value"))

