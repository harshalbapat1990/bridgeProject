"""
Integration tests for MIDAS Civil section export (_export_sections).

⚠️ WARNING: These tests require MIDAS Civil to be manually launched!
DO NOT RUN ON CI/CD - Only for local testing with real software running.

Prerequisites:
- MIDAS Civil NX installed and running
- Valid MIDAS Civil license
- Windows OS
- Correct path configured in infrastructure/config/exporters/midas_config.json
- MIDAS API key configured
- MIDAS Civil application launched manually before running tests

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
  - PSC_1CELL        → SectionPSC12Cell (1-cell box girder)
  - PSC_2CELL        → SectionPSC12Cell (2-cell box girder)
  - PSC_VALUE        → SectionPSCValue  (arbitrary polygon outlines)

TAPERED family:
  - LINEAR           → SectionTapered
  - PARABOLIC        → SectionTapered
  - CUBIC            → SectionTapered


Unsupported / invalid cases:
  - unsupported family string → ValueError
  - wrong object type dispatched to DB/USER/COMPOSITE/PSC/TAPERED handler
  - tapered section without exported base sections → ValueError
  - tapered section with different start/end type or family → ValueError
"""

import os
import uuid
from pathlib import Path

import pytest
from midas_civil import Model

from bda.domain.models.submodels.material import GeneralMaterialIsotropicProperties, DesignPropertiesConcrete, \
    DesignPropertiesSteel, MaterialSteel, MaterialConcrete
from bda.domain.models.submodels.section_base import Offset
from bda.infrastructure.adapters.analytical_software.exporters.midas_civil_exporter import MidasCivilExporter
from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider
from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession

from bda.domain.enums import (
    SectionFamily,
    SectionType,
    OffsetReference,
    TaperVariation,
)

from bda.domain.enums import UnitSystem

from bda.domain.models.submodels.sections.standard_shapes import (
    SectionStandardAngle,
    DimensionsAngle,
    SectionStandardBox,
    DimensionsBox,
    SectionStandardChannel,
    DimensionsChannel,
    SectionStandardSolidRound,
    DimensionsSolidRound,
    SectionStandardSolidRectangle,
    DimensionsSolidRectangle,
    SectionStandardISection,
    DimensionsISection, SectionStandardPipe, DimensionsPipe,
)
from bda.domain.models.submodels.sections.composite import (
    SectionCompositeSteelISymmetric,
    DimensionsCompositeSteelISymmetric,
    SectionCompositeSteelIAsymmetric,
    DimensionsCompositeSteelIAsymmetric,
)
from bda.domain.models.submodels.sections.psc import (
    SectionPSC12Cell,
    DimensionsPSC12Cell,
    SectionPSCValue,
    DimensionsPSCValues,
    JointsPSC,
    OuterHeightHo,
    OuterBreadthBo,
    InnerHeightHi,
    InnerBreadthBi,
    Point2D,
)
from bda.domain.models.submodels.sections.tapered import SectionTapered
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
# Module-level skip – MIDAS Civil not installed
# ---------------------------------------------------------------------------

