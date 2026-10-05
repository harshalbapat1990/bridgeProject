"""Unit tests for the preparation of the model done before the export to analytical software."""

import uuid
from copy import deepcopy

import pytest

from bda.domain import AnalyticalMultiModel
from bda.domain.enums import TaperVariation, UnitSystem
from bda.domain.models.submodels.material import (
    DesignPropertiesConcrete,
    DesignPropertiesSteel,
    GeneralMaterialIsotropicProperties,
    MaterialConcrete,
    MaterialSteel,
)
from bda.domain.models.submodels.sections import (
    DimensionsCompositeSteelISymmetric,
    DimensionsISection,
    SectionCompositeSteelISymmetric,
    SectionStandardISection,
    SectionTapered,
)
from bda.domain.units.registry import ureg
from bda.infrastructure.adapters.analytical_software.exporters.common.section_materials import (
    SectionMaterialsResolver,
)
from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.model_preparation import (
    CsiModelPraparator,
)

m = ureg.meter
MPa = ureg.megapascal


@pytest.fixture
def steel_material():
    return MaterialSteel(
        name="S355",
        general_properties=GeneralMaterialIsotropicProperties(
            unit_weight=78.5 * ureg.kilonewton / m ** 3,
            modulus_of_elasticity=210000.0 * MPa,
            poissons_ratio=0.3,
            thermal_coefficient=1.2e-5 / ureg.delta_degC,
        ),
        design_properties=DesignPropertiesSteel(
            characteristic_yield_strength_fyk=355 * MPa,
            characteristic_ultimate_tensile_strength_fuk=490 * MPa,
            mean_yield_strength_fym=355 * MPa,
            mean_ultimate_tensile_strength_fum=490 * MPa,
        ),
    )


@pytest.fixture
def concrete_material():
    return MaterialConcrete(
        name="C35/45",
        general_properties=GeneralMaterialIsotropicProperties(
            unit_weight=25.0 * ureg.kilonewton / m ** 3,
            modulus_of_elasticity=34000.0 * MPa,
            poissons_ratio=0.2,
            thermal_coefficient=1.0e-5 / ureg.delta_degC,
        ),
        design_properties=DesignPropertiesConcrete(
            characteristic_compressive_strength_fck=35 * MPa,
            mean_compressive_strength_fcm=43 * MPa,
        ),
    )


def make_composite_section(name: str, source_id: str | None = None) -> SectionCompositeSteelISymmetric:
    return SectionCompositeSteelISymmetric(
        name=name,
        source_id=source_id,
        dimensions=DimensionsCompositeSteelISymmetric(
            slab_width_bc=3.0 * m,
            slab_thickness_tc=0.25 * m,
            slab_girder_spacing_hh=0.0 * m,
            girder_top_flange_width_b1=0.5 * m,
            girder_top_flange_thickness_tf1=0.03 * m,
            girder_bottom_flange_width_b2=0.6 * m,
            girder_bottom_flange_thickness_tf2=0.04 * m,
            girder_web_thickness_tw=0.016 * m,
            girder_web_height_hw=1.2 * m,
        ),
    )


def make_i_section(name: str, source_id: str | None = None) -> SectionStandardISection:
    return SectionStandardISection(
        name=name,
        source_id=source_id,
        dimensions=DimensionsISection(
            total_height_h=0.5 * m,
            top_flange_width_b1=0.2 * m,
            top_flange_thickness_tf1=0.02 * m,
            bottom_flange_width_b2=0.2 * m,
            bottom_flange_thickness_tf2=0.02 * m,
            web_thickness_tw=0.01 * m,
            web_inner_radius_r1=0.0 * m,
            flange_end_radius_r2=0.0 * m,
        ),
    )


def make_amm(sections, materials) -> AnalyticalMultiModel:
    amm = AnalyticalMultiModel(unit_system=UnitSystem.SI, project_id=1, structure_id=1,
                               structure_name="Test", description="Test")
    for material in materials:
        amm.add_initial_material(material)
    for section in sections:
        amm.add_initial_section(section)
    return amm


