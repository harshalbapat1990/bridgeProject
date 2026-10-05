"""
Integration tests for CSI Bridge exporter/session_manager wiring.

⚠️ Requires CSI Bridge installed locally. These tests are skipped automatically
when the configured installation path is unavailable.
"""

import os
from pathlib import Path

import pytest

from bda.config.global_config import GlobalConfig
from bda.domain import AnalyticalMultiModel
from bda.domain.enums import OutputSoftware, UnitSystem
from bda.infrastructure.adapters.analytical_software.config_providers.csi_config_provider import CSIBridgeConfigProvider
from bda.infrastructure.adapters.analytical_software.exporters.csi_bridge_exporter import CSIBridgeExporter
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession

@pytest.fixture(scope="session", autouse=True)
def setup_global_config():
    GlobalConfig.reset()
    GlobalConfig()

def _get_csi_installation_dir() -> str:
    try:
        cfg = GlobalConfig().csi_bridge
        exe_path = cfg.get("program_path")
        if exe_path:
            return str(Path(exe_path).parent)
    except Exception:
        pass

    return r"C:\Program Files\Computers and Structures\CSiBridge 26"


CSI_BRIDGE_PATH = _get_csi_installation_dir()

pytestmark = pytest.mark.skipif(
    not os.path.exists(CSI_BRIDGE_PATH),
    reason=f"CSI Bridge not installed at configured path: {CSI_BRIDGE_PATH}",
)


@pytest.mark.integration
@pytest.mark.csi_bridge
class TestCSIBridgeIntegration:
    @pytest.fixture
    def config_provider(self):
        return CSIBridgeConfigProvider()

    @pytest.fixture
    def model(self):
        return AnalyticalMultiModel(
            project_id=1,
            structure_id=1,
            structure_name="Integration Test Bridge",
            description="Session-based CSI integration test",
            unit_system=UnitSystem.SI
        )

    def test_config_path_points_to_exe(self, config_provider):
        config = config_provider.load_config()
        exe_path = config.get("program_path")

        assert exe_path is not None
        assert os.path.exists(exe_path)
        assert exe_path.endswith("CSiBridge.exe")

    def test_open_session_and_export_empty_model(self, config_provider, model):
        session = CSIBridgeSession(config_provider)
        try:
            opened = session.open_session(create_new_instance=True, template_file_path=None)
            assert opened is True
            assert session.sap_model is not None
            assert session.bridge_modeler is not None

            exporter = CSIBridgeExporter(session)
            exporter.export(model)

        finally:
            session.close_session()

    def test_session_file_ops(self, config_provider):
        import tempfile

        session = CSIBridgeSession(config_provider)
        temp_path = None

        try:
            session.open_session(create_new_instance=True, template_file_path=None)

            with tempfile.NamedTemporaryFile(suffix=".bdb", delete=False) as tmp:
                temp_path = Path(tmp.name)

            assert session.save_model_as(temp_path) is True
            assert os.path.exists(temp_path)

            session.close_session()

            session = CSIBridgeSession(config_provider)
            session.open_session(create_new_instance=True, template_file_path=None)
            assert session.open_file(str(temp_path)) is True

        finally:
            session.close_session()
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