def _get_midas_install_dir() -> str:
    try:
        config = MidasConfigProvider().load_config()
        exe_path = config.get("program_path")
        if exe_path:
            return str(Path(exe_path).parent)
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
class TestMidasCivilSectionExport:
    """Integration tests for section export to real MIDAS Civil.

    These tests mirror the CSI Bridge section-export integration tests,
    but are adapted to actual MIDAS exporter behavior:
    - DB sections are routed through MIDAS DB export path
    - tapered sections require same start/end type and family
    - tapered sections must have their base sections exported first
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
        """Create a fresh model before and after each test."""
        Model.create()
        yield
        Model.create()

    # ------------------------------------------------------------------
    # Fixtures – shared materials
    # ------------------------------------------------------------------

    @pytest.fixture
    def steel_material(self):
        """Custom steel material used as material_main for steel sections."""
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

    @pytest.fixture
    def concrete_material(self):
        """Custom concrete material used as material_main/material_composite."""
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

    # ------------------------------------------------------------------
    # Fixtures – USER sections
    # ------------------------------------------------------------------

    @pytest.fixture
    def section_angle(self, steel_material):
        """SectionUserAngle – L-profile 203×203×22 mm."""
        sec = SectionStandardAngle(
            guid=str(uuid.uuid4()),
            name="UsrAngle_L203x203x22",
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
    def section_angle_alt(self, steel_material):
        """Second ANGLE section used as end section for tapered tests."""
        sec = SectionStandardAngle(
            guid=str(uuid.uuid4()),
            name="UsrAngle_L250x180x20",
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsAngle(
                height=0.250 * m,
                width=0.180 * m,
                thickness_web=0.020 * m,
                thickness_flange=0.020 * m,
            ),
        )
        sec.set_id(7)
        sec.set_material_main(steel_material)
        return sec

    @pytest.fixture
    def section_box(self, steel_material):
        """SectionUserBox – closed rectangular hollow section 500×300 mm."""
        sec = SectionStandardBox(
            guid=str(uuid.uuid4()),
            name="UsrBox_500x300",
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
            name="UsrChannel_U550",
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
            name="UsrSolidRound_D180",
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
            name="UsrSolidRect_400x250",
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
    def section_i_section(self, steel_material):
        """SectionUserISection – asymmetric I-girder 1010 mm deep."""
        sec = SectionStandardISection(
            guid=str(uuid.uuid4()),
            name="UsrISection_1010",
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
        sec.set_id(6)
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
        sec.set_id(8)
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
            name="CompSteelI_Symmetric",
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
    def section_composite_i_symmetric_alt(self, steel_material, concrete_material):
        """Alternate SectionCompositeSteelISymmetric used as end section for tapered COMPOSITE tests."""
        sec = SectionCompositeSteelISymmetric(
            guid=str(uuid.uuid4()),
            name="CompSteelI_Symm_Alt",
            offset=Offset(OffsetReference.CENTER_TOP),
            dimensions=DimensionsCompositeSteelISymmetric(
                slab_width_bc=3.40 * m,
                slab_thickness_tc=0.24 * m,
                slab_girder_spacing_hh=0.06 * m,
                girder_top_flange_width_b1=0.40 * m,
                girder_top_flange_thickness_tf1=0.032 * m,
                girder_bottom_flange_width_b2=0.52 * m,
                girder_bottom_flange_thickness_tf2=0.045 * m,
                girder_web_thickness_tw=0.020 * m,
                girder_web_height_hw=1.35 * m,
            ),
        )
        sec.set_id(22)
        sec.set_material_main(steel_material)
        sec.set_material_composite(concrete_material)
        return sec

    @pytest.fixture
    def section_composite_i_asymmetric(self, steel_material, concrete_material):
        """SectionCompositeSteelIAsymmetric – composite steel-concrete I girder asymmetric."""
        sec = SectionCompositeSteelIAsymmetric(
            guid=str(uuid.uuid4()),
            name="CompSteelI_Asymmetric",
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
        """SectionPSC12Cell – 1-cell prestressed concrete box girder."""
        sec = SectionPSC12Cell(
            guid=str(uuid.uuid4()),
            name="PSC_1Cell",
            section_type=SectionType.PSC_1CELL,
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsPSC12Cell(
                joints=JointsPSC(
                    jo1=False, jo2=False, jo3=False,
                    ji1=False, ji2=False, ji3=False, ji4=False, ji5=False
                ),
                outer_height_ho=OuterHeightHo(
                    ho1=0.1 * m, ho2=0.2 * m, ho2_1=0.0 * m,
                    ho2_2=0.0 * m, ho3=1.2 * m, ho3_1=0.0 * m
                ),
                outer_breadth_bo=OuterBreadthBo(
                    bo1=1.0 * m, bo1_1=0.0 * m, bo1_2=0.0 * m,
                    bo2=1.0 * m, bo2_1=0.0 * m, bo3=1.0 * m
                ),
                inner_height_hi=InnerHeightHi(
                    hi1=0.1 * m, hi2=0.2 * m, hi2_1=0.0 * m, hi2_2=0.0 * m,
                    hi3=1.0 * m, hi3_1=0.0 * m, hi4=0.1 * m, hi4_1=0.0 * m,
                    hi4_2=0.0 * m, hi5=0.2 * m
                ),
                inner_breadth_bi=InnerBreadthBi(
                    bi1=1.5 * m, bi1_1=0.0 * m, bi1_2=0.0 * m,
                    bi2_1=0.0 * m, bi3=1.0 * m, bi3_1=0.0 * m,
                    bi3_2=0.0 * m, bi4=None
                ),
            ),
        )
        sec.set_id(30)
        sec.set_material_main(concrete_material)
        return sec

    @pytest.fixture
    def section_psc_2cell(self, concrete_material):
        """SectionPSC12Cell – 2-cell prestressed concrete box girder."""
        sec = SectionPSC12Cell(
            guid=str(uuid.uuid4()),
            name="PSC_2Cell",
            section_type=SectionType.PSC_2CELL,
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsPSC12Cell(
                joints=JointsPSC(
                    jo1=False, jo2=False, jo3=False,
                    ji1=False, ji2=False, ji3=False, ji4=False, ji5=False
                ),
                outer_height_ho=OuterHeightHo(
                    ho1=0.1 * m, ho2=0.2 * m, ho2_1=0.0 * m,
                    ho2_2=0.0 * m, ho3=1.2 * m, ho3_1=0.0 * m
                ),
                outer_breadth_bo=OuterBreadthBo(
                    bo1=1.0 * m, bo1_1=0.0 * m, bo1_2=0.0 * m,
                    bo2=1.0 * m, bo2_1=0.0 * m, bo3=1.0 * m
                ),
                inner_height_hi=InnerHeightHi(
                    hi1=0.1 * m, hi2=0.2 * m, hi2_1=0.0 * m, hi2_2=0.0 * m,
                    hi3=1.0 * m, hi3_1=0.0 * m, hi4=0.1 * m, hi4_1=0.0 * m,
                    hi4_2=0.0 * m, hi5=0.2 * m
                ),
                inner_breadth_bi=InnerBreadthBi(
                    bi1=1.5 * m, bi1_1=0.0 * m, bi1_2=0.0 * m,
                    bi2_1=0.0 * m, bi3=1.0 * m, bi3_1=0.0 * m,
                    bi3_2=0.0 * m, bi4=0.15 * m
                ),
            ),
        )
        sec.set_id(31)
        sec.set_material_main(concrete_material)
        return sec

    @pytest.fixture
    def section_psc_2cell_alt(self, concrete_material):
        """Alternate SectionPSC12Cell (2-cell) used as end section for tapered PSC tests."""
        sec = SectionPSC12Cell(
            guid=str(uuid.uuid4()),
            name="PSC_2Cell_Alt",
            section_type=SectionType.PSC_2CELL,
            offset=Offset(OffsetReference.CENTER_CENTER),
            dimensions=DimensionsPSC12Cell(
                joints=JointsPSC(
                    jo1=False, jo2=False, jo3=False,
                    ji1=False, ji2=False, ji3=False, ji4=False, ji5=False
                ),
                outer_height_ho=OuterHeightHo(
                    ho1=0.12 * m, ho2=0.22 * m, ho2_1=0.0 * m,
                    ho2_2=0.0 * m, ho3=1.35 * m, ho3_1=0.0 * m
                ),
                outer_breadth_bo=OuterBreadthBo(
                    bo1=1.20 * m, bo1_1=0.0 * m, bo1_2=0.0 * m,
                    bo2=1.10 * m, bo2_1=0.0 * m, bo3=1.15 * m
                ),
                inner_height_hi=InnerHeightHi(
                    hi1=0.12 * m, hi2=0.22 * m, hi2_1=0.0 * m, hi2_2=0.0 * m,
                    hi3=1.10 * m, hi3_1=0.0 * m, hi4=0.12 * m, hi4_1=0.0 * m,
                    hi4_2=0.0 * m, hi5=0.22 * m
                ),
                inner_breadth_bi=InnerBreadthBi(
                    bi1=1.60 * m, bi1_1=0.0 * m, bi1_2=0.0 * m,
                    bi2_1=0.0 * m, bi3=1.10 * m, bi3_1=0.0 * m,
                    bi3_2=0.0 * m, bi4=0.18 * m
                ),
            ),
        )
        sec.set_id(33)
        sec.set_material_main(concrete_material)
        return sec

    @pytest.fixture
    def section_psc_value(self, concrete_material):
        """SectionPSCValue – prestressed concrete section defined by explicit polygons."""
        outer_outline = [
            Point2D(x=-3.0 * m, y=0.00 * m),
            Point2D(x=3.0 * m, y=0.00 * m),
            Point2D(x=3.0 * m, y=-0.25 * m),
            Point2D(x=1.5 * m, y=-0.25 * m),
            Point2D(x=1.5 * m, y=-1.80 * m),
            Point2D(x=3.0 * m, y=-1.80 * m),
            Point2D(x=3.0 * m, y=-2.00 * m),
            Point2D(x=-3.0 * m, y=-2.00 * m),
            Point2D(x=-3.0 * m, y=-1.80 * m),
            Point2D(x=-1.5 * m, y=-1.80 * m),
            Point2D(x=-1.5 * m, y=-0.25 * m),
            Point2D(x=-3.0 * m, y=-0.25 * m),
        ]

        inner_outline_right = [
            Point2D(x=0.15 * m, y=-0.25 * m),
            Point2D(x=1.35 * m, y=-0.25 * m),
            Point2D(x=1.35 * m, y=-1.80 * m),
            Point2D(x=0.15 * m, y=-1.80 * m),
        ]

        inner_outline_left = [
            Point2D(x=-1.35 * m, y=-0.25 * m),
            Point2D(x=-0.15 * m, y=-0.25 * m),
            Point2D(x=-0.15 * m, y=-1.80 * m),
            Point2D(x=-1.35 * m, y=-1.80 * m),
        ]

        sec = SectionPSCValue(
            guid=str(uuid.uuid4()),
            name="PSC_Value",
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
    def section_tapered_linear(self, steel_material, section_angle, section_angle_alt):
        """SectionTapered – linear taper between two ANGLE sections."""
        sec = SectionTapered(
            guid=str(uuid.uuid4()),
            name="TapLinear_Angle",
            section_start_id="1",
            section_end_id="7",
            offset=Offset(OffsetReference.CENTER_CENTER),
            taper_y_variation=TaperVariation.LINEAR,
            taper_z_variation=TaperVariation.LINEAR,
        )
        sec.set_id(40)
        sec.set_material_main(steel_material)
        sec.set_section_start(section_angle)
        sec.set_section_end(section_angle_alt)
        return sec

    @pytest.fixture
    def section_tapered_parabolic(
        self,
        steel_material,
        section_composite_i_symmetric,
        section_composite_i_symmetric_alt,
    ):
        """SectionTapered – parabolic taper between two COMPOSITE STEEL_I_TYPE1 sections."""
        sec = SectionTapered(
            guid=str(uuid.uuid4()),
            name="TapParabolic_Composite",
            section_start_id="20",
            section_end_id="22",
            offset=Offset(OffsetReference.CENTER_CENTER),
            taper_y_variation=TaperVariation.PARABOLIC,
            taper_z_variation=TaperVariation.PARABOLIC,
        )
        sec.set_id(41)
        sec.set_material_main(steel_material)
        sec.set_section_start(section_composite_i_symmetric)
        sec.set_section_end(section_composite_i_symmetric_alt)
        return sec

    @pytest.fixture
    def section_tapered_cubic(
        self,
        concrete_material,
        section_psc_2cell,
        section_psc_2cell_alt,
    ):
        """SectionTapered – cubic taper between two PSC_2CELL sections."""
        sec = SectionTapered(
            guid=str(uuid.uuid4()),
            name="TapCubic_PSC",
            section_start_id="31",
            section_end_id="33",
            offset=Offset(OffsetReference.CENTER_CENTER),
            taper_y_variation=TaperVariation.CUBIC,
            taper_z_variation=TaperVariation.CUBIC,
        )
        sec.set_id(42)
        sec.set_material_main(concrete_material)
        sec.set_section_start(section_psc_2cell)
        sec.set_section_end(section_psc_2cell_alt)
        return sec

    @pytest.fixture
    def section_tapered_invalid_type(self, steel_material, section_angle, section_box):
        """Invalid tapered section: start/end have different section types."""
        sec = SectionTapered(
            guid=str(uuid.uuid4()),
            name="TapInvalid_AngleToBox",
            section_start_id="1",
            section_end_id="2",
            offset=Offset(OffsetReference.CENTER_CENTER),
            taper_y_variation=TaperVariation.LINEAR,
            taper_z_variation=TaperVariation.LINEAR,
        )
        sec.set_id(43)
        sec.set_material_main(steel_material)
        sec.set_section_start(section_angle)
        sec.set_section_end(section_box)
        return sec

    # ------------------------------------------------------------------
    # Fixtures – combined section lists
    # ------------------------------------------------------------------

    @pytest.fixture
    def all_user_sections(
        self,
        section_angle,
        section_box,
        section_channel,
        section_solid_round,
        section_solid_rectangle,
        section_i_section,
        section_pipe
    ):
        """All six supported USER section types in one list."""
        return [
            section_angle,
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
        section_psc_2cell,
        section_psc_value,
    ):
        """All supported PSC section types in one list."""
        return [section_psc_1cell, section_psc_2cell, section_psc_value]

    @pytest.fixture
    def mixed_sections(self, all_user_sections, all_composite_sections, all_psc_sections):
        """All USER, COMPOSITE, and PSC sections combined in one list."""
        return all_user_sections + all_composite_sections + all_psc_sections

    @pytest.fixture
    def mixed_sections_with_tapered(
        self,
        all_user_sections,
        section_angle_alt,
        all_composite_sections,
        all_psc_sections,
        section_tapered_linear,
    ):
        """Mixed export including a tapered section.

        `_export_sections()` should export non-tapered sections first and
        tapered sections last.
        """
        return (
            all_user_sections
            + [section_angle_alt]
            + all_composite_sections
            + all_psc_sections
            + [section_tapered_linear]
        )

    # ------------------------------------------------------------------
    # Tests – empty input
    # ------------------------------------------------------------------

    def test_export_empty_list_does_not_raise(self, exporter):
        """Exporting an empty sections list must complete without errors."""
        exporter._export_sections([], EU_SI)

    # ------------------------------------------------------------------
    # Tests – USER
    # ------------------------------------------------------------------

    def test_export_single_angle_section(self, exporter, section_angle):
        exporter._export_sections([section_angle], EU_SI)

    def test_export_single_box_section(self, exporter, section_box):
        exporter._export_sections([section_box], EU_SI)

    def test_export_single_channel_section(self, exporter, section_channel):
        exporter._export_sections([section_channel], EU_SI)

    def test_export_single_solid_round_section(self, exporter, section_solid_round):
        exporter._export_sections([section_solid_round], EU_SI)

    def test_export_single_solid_rectangle_section(self, exporter, section_solid_rectangle):
        exporter._export_sections([section_solid_rectangle], EU_SI)

    def test_export_single_i_section(self, exporter, section_i_section):
        exporter._export_sections([section_i_section], EU_SI)

    def test_export_single_pipe(self, exporter, section_pipe):
        exporter._export_sections([section_pipe], EU_SI)
        Model.create()

    # ------------------------------------------------------------------
    # Tests – COMPOSITE
    # ------------------------------------------------------------------

    def test_export_composite_steel_i_symmetric(self, exporter, section_composite_i_symmetric):
        exporter._export_sections([section_composite_i_symmetric], EU_SI)
        Model.create()

    def test_export_composite_steel_i_asymmetric(self, exporter, section_composite_i_asymmetric):
        exporter._export_sections([section_composite_i_asymmetric], EU_SI)
        Model.create()

    # ------------------------------------------------------------------
    # Tests – PSC
    # ------------------------------------------------------------------

    def test_export_single_psc_1cell_section(self, exporter, section_psc_1cell):
        exporter._export_sections([section_psc_1cell], EU_SI)

    def test_export_single_psc_2cell_section(self, exporter, section_psc_2cell):
        exporter._export_sections([section_psc_2cell], EU_SI)

    def test_export_single_psc_value_section(self, exporter, section_psc_value):
        exporter._export_sections([section_psc_value], EU_SI)

    # ------------------------------------------------------------------
    # Tests – bulk / mixed exports
    # ------------------------------------------------------------------

    def test_export_mixed_sections_with_tapered(self, exporter, mixed_sections_with_tapered):
        """Export mixed list with tapered section in the same call."""
        exporter._export_sections(mixed_sections_with_tapered, EU_SI)

    # ------------------------------------------------------------------
    # Tests – TAPERED sections
    # ------------------------------------------------------------------

    def test_export_tapered_dbuser(
        self, exporter, section_angle, section_angle_alt, section_tapered_linear
    ):
        exporter._export_sections([section_angle, section_angle_alt], EU_SI)
        exporter._export_sections([section_tapered_linear], EU_SI)

    def test_export_tapered_composite(
        self,
        exporter,
        section_composite_i_symmetric,
        section_composite_i_symmetric_alt,
        section_tapered_parabolic,
    ):
        exporter._export_sections(
            [section_composite_i_symmetric, section_composite_i_symmetric_alt],
            EU_SI,
        )
        exporter._export_sections([section_tapered_parabolic], EU_SI)

    def test_export_tapered_psc(
        self,
        exporter,
        section_psc_2cell,
        section_psc_2cell_alt,
        section_tapered_cubic,
    ):
        exporter._export_sections([section_psc_2cell, section_psc_2cell_alt], EU_SI)
        exporter._export_sections([section_tapered_cubic], EU_SI)

    # ------------------------------------------------------------------
    # Tests – invalid / unsupported cases
    # ------------------------------------------------------------------

    def test_export_raises_on_unsupported_family(self, exporter, section_angle):
        """Unknown family should fail before dispatch."""
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", "unsupported_family")

        with pytest.raises(ValueError, match="Unsupported section family"):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_raises_when_db_section_has_wrong_object_type(self, exporter, section_angle):
        """Passing USER object while family claims DB must raise ValueError."""
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", SectionFamily.DB)

        with pytest.raises(ValueError):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_raises_when_user_section_dispatched_to_wrong_type(
        self, exporter, section_angle
    ):
        """Passing ANGLE section while section_type claims BOX must raise ValueError."""
        bad_section = section_angle
        object.__setattr__(bad_section, "section_type", SectionType.BOX)

        with pytest.raises(ValueError):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_raises_when_composite_section_has_wrong_object_type(
        self, exporter, section_angle
    ):
        """Passing USER object while family claims COMPOSITE must raise ValueError."""
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", SectionFamily.COMPOSITE)

        with pytest.raises(ValueError):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_raises_when_psc_section_has_wrong_object_type(
        self, exporter, section_angle
    ):
        """Passing USER object while family claims PSC must raise ValueError."""
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", SectionFamily.PSC)

        with pytest.raises(ValueError):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_raises_when_tapered_section_has_wrong_object_type(
        self, exporter, section_angle
    ):
        """Passing USER object while family claims TAPERED must raise ValueError."""
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", SectionFamily.TAPERED)

        with pytest.raises(ValueError):
            exporter._write_sections([bad_section], EU_SI)

    def test_export_raises_when_tapered_base_sections_were_not_exported_first(
        self, exporter, section_tapered_linear
    ):
        """Tapered export requires base sections to exist in the current MIDAS model."""
        Model.clear()
        with pytest.raises(ValueError, match=r".*Base sections for tapered section have not been found.*"):
            exporter._write_sections([section_tapered_linear], EU_SI)

    def test_export_raises_when_tapered_start_and_end_have_different_types(
        self, exporter, section_angle, section_box, section_tapered_invalid_type
    ):
        """MIDAS tapered export requires same start/end section_type and section_family."""
        exporter._export_sections([section_angle, section_box], EU_SI)

        with pytest.raises(
            ValueError,
            match="Start and end section type and section family must be the same",
        ):
            exporter._write_sections([section_tapered_invalid_type], EU_SI)

    def test_export_sections_returns_false_when_export_failed(self, exporter, section_angle):
        """A failed section export must be reported by the return value, not by an exception."""
        bad_section = section_angle
        object.__setattr__(bad_section, "section_family", "unsupported_family")

        assert exporter._export_sections([bad_section], EU_SI) is False, \
            "Failed section export should return False"