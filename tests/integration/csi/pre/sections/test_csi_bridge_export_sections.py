"""
Integration tests for CSI Bridge section export (_export_sections).

⚠️ WARNING: These tests require CSI Bridge to be manually launched!
DO NOT RUN ON CI/CD - Only for local testing with real software running.

Prerequisites:
- CSI Bridge 26 installed and running
- Valid CSI Bridge license
- Windows OS (COM automation required)
- Correct path configured in infrastructure/config/exporters/csi_bridge_config.json
- CSI Bridge application launched manually before running tests

Section families and types covered
───────────────────────────────────
USER family:
  - ANGLE            → SectionUserAngle
  - BOX              → SectionUserBox
  - CHANNEL          → SectionUserChannel
  - SOLID_ROUND      → SectionUserSolidRound
  - SOLID_RECTANGLE  → SectionUserSolidRectangle
  - I_SECTION        → SectionUserISection

COMPOSITE family:
  - STEEL_I_TYPE1    → SectionCompositeSteelItype1
  - STEEL_I_TYPE2    → SectionCompositeSteelItype2

PSC family:
  - PSC_1CELL         → SectionPSC12Cell (1-cell box girder)
  - PSC_2CELL         → SectionPSC12Cell (2-cell box girder)
  - PSC_VALUE         → SectionPSCValue  (arbitrary polygon outlines)

TAPERED family:
  - LINEAR            → SectionTapered (linear taper variation)
  - PARABOLIC         → SectionTapered (parabolic taper variation)
  - CUBIC             → SectionTapered (cubic taper variation)

Unsupported families (raise ValueError):
  - DB       → no exporter registered

Wrong-type guard tests (raise ValueError inside specific export method):
  - USER section dispatched to wrong type handler
"""

import pytest
import uuid
import os
from pathlib import Path

from pip._internal.network import session

from bda.domain.models.submodels.material import GeneralMaterialIsotropicProperties, DesignPropertiesConcrete, \
    DesignPropertiesSteel, MaterialSteel, MaterialConcrete
from bda.domain.models.submodels.section_base import Offset
from bda.domain.models.submodels.sections import SectionStandardPipe, DimensionsPipe
from bda.infrastructure.adapters.analytical_software.exporters.csi_bridge_exporter import CSIBridgeExporter
from bda.infrastructure.adapters.analytical_software.config_providers.csi_config_provider import CSIBridgeConfigProvider
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession

from bda.domain.enums import SectionFamily, SectionType, OffsetReference
from bda.domain.enums import UnitSystem

from bda.domain.models.submodels.sections.db_section import SectionDB
from bda.domain.models.submodels.sections.standard_shapes import (
    SectionStandardAngle, DimensionsAngle,
    SectionStandardBox, DimensionsBox,
    SectionStandardChannel, DimensionsChannel,
    SectionStandardSolidRound, DimensionsSolidRound,
    SectionStandardSolidRectangle, DimensionsSolidRectangle,
    SectionStandardISection, DimensionsISection,
)
from bda.domain.models.submodels.sections.composite import (
    SectionCompositeSteelISymmetric, DimensionsCompositeSteelISymmetric,
    SectionCompositeSteelIAsymmetric, DimensionsCompositeSteelIAsymmetric,
)
from bda.domain.models.submodels.sections.psc import (
    SectionPSC12Cell,  DimensionsPSC12Cell,
    SectionPSCValue,   DimensionsPSCValues,
    JointsPSC, OuterHeightHo, OuterBreadthBo, InnerHeightHi, InnerBreadthBi,
    Point2D,
)
from bda.domain.models.submodels.sections.tapered import SectionTapered
from bda.domain.enums import TaperVariation
from bda.domain.units.export_units import get_export_units
from bda.domain.units.registry import ureg

# ---------------------------------------------------------------------------
# Module-level SI export units (passed to every _export_sections call)
# ---------------------------------------------------------------------------
EU_SI = get_export_units(UnitSystem.SI)
m = ureg.meter
MPa = ureg.megapascal
kN_m3 = ureg.kilonewton / ureg.meter ** 3
per_degC = 1 / ureg.delta_degC