class TestFillMissingSectionMaterials:

    def test_materials_are_reused_from_a_copy_sharing_the_source_id(self, steel_material, concrete_material):
        """A source section takes the very same materials as its copy used by the model."""

        source_section = make_composite_section("girder", source_id="girder-source")

        used_copy = deepcopy(source_section)
        used_copy.set_material_main(steel_material)
        used_copy.set_material_composite(concrete_material)

        amm = make_amm([source_section, used_copy], [steel_material, concrete_material])

        SectionMaterialsResolver.fill_missing_section_materials(amm, "CSI Bridge")

        assert source_section.material_main is steel_material
        assert source_section.material_composite is concrete_material

    def test_existing_materials_are_not_overwritten(self, steel_material, concrete_material):
        """Materials already assigned, for example by the geometry module, are kept."""

        other_concrete = deepcopy(concrete_material)
        other_concrete.name = "C50/60"

        section = make_composite_section("girder", source_id="girder-source")
        section.set_material_main(steel_material)
        section.set_material_composite(other_concrete)

        donor = deepcopy(section)
        donor.set_material_composite(concrete_material)

        amm = make_amm([section, donor], [steel_material, concrete_material])

        SectionMaterialsResolver.fill_missing_section_materials(amm, "CSI Bridge")

        assert section.material_composite is other_concrete

    def test_tapered_components_share_materials_with_the_tapered_section(self, steel_material, concrete_material):
        """Start and end sections of a tapered section refer to the same material instances."""

        section_start = make_composite_section("girder_start")
        section_end = make_composite_section("girder_end")
        section_end.set_material_composite(concrete_material)

        tapered = SectionTapered(
            name="girder_tapered",
            section_start_id=section_start.guid,
            section_end_id=section_end.guid,
            taper_y_variation=TaperVariation.LINEAR,
            taper_z_variation=TaperVariation.LINEAR,
        )
        tapered.set_section_start(section_start)
        tapered.set_section_end(section_end)
        tapered.set_material_main(steel_material)

        amm = make_amm([tapered], [steel_material, concrete_material])

        SectionMaterialsResolver.fill_missing_section_materials(amm, "CSI Bridge")

        assert section_start.material_main is steel_material
        assert section_end.material_main is steel_material
        # the tapered section carries no composite material, so it is shared between the components
        assert section_start.material_composite is concrete_material

    def test_section_family_drives_the_fallback_material(self, steel_material, concrete_material):
        """A section without any counterpart gets the material typical for its family."""

        composite_section = make_composite_section("girder")
        steel_section = make_i_section("bracing")

        amm = make_amm([composite_section, steel_section], [concrete_material, steel_material])

        SectionMaterialsResolver.fill_missing_section_materials(amm, "CSI Bridge")

        assert composite_section.material_main is steel_material
        assert composite_section.material_composite is concrete_material
        assert steel_section.material_main is steel_material

    def test_model_without_materials_is_left_untouched(self):
        """Nothing can be assigned when the model has no materials at all."""

        section = make_composite_section("girder")
        amm = make_amm([section], [])

        SectionMaterialsResolver.fill_missing_section_materials(amm, "CSI Bridge")

        assert section.material_main is None
        assert section.material_composite is None


class TestCollectSectionsForExport:

    def test_tapered_component_sections_are_collected(self, steel_material):
        """Start and end sections are exported as well, although the model does not return them."""

        section_start = make_i_section("girder_start")
        section_end = make_i_section("girder_end")

        tapered = SectionTapered(
            name="girder_tapered",
            section_start_id=section_start.guid,
            section_end_id=section_end.guid,
            taper_y_variation=TaperVariation.LINEAR,
            taper_z_variation=TaperVariation.LINEAR,
        )
        tapered.set_section_start(section_start)
        tapered.set_section_end(section_end)

        amm = make_amm([tapered], [steel_material])

        collected = SectionMaterialsResolver.collect_sections_for_export(amm)

        assert [s.guid for s in collected] == [tapered.guid, section_start.guid, section_end.guid]


class TestEnsureUniqueSectionNames:

    def test_names_of_unused_sections_are_made_unique(self, steel_material):
        """Sections not used by any group are exported too, so their names must be unique as well."""

        first = make_i_section("girder")
        second = make_i_section("girder")

        amm = make_amm([first, second], [steel_material])

        CsiModelPraparator._ensure_unique_section_names(amm)

        assert first.name == "girder"
        assert second.name == "girder (1)"
