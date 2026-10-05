"""
Integration tests for CSI Bridge material export (_export_materials).

⚠️ WARNING: These tests require CSI Bridge to be manually launched!
DO NOT RUN ON CI/CD - Only for local testing with real software running.

Prerequisites:
- CSI Bridge 26 installed and running
- Valid CSI Bridge license
- Windows OS (COM automation required)
- Correct path configured in infrastructure/config/exporters/csi_bridge_config.json
- CSI Bridge application launched manually before running tests
"""

import uuid
from typing import cast

import pytest
import os
from pathlib import Path

from bda.domain.models.submodels import MaterialBase, MaterialSteel, MaterialReinforcement, MaterialConcrete, \
    MaterialTendon
from bda.domain.models.submodels.material import GeneralMaterialIsotropicProperties, DesignPropertiesSteel, \
    DesignPropertiesConcrete, DesignPropertiesReinforcement, DesignPropertiesTendon
from bda.infrastructure.adapters.analytical_software.exporters.csi_bridge_exporter import CSIBridgeExporter
from bda.infrastructure.adapters.analytical_software.config_providers.csi_config_provider import CSIBridgeConfigProvider
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession

from bda.domain.units.export_units import get_export_units
from bda.domain.units.registry import ureg
from bda.domain.enums import UnitSystem

# ---------------------------------------------------------------------------
# Module-level SI export units (passed to every _export_materials call)
# ---------------------------------------------------------------------------
EU_SI = get_export_units(UnitSystem.SI)


# ---------------------------------------------------------------------------
# Module-level skip – CSI Bridge not installed
# ---------------------------------------------------------------------------

def _get_csi_bridge_install_dir() -> str:
    try:
        config = CSIBridgeConfigProvider().load_config()
        exe_path = config.get("program_path")
        if isinstance(exe_path, str) and exe_path:
            exe_path_str = cast(str, exe_path)
            return str(Path(exe_path_str).parent)
    except Exception:
        pass
    return r"C:\Program Files\Computers and Structures\CSiBridge 26"


CSI_BRIDGE_PATH = _get_csi_bridge_install_dir()

pytestmark = pytest.mark.skipif(
    not os.path.exists(CSI_BRIDGE_PATH),
    reason=f"CSI Bridge not installed at configured path: {CSI_BRIDGE_PATH}",
)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.csi_bridge
@pytest.mark.slow
class TestCSIBridgeMaterialExport:
    """Integration tests for material export to real CSI Bridge.

    These tests verify that materials are correctly exported via CSI Bridge COM API.

    Prerequisites:
    - CSI Bridge must be manually launched before running these tests.
    - If CSI Bridge is not running, all tests in this class are skipped automatically.
    """

    # ------------------------------------------------------------------
    # Fixtures – infrastructure
    # ------------------------------------------------------------------

    @pytest.fixture
    def config_provider(self):
        """Provide real CSI Bridge configuration."""
        return CSIBridgeConfigProvider()

    @pytest.fixture
    def exporter(self, config_provider):
        """Create exporter; skip all tests if CSI Bridge is not running."""
        session = CSIBridgeSession(config_provider)
        try:
            session.open_session(create_new_instance=False, template_file_path=None)
            exp = CSIBridgeExporter(session)
        except RuntimeError:
            pytest.skip(
                "CSI Bridge is not running. "
                "Launch CSI Bridge manually before running these tests."
            )
        yield exp
        session.close_session(close_app=False)

    @pytest.fixture(autouse=True)
    def reset_model(self, exporter):
        """Before each test: yield to run the test.
        After each test: nothing specific to clean up.
        """
        yield

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
    def tendon_custom(self):
        """Single custom tendon material."""
        m = MaterialTendon(
            guid=str(uuid.uuid4()),
            name="TestTendon_Custom",
            general_properties=GeneralMaterialIsotropicProperties(
                unit_weight=78.5 * ureg.kilonewton / ureg.meter ** 3,
                modulus_of_elasticity=200000.0 * ureg.megapascal,
                poissons_ratio=0.3,
                thermal_coefficient=1.2e-5 / ureg.delta_degC,
            ),
            design_properties=DesignPropertiesTendon(
                characteristic_yield_strength_fyk=
                255 * ureg.megapascal,
                characteristic_ultimate_tensile_strength_fuk=
                275 * ureg.megapascal
            )
        )
        m.set_id(4)
        return m

    @pytest.fixture
    def mixed_materials(self,
                        steel_custom,
                        concrete_custom,
                        reinforcement_custom,
                        tendon_custom: MaterialTendon):
        """Mixed list of custom materials covering all supported types."""
        return [steel_custom, concrete_custom, reinforcement_custom, tendon_custom]

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_export_empty_list_does_not_raise(self, exporter):
        """Exporting an empty materials list should complete without errors."""
        exporter._export_materials([], EU_SI)

    def test_export_single_custom_steel(self, exporter, steel_custom):
        """Export a single custom steel material."""
        exporter._export_materials([steel_custom], EU_SI)

    def test_export_single_custom_concrete(self, exporter, concrete_custom):
        """Export a single custom concrete material."""
        exporter._export_materials([concrete_custom], EU_SI)

    def test_export_single_custom_reinforcement(self, exporter, reinforcement_custom):
        """Export a single custom reinforcement material (uses steel path)."""
        exporter._export_materials([reinforcement_custom], EU_SI)

    def test_export_single_custom_tendon(self, exporter, tendon_custom):
        """Export a single custom tendon material (uses steel path)."""
        exporter._export_materials([tendon_custom], EU_SI)

    def test_export_mixed_materials(self, exporter, mixed_materials):
        """Export a list with steel, concrete and reinforcement custom materials."""
        exporter._export_materials(mixed_materials, EU_SI)

    def test_export_raises_on_unsupported_type(self, exporter):
        """Writing materials should propagate an exception for unsupported material type."""
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

        assert exporter._export_materials([bad_material], EU_SI) is False, \
            "Failed material export should return False"
