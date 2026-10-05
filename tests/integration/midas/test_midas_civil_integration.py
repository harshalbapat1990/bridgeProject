"""
Integration tests for MIDAS Civil exporter/session_manager wiring.

⚠️ Requires MIDAS Civil installed locally. These tests are skipped automatically
when the configured installation path is unavailable.
"""

import os
from pathlib import Path

import pytest

from bda.config.global_config import GlobalConfig
from bda.domain import AnalyticalMultiModel
from bda.domain.enums import OutputSoftware, UnitSystem
from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider
from bda.infrastructure.adapters.analytical_software.exporters.midas_civil_exporter import MidasCivilExporter
from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession

@pytest.fixture(scope="session", autouse=True)
def setup_global_config():
    GlobalConfig.reset()
    GlobalConfig()

def _get_midas_installation_dir() -> str:
    try:
        cfg = GlobalConfig().midas_civil
        exe_path = cfg.get("program_path")
        if exe_path:
            return str(Path(exe_path).parent)
    except Exception:
        pass

    return r"C:\Program Files\MIDAS\MIDAS CIVIL NX\MIDAS CIVIL NX"


MIDAS_PATH = _get_midas_installation_dir()

pytestmark = pytest.mark.skipif(
    not os.path.exists(MIDAS_PATH),
    reason=f"MIDAS Civil not installed at configured path: {MIDAS_PATH}",
)


@pytest.mark.integration
@pytest.mark.midas_civil
class TestMidasCivilIntegration:
    @pytest.fixture
    def config_provider(self):
        return MidasConfigProvider()

    @pytest.fixture
    def model(self) -> AnalyticalMultiModel:
        return AnalyticalMultiModel(
            unit_system=UnitSystem.SI,
            project_id=1,
            structure_id=1,
            structure_name="Test Structure",
            description="Session-based MIDAS integration test",
        )

    def test_config_has_required_fields(self, config_provider):
        config = config_provider.load_config()

        assert isinstance(config.get("base_url"), str)
        assert isinstance(config.get("mapi_key"), str)
        exe_path = config.get("program_path")
        assert isinstance(exe_path, str)
        assert os.path.exists(exe_path)

    def test_open_session_create_instance(self, config_provider):
        session = MidasCivilSession(config_provider)
        try:
            opened = session.open_session(create_new_instance=True, template_file_path=None)
            assert opened is True
            assert session.created_instance is True
            assert session.midas_process is not None

        finally:
            session.close_session()

    # @pytest.mark.skip(reason="Requires live MIDAS API/process readiness and license state")
    def test_export_empty_model(self, config_provider, model):
        session = MidasCivilSession(config_provider)
        try:
            session.open_session(create_new_instance=True, template_file_path=None)
            exporter = MidasCivilExporter(session)
            exporter.export(model)
        finally:
            session.close_session()