# ---------------------------------------------------------------------------
# Module-level skip – CSI Bridge not installed
# ---------------------------------------------------------------------------

def _get_csi_bridge_install_dir() -> str:
    try:
        config = CSIBridgeConfigProvider().load_config()
        exe_path = config.get("program_path")
        if exe_path:
            return str(Path(exe_path).parent)
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
class TestCSIBridgeSectionExport:
    """Integration tests for section export to real CSI Bridge.

    Every supported section type (USER, COMPOSITE, and PSC families) is tested
    individually, in bulk, and in mixed combinations. Tests for unsupported
    families and wrong-object-type guards are also included.

    Prerequisites:
    - CSI Bridge must be manually launched before running these tests.
    - If CSI Bridge is not running, all tests in this class are skipped.
    """

    # ------------------------------------------------------------------
    # Fixtures – infrastructure
    # ------------------------------------------------------------------

    @pytest.fixture(autouse=True, scope='session')
    def config_provider(self):
        """Provide real CSI Bridge configuration."""
        return CSIBridgeConfigProvider()

    @pytest.fixture(autouse=True, scope='session')
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
        """Yield to run the test; nothing to clean up between section exports."""
        yield

    # ------------------------------------------------------------------
    # Fixtures – shared materials
    # ------------------------------------------------------------------

    @pytest.fixture(autouse=True, scope='session')
    def steel_material(self):
        """Custom steel material used as material_main for all sections."""
        mat = MaterialSteel(
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
        mat.set_id(1)
        return mat

    @pytest.fixture(autouse=True, scope='session')
    def concrete_material(self):
        """Custom concrete material used as material_composite for composite sections."""
        mat = MaterialConcrete(
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
        mat.set_id(2)
        return mat

    @pytest.fixture(autouse=True, scope='session')
    def export_materials_first(self, exporter, steel_material, concrete_material):
        """Export shared materials before any sections, so that sections can reference them by ID."""
        exporter._export_materials([steel_material, concrete_material], EU_SI)

    # ------------------------------------------------------------------
    # Fixtures – USER sections
    # ------------------------------------------------------------------

    @pytest.fixture
    def section_angle(self, steel_material):
        """SectionUserAngle – L-profile 203×203×22 mm (SI)."""
        sec = SectionStandardAngle(
            guid=str(uuid.uuid4()),
            name="TestAngle_L203x203x22",
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsAngle(
                height=0.203 * m,
                width=0.203 * m,
                thickness_web=0.022 * m,
                thickness_flange=0.022 * m,
            ),
        )
        sec.set_id(1)
        sec.set_material_main(steel_material)
        return sec

    @pytest.fixture
    def section_angle_2(self, steel_material):
        """SectionUserAngle – L-profile 203×203×22 mm (SI)."""
        sec = SectionStandardAngle(
            guid=str(uuid.uuid4()),
            name="TestAngle_L403x503x42",
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsAngle(
                height=0.403 * m,
                width=0.503 * m,
                thickness_web=0.042 * m,
                thickness_flange=0.042 * m,
            ),
        )
        sec.set_id(1)
        sec.set_material_main(steel_material)
        return sec

    @pytest.fixture
    def section_box(self, steel_material):
        """SectionUserBox – closed rectangular hollow section 500×300 mm."""
        sec = SectionStandardBox(
            guid=str(uuid.uuid4()),
            name="TestBox_500x300",
            offset=Offset(OffsetReference.CENTER_TOP),
            dimensions=DimensionsBox(
                height_h=0.50 * m,
                top_flange_width_b=0.30 * m,
                web_thickness_tw=0.015 * m,
                top_flange_thickness_tf1=0.020 * m,
            ),
        )
        sec.set_id(2)
        sec.set_material_main(steel_material)
        return sec

    @pytest.fixture
    def section_channel(self, steel_material):
        """SectionUserChannel – U-profile 550 mm."""
        sec = SectionStandardChannel(
            guid=str(uuid.uuid4()),
            name="TestChannel_U550",
            offset=Offset(OffsetReference.LEFT_TOP),
            dimensions=DimensionsChannel(
                height_h=0.55 * m,
                top_flange_width_b1=0.20 * m,
                bottom_flange_width_b2=0.22 * m,
                web_thickness_tw=0.014 * m,
                top_flange_thickness_tf1=0.018 * m,
                bottom_flange_thickness_tf2=0.020 * m,
                web_inner_radius_r1=0.010 * m,
                flange_end_radius_r2=0.008 * m,
            ),
        )
        sec.set_id(3)
        sec.set_material_main(steel_material)
        return sec

    @pytest.fixture
    def section_solid_round(self, steel_material):
        """SectionUserSolidRound – circular solid bar ⌀180 mm."""
        sec = SectionStandardSolidRound(
            guid=str(uuid.uuid4()),
            name="TestSolidRound_D180",
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsSolidRound(
                diameter_d=0.18 * m,
            ),
        )
        sec.set_id(4)
        sec.set_material_main(steel_material)
        return sec

    @pytest.fixture
    def section_solid_rectangle(self, steel_material):
        """SectionUserSolidRectangle – rectangular solid bar 400×250 mm."""
        sec = SectionStandardSolidRectangle(
            guid=str(uuid.uuid4()),
            name="TestSolidRect_400x250",
            offset=Offset(OffsetReference.CENTER_BOTTOM),
            dimensions=DimensionsSolidRectangle(
                height_h=0.40 * m,
                width_b=0.25 * m,
            ),
        )
        sec.set_id(5)
        sec.set_material_main(steel_material)
        return sec

    @pytest.fixture
    def section_pipe(self, steel_material):
        """SectionUserPipe – circular pipe 400×25 mm."""
        sec = SectionStandardPipe(
            guid=str(uuid.uuid4()),
            name="TestPipe_400x25",
            offset=Offset(OffsetReference.CENTER_BOTTOM),
            dimensions=DimensionsPipe(
                external_diameter_d=0.40 * m,
                wall_thickness_tw=0.025 * m,
            ),
        )
        sec.set_id(6)
        sec.set_material_main(steel_material)
        return sec

    @pytest.fixture
    def section_i_section(self, steel_material):
        """SectionUserISection – symmetric I-girder 1010 mm deep."""
        sec = SectionStandardISection(
            guid=str(uuid.uuid4()),
            name="TestISection_1010",
            offset=Offset(OffsetReference.CENTER_TOP),
            dimensions=DimensionsISection(
                total_height_h=1.010 * m,
                top_flange_width_b1=0.41 * m,
                bottom_flange_width_b2=0.50 * m,
                web_thickness_tw=0.015 * m,
                top_flange_thickness_tf1=0.020 * m,
                bottom_flange_thickness_tf2=0.050 * m,
                web_inner_radius_r1=0.010 * m,
                flange_end_radius_r2=0.010 * m,
            ),
        )
        sec.set_id(7)
        sec.set_material_main(steel_material)
        return sec

    # ------------------------------------------------------------------
    # Fixtures – COMPOSITE sections
    # ------------------------------------------------------------------

    @pytest.fixture
    def section_composite_i_symmetric(self, steel_material, concrete_material):
        """SectionCompositeSteelISymmetric – composite steel-concrete I girder symmetric."""
        sec = SectionCompositeSteelISymmetric(
            guid=str(uuid.uuid4()),
            name="TestComposite_SteelI_Symmetric",
            offset=Offset(OffsetReference.CENTER_TOP),
            dimensions=DimensionsCompositeSteelISymmetric(
                slab_width_bc=3.00 * m,
                slab_thickness_tc=0.20 * m,
                slab_girder_spacing_hh=0.05 * m,
                girder_top_flange_width_b1=0.35 * m,
                girder_top_flange_thickness_tf1=0.030 * m,
                girder_bottom_flange_width_b2=0.45 * m,
                girder_bottom_flange_thickness_tf2=0.040 * m,
                girder_web_thickness_tw=0.018 * m,
                girder_web_height_hw=1.20 * m,
            ),
        )
        sec.set_id(20)
        sec.set_material_main(steel_material)
        sec.set_material_composite(concrete_material)
        return sec

    @pytest.fixture
    def section_composite_i_asymmetric(self, steel_material, concrete_material):
        """SectionCompositeSteelIAsymmetric – composite steel-concrete I girder asymmetric (skewed web)."""
        sec = SectionCompositeSteelIAsymmetric(
            guid=str(uuid.uuid4()),
            name="TestComposite_SteelI_Asymmetric",
            offset=Offset(OffsetReference.CENTER_TOP),
            dimensions=DimensionsCompositeSteelIAsymmetric(
                slab_distance_rf_sg=0.15 * m,
                top_flange_distance_rf_top=0.20 * m,
                bottom_flange_distance_rf_bot=0.25 * m,
                slab_width_bc=3.20 * m,
                slab_thickness_tc=0.22 * m,
                slab_girder_spacing_hh=0.05 * m,
                girder_top_flange_left_width_b1=0.30 * m,
                girder_top_flange_right_width_b2=0.32 * m,
                girder_top_flange_thickness_t1=0.025 * m,
                girder_bottom_flange_left_width_b3=0.45 * m,
                girder_bottom_flange_right_width_b4=0.47 * m,
                girder_bottom_flange_thickness_t2=0.035 * m,
                girder_web_thickness_tw=0.016 * m,
                girder_web_height_h=1.25 * m,
            ),
        )
        sec.set_id(21)
        sec.set_material_main(steel_material)
        sec.set_material_composite(concrete_material)
        return sec

    # ------------------------------------------------------------------
    # Fixtures – PSC sections
    # ------------------------------------------------------------------

    @pytest.fixture
    def section_psc_1cell(self, concrete_material):
        """SectionPSC12Cell – 1-cell prestressed concrete box girder.

        Dimensions taken from CSI Bridge Section Data dialog (PSC-1CELL).
        Outer: HO1=0.1, HO2=0.2, HO2-1=0, HO2-2=0, HO3=1.2, HO3-1=0
               BO1=1,   BO1-1=0, BO1-2=0, BO2=1,   BO2-1=0,  BO3=1
        Inner: HI1=0.1, HI2=0.2, HI2-1=0, HI2-2=0, HI3=1,   HI3-1=0,
               HI4=0.1, HI4-1=0, HI4-2=0, HI5=0.2
               BI1=1.5, BI1-1=0, BI1-2=0, BI2-1=0, BI3=1,   BI3-1=0,
               BI3-2=0, BI4=0.15
        """
        sec = SectionPSC12Cell(
            guid=str(uuid.uuid4()),
            name="TestPSC_1Cell",
            section_type=SectionType.PSC_1CELL,
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsPSC12Cell(
                joints=JointsPSC(jo1=False, jo2=False, jo3=False,
                                 ji1=False, ji2=False, ji3=False, ji4=False, ji5=False),
                outer_height_ho=OuterHeightHo(ho1=0.1*m, ho2=0.2*m, ho2_1=0.0*m,
                                              ho2_2=0.0*m, ho3=1.2*m, ho3_1=0.0*m),
                outer_breadth_bo=OuterBreadthBo(bo1=1.0*m, bo1_1=0.0*m, bo1_2=0.0*m,
                                                bo2=1.0*m, bo2_1=0.0*m, bo3=1.0*m),
                inner_height_hi=InnerHeightHi(hi1=0.1*m, hi2=0.2*m, hi2_1=0.0*m, hi2_2=0.0*m,
                                              hi3=1.0*m, hi3_1=0.0*m, hi4=0.1*m, hi4_1=0.0*m,
                                              hi4_2=0.0*m, hi5=0.2*m),
                inner_breadth_bi=InnerBreadthBi(bi1=1.5*m, bi1_1=0.0*m, bi1_2=0.0*m,
                                                bi2_1=0.0*m, bi3=1.0*m, bi3_1=0.0*m,
                                                bi3_2=0.0*m, bi4=0.15*m),
            ),
        )
        sec.set_id(30)
        sec.set_material_main(concrete_material)
        return sec

    @pytest.fixture
    def section_psc_2cells(self, concrete_material):
        """SectionPSC12Cell – 2-cell prestressed concrete box girder.

        Dimensions taken from CSI Bridge Section Data dialog (PSC-2CELL).
        Outer: same as 1-cell variant.
        Inner: same as 1-cell variant.
        """
        sec = SectionPSC12Cell(
            guid=str(uuid.uuid4()),
            name="TestPSC_2Cell",
            section_type=SectionType.PSC_2CELL,
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsPSC12Cell(
                joints=JointsPSC(jo1=False, jo2=False, jo3=False,
                                 ji1=False, ji2=False, ji3=False, ji4=False, ji5=False),
                outer_height_ho=OuterHeightHo(ho1=0.1*m, ho2=0.2*m, ho2_1=0.0*m,
                                              ho2_2=0.0*m, ho3=1.2*m, ho3_1=0.0*m),
                outer_breadth_bo=OuterBreadthBo(bo1=1.0*m, bo1_1=0.0*m, bo1_2=0.0*m,
                                                bo2=1.0*m, bo2_1=0.0*m, bo3=1.0*m),
                inner_height_hi=InnerHeightHi(hi1=0.1*m, hi2=0.2*m, hi2_1=0.0*m, hi2_2=0.0*m,
                                              hi3=1.0*m, hi3_1=0.0*m, hi4=0.1*m, hi4_1=0.0*m,
                                              hi4_2=0.0*m, hi5=0.2*m),
                inner_breadth_bi=InnerBreadthBi(bi1=1.5*m, bi1_1=0.0*m, bi1_2=0.0*m,
                                                bi2_1=0.0*m, bi3=1.0*m, bi3_1=0.0*m,
                                                bi3_2=0.0*m, bi4=0.15*m),
            ),
        )
        sec.set_id(31)
        sec.set_material_main(concrete_material)
        return sec

    @pytest.fixture
    def section_psc_value(self, concrete_material):
        """SectionPSCValue – prestressed concrete section defined by explicit polygons.

        Represents a two-cell box girder 6 m wide × 2 m deep with:
        - outer outline: 12-vertex polygon (top deck + webs + bottom slab)
        - inner outline 1 (right cell): rectangular void
        - inner outline 2 (left cell): rectangular void

        Coordinates in metres; origin at top-centre, Y downward negative.
        """
        outer_outline = [
            Point2D(x=-3.0*m, y= 0.00*m),
            Point2D(x= 3.0*m, y= 0.00*m),
            Point2D(x= 3.0*m, y=-0.25*m),
            Point2D(x= 1.5*m, y=-0.25*m),
            Point2D(x= 1.5*m, y=-1.80*m),
            Point2D(x= 3.0*m, y=-1.80*m),
            Point2D(x= 3.0*m, y=-2.00*m),
            Point2D(x=-3.0*m, y=-2.00*m),
            Point2D(x=-3.0*m, y=-1.80*m),
            Point2D(x=-1.5*m, y=-1.80*m),
            Point2D(x=-1.5*m, y=-0.25*m),
            Point2D(x=-3.0*m, y=-0.25*m),
        ]

        inner_outline_right = [
            Point2D(x= 0.15*m, y=-0.25*m),
            Point2D(x= 1.35*m, y=-0.25*m),
            Point2D(x= 1.35*m, y=-1.80*m),
            Point2D(x= 0.15*m, y=-1.80*m),
        ]

        inner_outline_left = [
            Point2D(x=-1.35*m, y=-0.25*m),
            Point2D(x=-0.15*m, y=-0.25*m),
            Point2D(x=-0.15*m, y=-1.80*m),
            Point2D(x=-1.35*m, y=-1.80*m),
        ]

        sec = SectionPSCValue(
            guid=str(uuid.uuid4()),
            name="TestPSC_Value",
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsPSCValues(
                outer_outline=outer_outline,
                inner_outlines=[inner_outline_right, inner_outline_left],
            ),
        )
        sec.set_id(32)
        sec.set_material_main(concrete_material)
        return sec

    # ------------------------------------------------------------------
    # Fixtures – TAPERED sections
    # ------------------------------------------------------------------

    @pytest.fixture
    def section_tapered_linear(self, concrete_material, section_angle, section_angle_2):
        """SectionTapered – linear taper between PSC_1CELL (start) and PSC_2CELL (end).

        Both component sections must be exported to CSI Bridge first so that
        SetNonPrismatic can reference them by name.
        """
        sec = SectionTapered(
            guid=str(uuid.uuid4()),
            name="TestTapered_angles_linear",
            offset=Offset(OffsetReference.CENTER_CENTER),
            section_start_id="",
            section_end_id="",
            taper_y_variation=TaperVariation.LINEAR,
            taper_z_variation=TaperVariation.LINEAR,
        )
        sec.set_id(40)
        sec.set_material_main(concrete_material)
        sec.set_section_start(section_angle)
        sec.set_section_end(section_angle_2)
        return sec

    @pytest.fixture
    def section_tapered_parabolic(self, concrete_material, section_angle, section_angle_2):
        """SectionTapered – parabolic taper between angle (start) and angle_2 (end).

        Both component sections must be exported to CSI Bridge first so that
        SetNonPrismatic can reference them by name.
        """
        sec = SectionTapered(
            guid=str(uuid.uuid4()),
            name="TestTapered_Parabolic_angle_to_angle2",
            offset=Offset(OffsetReference.CENTER_CENTER),
            section_start_id="",
            section_end_id="",
            taper_y_variation=TaperVariation.PARABOLIC,
            taper_z_variation=TaperVariation.PARABOLIC,
        )
        sec.set_id(41)
        sec.set_material_main(concrete_material)
        sec.set_section_start(section_angle)
        sec.set_section_end(section_angle_2)
        return sec

    @pytest.fixture
    def section_tapered_cubic(self, concrete_material, section_angle, section_angle_2):
        """SectionTapered – cubic taper between angle (start) and angle_2 (end).

        Both component sections must be exported to CSI Bridge first so that
        SetNonPrismatic can reference them by name.
        """
        sec = SectionTapered(
            guid=str(uuid.uuid4()),
            name="TestTapered_Cubic_angle_to_angle2",
            offset=Offset(OffsetReference.CENTER_CENTER),
            section_start_id="",
            section_end_id="",
            taper_y_variation=TaperVariation.CUBIC,
            taper_z_variation=TaperVariation.CUBIC,
        )
        sec.set_id(41)
        sec.set_material_main(concrete_material)
        sec.set_section_start(section_angle)
        sec.set_section_end(section_angle_2)
        return sec


    # ------------------------------------------------------------------
    # Fixtures – combined section lists
    # ------------------------------------------------------------------

    @pytest.fixture
    def all_user_sections(
        self,
        section_angle,
        section_angle_2,
        section_box,
        section_channel,
        section_solid_round,
        section_solid_rectangle,
        section_i_section,
        section_pipe,
    ):
        """All six supported USER section types in one list."""
        return [
            section_angle,
            section_angle_2,
            section_box,
            section_channel,
            section_solid_round,
            section_solid_rectangle,
            section_i_section,
            section_pipe,
        ]

    @pytest.fixture
    def all_composite_sections(
        self,
        section_composite_i_symmetric,
        section_composite_i_asymmetric,
    ):
        """Both supported COMPOSITE section types in one list."""
        return [section_composite_i_symmetric, section_composite_i_asymmetric]

    @pytest.fixture
    def all_psc_sections(
        self,
        section_psc_1cell,
        section_psc_2cells,
        section_psc_value,
    ):
        """All supported PSC section types in one list."""
        return [section_psc_1cell, section_psc_2cells, section_psc_value]

    @pytest.fixture
    def mixed_sections(self, all_user_sections, all_composite_sections, all_psc_sections):
        """All USER, COMPOSITE, and PSC sections combined in a single list."""
        return all_user_sections + all_composite_sections + all_psc_sections

    # ------------------------------------------------------------------
    # Tests – empty input
    # ------------------------------------------------------------------

    def test_export_empty_list_does_not_raise(self, exporter):
        """Exporting an empty sections list must complete without errors."""
        exporter._export_sections([], EU_SI)

    # ------------------------------------------------------------------
    # Tests – USER / ANGLE
    # ------------------------------------------------------------------

    def test_export_single_angle_section(self, exporter, section_angle):
        """Export a single L-profile (ANGLE) USER section."""
        exporter._export_sections([section_angle], EU_SI)

    # ------------------------------------------------------------------
    # Tests – USER / BOX
    # ------------------------------------------------------------------

    def test_export_single_box_section(self, exporter, section_box):
        """Export a single rectangular hollow section (BOX) USER section."""
        exporter._export_sections([section_box], EU_SI)

    # ------------------------------------------------------------------
    # Tests – USER / CHANNEL
    # ------------------------------------------------------------------

    def test_export_single_channel_section(self, exporter, section_channel):
        """Export a single U-profile (CHANNEL) USER section."""
        exporter._export_sections([section_channel], EU_SI)

    # ------------------------------------------------------------------
    # Tests – USER / SOLID_ROUND
    # ------------------------------------------------------------------

    def test_export_single_solid_round_section(self, exporter, section_solid_round):
        """Export a single circular solid section (SOLID_ROUND) USER section."""
        exporter._export_sections([section_solid_round], EU_SI)

    # ------------------------------------------------------------------
    # Tests – USER / SOLID_RECTANGLE
    # ------------------------------------------------------------------

    def test_export_single_solid_rectangle_section(self, exporter, section_solid_rectangle):
        """Export a single rectangular solid section (SOLID_RECTANGLE) USER section."""
        exporter._export_sections([section_solid_rectangle], EU_SI)

    # ------------------------------------------------------------------
    # Tests – USER / I_SECTION
    # ------------------------------------------------------------------

    def test_export_single_i_section(self, exporter, section_i_section):
        """Export a single symmetric I-girder (I_SECTION) USER section."""
        exporter._export_sections([section_i_section], EU_SI)

    # ------------------------------------------------------------------
    # Tests – USER / PIPE
    # ------------------------------------------------------------------

    def test_export_single_pipe(self, exporter, section_pipe):
        """Export a single pipe USER section."""
        exporter._export_sections([section_pipe], EU_SI)

    # ------------------------------------------------------------------
    # Tests – COMPOSITE / STEEL_I_TYPE1
    # ------------------------------------------------------------------

    def test_export_composite_steel_i_type1(self, exporter, section_composite_i_symmetric):
        """Export a composite steel-concrete I-girder type 1 (STEEL_I_TYPE1)."""
        exporter._export_sections([section_composite_i_symmetric], EU_SI)

    # ------------------------------------------------------------------
    # Tests – COMPOSITE / STEEL_I_TYPE2
    # ------------------------------------------------------------------

    def test_export_composite_steel_i_type2(self, exporter, section_composite_i_asymmetric):
        """Export a composite steel-concrete I-girder type 2 with inclined web (STEEL_I_TYPE2)."""
        exporter._export_sections([section_composite_i_asymmetric], EU_SI)

    # ------------------------------------------------------------------
    # Tests – PSC / PSC_1CELL
    # ------------------------------------------------------------------

    def test_export_single_psc_1cell_section(self, exporter, section_psc_1cell):
        """Export a single 1-cell prestressed concrete box girder (PSC_1CELL)."""
        exporter._export_sections([section_psc_1cell], EU_SI)

    # ------------------------------------------------------------------
    # Tests – PSC / PSC_2CELL
    # ------------------------------------------------------------------

    def test_export_single_psc_2cell_section(self, exporter, section_psc_2cells):
        """Export a single 2-cell prestressed concrete box girder (PSC_2CELL)."""
        exporter._export_sections([section_psc_2cells], EU_SI)

    # ------------------------------------------------------------------
    # Tests – PSC / PSC_VALUE
    # ------------------------------------------------------------------

    def test_export_single_psc_value_section(self, exporter, section_psc_value):
        """Export a single PSC_VALUE section (arbitrary polygon outlines)."""
        exporter._export_sections([section_psc_value], EU_SI)

    # ------------------------------------------------------------------
    # Tests – bulk / mixed exports
    # ------------------------------------------------------------------

    def test_export_all_user_sections(self, exporter, all_user_sections):
        """Export all six supported USER section types in a single call."""
        exporter._export_sections(all_user_sections, EU_SI)

    def test_export_all_composite_sections(self, exporter, all_composite_sections):
        """Export both supported COMPOSITE section types in a single call."""
        exporter._export_sections(all_composite_sections, EU_SI)

    def test_export_all_psc_sections(self, exporter, all_psc_sections):
        """Export both supported PSC section types in a single call."""
        exporter._export_sections(all_psc_sections, EU_SI)

    def test_export_mixed_sections(self, exporter, mixed_sections):
        """Export USER, COMPOSITE, and PSC sections together in one call."""
        exporter._export_sections(mixed_sections, EU_SI)

    # ------------------------------------------------------------------
    # Tests – unsupported section families (raise ValueError)
    # ------------------------------------------------------------------

    def test_export_raises_on_db_family(self, exporter, steel_material):
        """Exporting a DB (database/standard) section must raise ValueError.

        DB sections are not exported via the COM frame-property API;
        they are selected from the built-in CSI Bridge section library.
        """
        db_section = SectionDB(
            guid=str(uuid.uuid4()),
            name="TestDB_L203x203x22",
            section_type=SectionType.ANGLE,
            offset=Offset(OffsetReference.CENTER_CENTER),
            standard="AISC10(SI)",
            profile_name="L203X203X22.2",
        )
        db_section.set_id(99)
        with pytest.raises(ValueError, match="Unsupported section family"):
            exporter._write_sections([db_section], EU_SI)

    # ------------------------------------------------------------------
    # Tests – TAPERED sections
    # ------------------------------------------------------------------

    def test_export_tapered_linear(
        self, exporter, section_psc_1cell, section_psc_2cells, section_tapered_linear
    ):
        """Export a TAPERED section with LINEAR variation.

        Component PSC sections are exported first so that
        SetNonPrismatic can reference them by name.
        """
        exporter._export_sections([section_psc_1cell, section_psc_2cells], EU_SI)
        exporter._export_sections([section_tapered_linear], EU_SI)

    def test_export_tapered_parabolic(
        self, exporter, section_psc_1cell, section_psc_value, section_tapered_parabolic
    ):
        """Export a TAPERED section with PARABOLIC variation.

        Component PSC sections are exported first so that
        SetNonPrismatic can reference them by name.
        """
        exporter._export_sections([section_psc_1cell, section_psc_value], EU_SI)
        exporter._export_sections([section_tapered_parabolic], EU_SI)

    def test_export_tapered_cubic(
        self, exporter, section_psc_2cells, section_psc_value, section_tapered_cubic
    ):
        """Export a TAPERED section with CUBIC variation.

        Component PSC sections are exported first so that
        SetNonPrismatic can reference them by name.
        """
        exporter._export_sections([section_psc_2cells, section_psc_value], EU_SI)
        exporter._export_sections([section_tapered_cubic], EU_SI)


    # ------------------------------------------------------------------
    # Tests – wrong object type guards (raise ValueError inside handler)
    # ------------------------------------------------------------------

    def test_export_raises_when_user_section_dispatched_to_wrong_type(
        self, exporter, section_angle
    ):
        """Passing an ANGLE section while section_type claims BOX must raise ValueError.

        This tests the isinstance guard inside _export_box.
        """
        bad_section = section_angle
        object.__setattr__(bad_section, "section_type", SectionType.BOX)
        with pytest.raises(ValueError):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_raises_when_composite_section_has_wrong_object_type(
        self, exporter, section_angle
    ):
        """Passing a USER section while section_family claims COMPOSITE must raise ValueError.

        This tests the isinstance(section, SectionCompositeBase) guard inside _export_composite.
        """
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", SectionFamily.COMPOSITE)
        with pytest.raises(ValueError):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_raises_when_psc_section_has_wrong_object_type(
        self, exporter, section_angle
    ):
        """Passing a USER section while section_family claims PSC must raise ValueError.

        This tests the isinstance(section, SectionPSCBase) guard inside _export_psc.
        """
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", SectionFamily.PSC)
        with pytest.raises(ValueError):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_raises_when_tapered_section_has_wrong_object_type(
        self, exporter, section_angle
    ):
        """Passing a USER section while section_family claims TAPERED must raise ValueError.

        This tests the isinstance(section, SectionTapered) guard inside _export_tapered.
        """
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", SectionFamily.TAPERED)
        with pytest.raises(ValueError):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_sections_returns_false_when_export_failed(self, exporter, section_angle):
        """A failed section export must be reported by the return value, not by an exception."""
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", SectionFamily.PSC)

        assert exporter._export_sections([bad_section], EU_SI) is False, \
            "Failed section export should return False"

