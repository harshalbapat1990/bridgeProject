"""
Integration tests for MIDAS Civil material export (_export_materials).

⚠️ WARNING: These tests require MIDAS Civil to be manually launched!
DO NOT RUN ON CI/CD - Only for local testing with real software running.

Prerequisites:
- MIDAS Civil NX installed and running
- Valid MIDAS Civil license
- Windows OS
- Correct path configured in infrastructure/config/exporters/midas_config.json
- MIDAS API key configured
- MIDAS Civil application launched manually before running tests
"""
import uuid
from typing import cast

import pytest
import os
from pathlib import Path

from midas_civil import Model

from bda.domain.models.submodels import MaterialSteel
from bda.domain.models.submodels.material import GeneralMaterialIsotropicProperties, DesignPropertiesSteel, \
    MaterialConcrete, DesignPropertiesConcrete, MaterialReinforcement, DesignPropertiesReinforcement
from bda.infrastructure.adapters.analytical_software.exporters.midas_civil_exporter import MidasCivilExporter
from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider
from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession
from bda.domain.enums import (
    MaterialModelType,
    MaterialType,
)
from bda.domain.units.export_units import get_export_units
from bda.domain.units.registry import ureg
from bda.domain.enums import UnitSystem

# ---------------------------------------------------------------------------
# Module-level SI export units (passed to every _export_materials call)
# ---------------------------------------------------------------------------
EU_SI = get_export_units(UnitSystem.SI)


# ---------------------------------------------------------------------------
# Module-level skip – MIDAS Civil not installed
# ---------------------------------------------------------------------------

def _get_midas_install_dir() -> str:
    try:
        config = MidasConfigProvider().load_config()
        exe_path = config.get("program_path")
        if isinstance(exe_path, str) and exe_path:
            exe_path_str = cast(str, exe_path)
            return str(Path(exe_path_str).parent)
    except Exception:
        pass
    return r"C:\Program Files\MIDAS\MIDAS CIVIL NX\MIDAS CIVIL NX"


MIDAS_CIVIL_PATH = _get_midas_install_dir()

