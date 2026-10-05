"""Unit tests for exporter implementations."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bda.config.global_config import GlobalConfig
from bda.domain import AnalyticalMultiModel
from bda.domain.enums import OutputSoftware, UnitSystem
from bda.infrastructure.adapters.analytical_software.exporters.csi_bridge_exporter import CSIBridgeExporter
from bda.infrastructure.adapters.analytical_software.exporters.exporter_factory import ExporterFactory
from bda.infrastructure.adapters.analytical_software.exporters.midas_civil_exporter import MidasCivilExporter
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession
from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession
from bda.infrastructure.adapters.analytical_software.session_managers.session_factory import SessionFactory


@pytest.fixture(scope="session", autouse=True)
def setup_global_config():
    GlobalConfig.reset()
    config_path = Path(__file__).parent / "fixtures" / "appsettings_tests.json"
    config_path = config_path.resolve()

    GlobalConfig(appsettings_path=str(config_path))


@pytest.fixture
def simple_model() -> AnalyticalMultiModel:
    return AnalyticalMultiModel(
        project_id=1,
        structure_id=1,
        structure_name="Test Bridge",
        description="Test structure",
        unit_system=UnitSystem.SI,
    )


@pytest.fixture
def csi_session():
    with patch(
        "bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session.comtypes.client.CreateObject"
    ) as mock_create, patch(
        "bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session.comtypes.gen"
    ) as mock_gen:
        from bda.infrastructure.adapters.analytical_software.config_providers.csi_config_provider import \
            CSIBridgeConfigProvider

        mock_helper = MagicMock()
        mock_helper_interface = MagicMock()
        mock_sap_object = MagicMock()
        mock_sap_model = MagicMock()

        mock_helper.QueryInterface.return_value = mock_helper_interface
        mock_create.return_value = mock_helper
        mock_gen.CSiBridge1.cHelper = MagicMock()

        mock_sap_object.SapModel = mock_sap_model
        mock_sap_model.BridgeModeler_1 = MagicMock()
        mock_sap_model.InitializeNewModel.return_value = 0
        mock_sap_model.File.NewBlank.return_value = 0
        mock_sap_model.File.OpenFile.return_value = 0
        mock_sap_model.File.Save.return_value = 0
        mock_sap_model.SetPresentUnits.return_value = 0

        mock_helper_interface.GetObject.return_value = mock_sap_object
        mock_helper_interface.CreateObjectProgID.return_value = mock_sap_object

        CSIBridgeConfigProvider = MagicMock()
        CSIBridgeConfigProvider.return_value.helper_object.return_value = "helper_object"
        CSIBridgeConfigProvider.return_value.program_id.return_value = "program_id"
        CSIBridgeConfigProvider.return_value.program_path.return_value = "program_path"
        CSIBridgeConfigProvider.return_value.headless_mode.return_value = False

        session = CSIBridgeSession(CSIBridgeConfigProvider())
        session.open_session(create_new_instance=True, template_file_path=None)
        yield session
        session.close_session()


@pytest.fixture
def midas_session():
    with patch(
        "bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session.MidasAPI"
    ) as mock_api, patch(
        "bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session.Path.exists",
        return_value=True,
    ), patch(
        "bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session.subprocess.Popen"
    ) as mock_popen, patch.object(
        MidasCivilSession, "_initialize_api", return_value=None
    ):
        from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import (
            MidasConfigProvider,
        )

        process = MagicMock()
        process.poll.return_value = None
        process.wait.return_value = None
        process.pid = 1234
        mock_popen.return_value = process

        response = MagicMock()
        response.status_code = 200
        mock_api.return_value.request.return_value = response

        MidasConfigProvider = MagicMock()
        MidasConfigProvider.return_value.base_url.return_value = "http://example.com"
        MidasConfigProvider.return_value.mapi_key.return_value = "mapi.key"
        MidasConfigProvider.return_value.program_path.return_value = "C:\\temp"

        session = MidasCivilSession(MidasConfigProvider)
        session.open_session(create_new_instance=True, template_file_path=None)
        yield session
        session.close_session()


class TestMidasCivilExporter:
    def test_exporter_initialization(self, midas_session):
        exporter = ExporterFactory.get_exporter(OutputSoftware.MIDAS, midas_session)
        assert isinstance(exporter, MidasCivilExporter)
        assert exporter.software_name == "MIDAS Civil"


class TestCSIBridgeExporter:
    def test_exporter_initialization(self, csi_session):
        exporter = ExporterFactory.get_exporter(OutputSoftware.CSIBRIDGE, csi_session)
        assert isinstance(exporter, CSIBridgeExporter)
        assert exporter.software_name == "CSI Bridge"

    def test_export_with_empty_model(self, csi_session, simple_model):
        exporter = ExporterFactory.get_exporter(OutputSoftware.CSIBRIDGE, csi_session)
        exporter.export(simple_model)

        assert csi_session.sap_model.File.Save.called, "The exported model has to be saved"

    def test_export_saves_model_when_orchestration_failed(self, csi_session, simple_model):
        """A failed export still has to save the model, so that it can be inspected."""
        exporter = ExporterFactory.get_exporter(OutputSoftware.CSIBRIDGE, csi_session)

        csi_session.sap_model.File.Save.reset_mock()
        csi_session.sap_model.SetPresentUnits.return_value = 1

        with pytest.raises(RuntimeError):
            exporter.export(simple_model)

        assert csi_session.sap_model.File.Save.called, \
            "The partially exported model has to be saved even when the export failed"


class TestFactories:
    def test_session_factory_returns_expected_types(self):
        with patch(
            "bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session.comtypes.client.CreateObject"
        ), patch("bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session.comtypes.gen"):
            csi = SessionFactory.get_session(OutputSoftware.CSIBRIDGE)
            assert isinstance(csi, CSIBridgeSession)

        midas = SessionFactory.get_session(OutputSoftware.MIDAS)
        assert isinstance(midas, MidasCivilSession)

    def test_exporter_factory_unsupported_software(self, csi_session):
        from enum import Enum

        class UnsupportedSoftware(str, Enum):
            UNKNOWN = "unknown"

        with pytest.raises(ValueError):
            ExporterFactory.get_exporter(UnsupportedSoftware.UNKNOWN, csi_session)  # type: ignore[arg-type]