pytestmark = pytest.mark.skipif(
    not os.path.exists(MIDAS_CIVIL_PATH),
    reason=f"MIDAS Civil not installed at configured path: {MIDAS_CIVIL_PATH}",
)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.midas_civil
@pytest.mark.slow
class TestMidasCivilMaterialExport:
    """Integration tests for material export to real MIDAS Civil.

    These tests verify that materials are correctly exported via MIDAS API.

    Prerequisites:
    - MIDAS Civil must be manually launched before running these tests.
    - API must be active (exporter.is_active == True).
    - If MIDAS is not running, all tests in this class are skipped automatically.
    """

    # ------------------------------------------------------------------
    # Fixtures – infrastructure
    # ------------------------------------------------------------------

    @pytest.fixture
    def config_provider(self):
        """Provide real MIDAS Civil configuration."""
        return MidasConfigProvider()

    @pytest.fixture
    def exporter(self, config_provider):
        """Create exporter and skip all tests if MIDAS API is not active."""
        session = MidasCivilSession(config_provider)
        session.open_session(create_new_instance=False, template_file_path=None)
        exp = MidasCivilExporter(session)
        if not session.is_active:
            pytest.skip(
                "MIDAS Civil is not running or API is not active. "
                "Launch MIDAS Civil manually before running these tests."
            )
        yield exp
        session.close_session()

    @pytest.fixture(autouse=True)
    def reset_model(self, exporter):
        """Before each test: create fresh model and delete all materials.
        After each test: wait 5 s to let MIDAS process the previous request.
        """
        # --- setup ---
        # MidasAPI(exporter.base_url, exporter.mapi_key).request("DELETE", "/db/MATL")
        yield
        # --- teardown ---

    # ------------------------------------------------------------------
    # Fixtures – material sets
    # ------------------------------------------------------------------

    @pytest.fixture
    def steel_custom(self):
        """Single custom steel material."""
        m = MaterialSteel(
            guid=str(uuid.uuid4()),
            name="TestSteel_Custom",
            general_properties=GeneralMaterialIsotropicProperties(
                unit_weight=78.5 * ureg.kilonewton / ureg.meter ** 3,
                modulus_of_elasticity=210000.0 * ureg.megapascal,
                poissons_ratio=0.3,
                thermal_coefficient=1.2e-5 / ureg.delta_degC,
            ),
            design_properties=DesignPropertiesSteel(
                characteristic_yield_strength_fyk=
                255 * ureg.megapascal,
                characteristic_ultimate_tensile_strength_fuk=
                275 * ureg.megapascal,
                mean_yield_strength_fym=
                300 * ureg.megapascal,
                mean_ultimate_tensile_strength_fum=
                315 * ureg.megapascal,
            )
        )
        m.set_id(1)
        return m

    @pytest.fixture
    def concrete_custom(self):
        """Single custom concrete material."""
        m = MaterialConcrete(
            guid=str(uuid.uuid4()),
            name="TestConcrete_Custom",
            general_properties=GeneralMaterialIsotropicProperties(
                unit_weight=25.0 * ureg.kilonewton / ureg.meter ** 3,
                modulus_of_elasticity=30000.0 * ureg.megapascal,
                poissons_ratio=0.2,
                thermal_coefficient=1.0e-5 / ureg.delta_degC,
            ),
            design_properties=DesignPropertiesConcrete(
                characteristic_compressive_strength_fck=
                45 * ureg.megapascal,
                mean_compressive_strength_fcm=
                48 * ureg.megapascal,
            )
        )
        m.set_id(2)
        return m

    @pytest.fixture
    def reinforcement_custom(self):
        """Single custom reinforcement material (mapped to steel path)."""
        m = MaterialReinforcement(
            guid=str(uuid.uuid4()),
            name="TestRebar_Custom",
            general_properties=GeneralMaterialIsotropicProperties(
                unit_weight=78.5 * ureg.kilonewton / ureg.meter ** 3,
                modulus_of_elasticity=200000.0 * ureg.megapascal,
                poissons_ratio=0.3,
                thermal_coefficient=1.2e-5 / ureg.delta_degC,
            ),
            design_properties=DesignPropertiesReinforcement(
                characteristic_yield_strength_fyk=
                255 * ureg.megapascal,
                characteristic_ultimate_tensile_strength_fuk=
                275 * ureg.megapascal,
                mean_yield_strength_fym=
                295 * ureg.megapascal,
                mean_ultimate_tensile_strength_fum=
                305 * ureg.megapascal
            )
        )
        m.set_id(3)
        return m

    @pytest.fixture
    def mixed_materials(self, steel_custom, concrete_custom, reinforcement_custom):
        """Mixed list of custom materials covering all supported types."""
        return [steel_custom, concrete_custom, reinforcement_custom]

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_export_empty_list_returns_true(self, exporter):
        """Exporting an empty materials list should return True without errors."""
        result = exporter._export_materials([], EU_SI)
        Model.create()
        assert result is True, "Empty export should return True"

    def test_export_single_custom_steel(self, exporter, steel_custom):
        """Export a single custom steel material."""
        result = exporter._export_materials([steel_custom], EU_SI)
        Model.create()
        assert result is True, "Export of custom steel should return True"

    def test_export_single_custom_concrete(self, exporter, concrete_custom):
        """Export a single custom concrete material."""
        result = exporter._export_materials([concrete_custom], EU_SI)
        Model.create()
        assert result is True, "Export of custom concrete should return True"

    def test_export_single_custom_reinforcement(self, exporter, reinforcement_custom):
        """Export a single custom reinforcement material (uses steel path)."""
        result = exporter._export_materials([reinforcement_custom], EU_SI)
        Model.create()
        assert result is True, "Export of custom reinforcement should return True"

    def test_export_mixed_materials(self, exporter, mixed_materials):
        """Export a list with steel, concrete and reinforcement custom materials."""
        result = exporter._export_materials(mixed_materials, EU_SI)
        Model.create()
        assert result is True, "Export of mixed materials list should return True"

    def test_export_raises_on_unsupported_type(self, exporter):
        """Writing materials should propagate ValueError for unsupported material type."""
        bad_material = MaterialConcrete(
            guid=str(uuid.uuid4()),
            name="TestConcrete_Custom",
            general_properties=GeneralMaterialIsotropicProperties(
                unit_weight=25.0 * ureg.kilonewton / ureg.meter ** 3,
                modulus_of_elasticity=30000.0 * ureg.megapascal,
                poissons_ratio=0.2,
                thermal_coefficient=1.0e-5 / ureg.delta_degC,
            ),
            design_properties=DesignPropertiesConcrete(
                characteristic_compressive_strength_fck=
                45 * ureg.megapascal,
                mean_compressive_strength_fcm=
                48 * ureg.megapascal,
            )
        )
        # Force an unsupported material_type value after construction
        object.__setattr__(bad_material, "material_type", "unsupported_type")

        with pytest.raises(Exception):
            exporter._write_materials([bad_material], EU_SI)
            Model.create()

        assert exporter._export_materials([bad_material], EU_SI) is False, \
            "Failed material export should return False"

