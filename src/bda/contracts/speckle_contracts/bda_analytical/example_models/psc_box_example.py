"""PSC box example model.

Built from the fixtures in tests/unit/fixtures/mvp_cases/psc-box using the
speckle contract ``.create()`` methods, following the same pattern as
steel_composite_example.py.

Notes on fidelity to the fixture:
- The fixture references materials/sections by GUID or free-form name
  (e.g. "psc-box-section-low", "0a319344-..."). Contract applicationIds are
  regex-constrained (e.g. ``SECT-0001-PSC-VALUE``, ``MAT-0001-CONC-AASHTO``),
  so those free-form ids have been mapped to contract-compliant applicationIds
  below (see the id maps in each section).
- Each box girder has a tendon group ("tendon-group" in the fixture), built
  via ``GeometryGroupTendonGroup``. The fixture doesn't define a tendon
  material or section, so a representative AASHTO strand material and the
  fixture's "dummy" solid-circle section are used (see the id maps below).
- Pier_3 in the fixture has no ``foundation_details`` / pile list under its
  Below Ground group (unlike Abutment_0, Pier_1 and Pier_2), only a pile cap.
  This is mirrored as-is: Pier_3's below ground has a pile cap but no piles.
- Pier_3's above-ground "Details" state ``no_of_piers: 2`` but only one pier
  (``pier_3_1``) is listed; this is mirrored as-is from the fixture.
"""

import datetime

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_bridge import (
    GeometryGroupBridge,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_superstructure import (
    GeometryGroupSuperstructure,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_span import (
    GeometryGroupSpan,
    TaperedDetailsParameterGroup,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_longitudinal_members import (
    GeometryGroupLongitudinalMembers,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_girder import (
    GeometryGroupGirder,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_substructure import (
    GeometryGroupSubstructure,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_support import (
    GeometryGroupSupport,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_above_ground import (
    GeometryGroupAboveGround,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_below_ground import (
    GeometryGroupBelowGround,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_vertical_members import (
    GeometryGroupVerticalMembersAboveGround,
    GeometryGroupVerticalMembersBelowGround,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_horizontal_members import (
    GeometryGroupHorizontalMembersAboveGround,
    GeometryGroupHorizontalMembersBelowGround,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_wall import (
    GeometryGroupWall,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_pier import (
    GeometryGroupPier,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_pile import (
    GeometryGroupPile,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_pile_cap import (
    GeometryGroupPileCap,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_crossbeam import (
    GeometryGroupCrossbeam,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_linkage import (
    GeometryGroupLinkage,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_superstructure_to_substructure_connections import (
    GeometryGroupSuperstructureToSubstructureConnections,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_tendon_group import (
    GeometryGroupTendonGroup,
)

from bda.contracts.paramodel.groups.enums import (
    SpacingTypeParaModel,
    BridgeTypeParaModel,
    BridgeIdealisationParaModel,
    ElementOrientationParaModel,
    SupportTypeParaModel,
    FoundationTypeParaModel,
    BearingConfigurationTypeParaModel,
    DofTypeEnumParaModel,
)
from bda.contracts.paramodel.sections.sections_para_models import (
    SectionTypeParaModel,
    TaperVariationParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.model_root import ModelRootCollection
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_DataObject import (
    BDA_ModelDataDataObject,
    ModelUnitSystemEnum,
    OutputSoftwareEnum,
    DesignCodesEnum,
    StructureTypeEnum,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.materials_collection import (
    MaterialsCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.materials.concrete.concrete_material_aashto import (
    ConcreteAASHTOMaterialDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.materials.tendon.tendon_material_aashto import (
    TendonAASHTOMaterialDataObject,
)

from bda.contracts.speckle_contracts.bda_analytical.sections.section_collection import (
    SectionsCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.solid_circle_data_object import (
    SectionDataObject_SolidCircle,
)
from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.solid_rectangle_data_object import (
    SectionDataObject_SolidRectangle,
)
from bda.contracts.speckle_contracts.bda_analytical.sections.psc_family.psc_section_types.psc_value_type_data_object import (
    SectionDataObject_PSCValue,
)
from bda.contracts.speckle_contracts.bda_analytical.sections.taper_section_group import (
    SectionDataObject_Tapered,
)

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.boundary_conditions_collection import (
    BoundaryConditionsCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_bc_collection import (
    BearingBCCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_bc_data_object import (
    BearingBCDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.spring_parameters import (
    BoundaryConditionSpringParameterGroup,
)


###############################################################################################
# MATERIALS
###############################################################################################
# fixture material_id (GUID) -> contract applicationId
#   0a319344-c9e3-45db-b840-24310be69c22 (C5000)              -> MAT-0001-CONC-AASHTO
#   443913a0-c9e3-45db-b840-24310be69c22 (C5000_substructure) -> MAT-0002-CONC-AASHTO
#   443913a0-c9e3-45db-b840-22c96eb01342 (C5000_piles)        -> MAT-0003-CONC-AASHTO
#   (tendon strand - not in fixture)                          -> MAT-0004-TENDON-AASHTO

deck_concrete = ConcreteAASHTOMaterialDataObject.create(
    name="C5000",
    application_id="MAT-0001-CONC-AASHTO",
    unit_weight=25,
    unit_weight_unit="kN/m³",
    poissons_ratio=0.2,
    modulus_of_elasticity=20.5,
    elasticity_unit="GPa",
    coefficient_of_thermal_expansion=6.667e-6,
    thermal_coefficient_unit="1/Δ°F",
    expected_concrete_strength=50000,
    specified_concrete_strength=40000,
    concrete_strength_unit="kN/m²",
)

substructure_concrete = ConcreteAASHTOMaterialDataObject.create(
    name="C5000_substructure",
    application_id="MAT-0002-CONC-AASHTO",
    unit_weight=25,
    unit_weight_unit="kN/m³",
    poissons_ratio=0.2,
    modulus_of_elasticity=20.5,
    elasticity_unit="GPa",
    coefficient_of_thermal_expansion=6.667e-6,
    thermal_coefficient_unit="1/Δ°F",
    expected_concrete_strength=37000,
    specified_concrete_strength=30000,
    concrete_strength_unit="kN/m²",
)

piles_concrete = ConcreteAASHTOMaterialDataObject.create(
    name="C5000_piles",
    application_id="MAT-0003-CONC-AASHTO",
    unit_weight=25,
    unit_weight_unit="kN/m³",
    poissons_ratio=0.2,
    modulus_of_elasticity=20.5,
    elasticity_unit="GPa",
    coefficient_of_thermal_expansion=6.667e-6,
    thermal_coefficient_unit="1/Δ°F",
    expected_concrete_strength=37000,
    specified_concrete_strength=30000,
    concrete_strength_unit="kN/m²",
)

tendon_strand = TendonAASHTOMaterialDataObject.create(
    name="AASHTO 1860 MPa Strand",
    application_id="MAT-0004-TENDON-AASHTO",
    unit_weight=77.0,
    unit_weight_unit="kN/m³",
    modulus_of_elasticity=195,
    elasticity_unit="GPa",
    poissons_ratio=0.30,
    coefficient_of_thermal_expansion=1.2e-5,
    thermal_coefficient_unit="1/Δ°F",
    tendon_yield_strength=1670e6,
    tendon_specified_minimum_tensile_strength=1860e6,
    strength_unit="kN/m²",
)

materials_collection = MaterialsCollection.create(
    application_id="COL-MATERIALS",
    materials=[
        deck_concrete,
        substructure_concrete,
        piles_concrete,
        tendon_strand,
    ],
)


###############################################################################################
# SECTIONS
###############################################################################################
# fixture section_id -> contract applicationId
#   pile_section                     -> SECT-0001-STANDARD-SOLID-CIRCLE
#   pier-section                     -> SECT-0002-STANDARD-SOLID-CIRCLE
#   rec_1.2x1.2                      -> SECT-0003-STANDARD-SOLID-RECTANGLE
#   pilecap                          -> SECT-0004-STANDARD-SOLID-RECTANGLE
#   crossbeam-high                   -> SECT-0005-STANDARD-SOLID-RECTANGLE
#   crossbeam-low                    -> SECT-0006-STANDARD-SOLID-RECTANGLE
#   crossbeam-tapered-high-to-low    -> SECT-0007-TAPERED
#   crossbeam-tapered-low-to-high    -> SECT-0008-TAPERED
#   (abutment wall - not in fixture) -> SECT-0009-STANDARD-SOLID-RECTANGLE
#   psc-box-section-low              -> SECT-0010-PSC-VALUE
#   psc-box-section-high             -> SECT-0011-PSC-VALUE
#   tapered-high-to-low              -> SECT-0012-TAPERED
#   tapered-low-to-high              -> SECT-0013-TAPERED
#   dummy                            -> SECT-0014-STANDARD-SOLID-CIRCLE

pile_section = SectionDataObject_SolidCircle.create(
    name="pile_section",
    description="Pile section",
    application_id="SECT-0001-STANDARD-SOLID-CIRCLE",
    diameter=1.20,
    unit="m",
)

pier_section = SectionDataObject_SolidCircle.create(
    name="pier-section",
    description="Pier section",
    application_id="SECT-0002-STANDARD-SOLID-CIRCLE",
    diameter=2.00,
    unit="m",
)

pier_1_section = SectionDataObject_SolidRectangle.create(
    name="rec_1.2x1.2",
    description="Pier 1 rectangular column section",
    application_id="SECT-0003-STANDARD-SOLID-RECTANGLE",
    height=1.20,
    width=1.20,
    unit="m",
)

pilecap_section = SectionDataObject_SolidRectangle.create(
    name="pilecap",
    description="Pile cap section",
    application_id="SECT-0004-STANDARD-SOLID-RECTANGLE",
    height=2.50,
    width=6.00,
    unit="m",
)

crossbeam_high_section = SectionDataObject_SolidRectangle.create(
    name="crossbeam-high",
    description="Crossbeam section at piers",
    application_id="SECT-0005-STANDARD-SOLID-RECTANGLE",
    height=3.00,
    width=2.00,
    unit="m",
)

crossbeam_low_section = SectionDataObject_SolidRectangle.create(
    name="crossbeam-low",
    description="Crossbeam section at piers (tapered end)",
    application_id="SECT-0006-STANDARD-SOLID-RECTANGLE",
    height=1.25,
    width=2.00,
    unit="m",
)

crossbeam_tapered_high_to_low = SectionDataObject_Tapered.create(
    name="cross-h2l",
    application_id="SECT-0007-TAPERED",
    start_section_application_id="SECT-0005-STANDARD-SOLID-RECTANGLE",
    end_section_application_id="SECT-0006-STANDARD-SOLID-RECTANGLE",
    section_type=SectionTypeParaModel.SOLID_RECTANGLE,
    taper_y_variation=TaperVariationParaModel.LINEAR,
    taper_z_variation=TaperVariationParaModel.PARABOLIC,
)

crossbeam_tapered_low_to_high = SectionDataObject_Tapered.create(
    name="cross-l2h",
    application_id="SECT-0008-TAPERED",
    start_section_application_id="SECT-0006-STANDARD-SOLID-RECTANGLE",
    end_section_application_id="SECT-0005-STANDARD-SOLID-RECTANGLE",
    section_type=SectionTypeParaModel.SOLID_RECTANGLE,
    taper_y_variation=TaperVariationParaModel.LINEAR,
    taper_z_variation=TaperVariationParaModel.PARABOLIC,
)

abutment_wall_section = SectionDataObject_SolidRectangle.create(
    name="abutment_wall_section",
    description="Abutment stem wall section (not present in fixture; added to satisfy the wall's required section)",
    application_id="SECT-0009-STANDARD-SOLID-RECTANGLE",
    height=1.50,
    width=6.00,
    unit="m",
)

psc_box_section_low = SectionDataObject_PSCValue.create(
    name="psc_box_low",
    description="PSC box girder section - low (non-haunched) end",
    application_id="SECT-0010-PSC-VALUE",
    external_polygon=[
        (-6.0, 2.5),
        (6.0, 2.5),
        (6.0, 2.35),
        (5.0, 2.3),
        (4.5, 2.25),
        (3.6974, 2.1),
        (2.75, 0.3),
        (2.75, 0.0),
        (-2.75, 0.0),
        (-2.75, 0.3),
        (-3.6974, 2.1),
        (-4.5, 2.25),
        (-5.0, 2.3),
        (-6.0, 2.35),
    ],
    internal_polygons={
        "Void 1": [
            (-0.25, 2.2),
            (-1.8323, 2.2),
            (-2.8323, 2.1),
            (-2.9926, 1.8345),
            (-2.351, 0.6155),
            (-1.9113, 0.35),
            (-1.1613, 0.3),
            (-0.25, 0.3),
        ],
        "Void 2": [
            (2.8323, 2.1),
            (1.8323, 2.2),
            (0.25, 2.2),
            (0.25, 0.3),
            (1.1613, 0.3),
            (1.9113, 0.35),
            (2.351, 0.6155),
            (2.9926, 1.8345),
        ],
    },
    unit="m",
)

psc_box_section_high = SectionDataObject_PSCValue.create(
    name="psc_box_high",
    description="PSC box girder section - high (haunched) end",
    application_id="SECT-0011-PSC-VALUE",
    external_polygon=[
        (-6.0, 4.5),
        (6.0, 4.5),
        (6.0, 4.35),
        (5.0, 4.3),
        (4.5, 4.25),
        (3.6974, 4.1),
        (2.75, 0.3),
        (2.75, 0.0),
        (-2.75, 0.0),
        (-2.75, 0.3),
        (-3.6974, 4.1),
        (-4.5, 4.25),
        (-5.0, 4.3),
        (-6.0, 4.35),
    ],
    internal_polygons={
        "Void 1": [
            (-0.25, 4.2),
            (-1.8323, 4.2),
            (-2.8323, 4.1),
            (-2.9926, 3.8345),
            (-2.351, 0.6155),
            (-1.9113, 0.35),
            (-1.1613, 0.3),
            (-0.25, 0.3),
        ],
        "Void 2": [
            (2.8323, 4.1),
            (1.8323, 4.2),
            (0.25, 4.2),
            (0.25, 0.3),
            (1.1613, 0.3),
            (1.9113, 0.35),
            (2.351, 0.6155),
            (2.9926, 3.8345),
        ],
    },
    unit="m",
)

tapered_high_to_low = SectionDataObject_Tapered.create(
    name="tapered_1",
    application_id="SECT-0012-TAPERED",
    start_section_application_id="SECT-0011-PSC-VALUE",
    end_section_application_id="SECT-0010-PSC-VALUE",
    section_type=SectionTypeParaModel.PSC_VALUE,
    taper_y_variation=TaperVariationParaModel.PARABOLIC,
    taper_z_variation=TaperVariationParaModel.PARABOLIC,
)

tapered_low_to_high = SectionDataObject_Tapered.create(
    name="tapered_2",
    application_id="SECT-0013-TAPERED",
    start_section_application_id="SECT-0010-PSC-VALUE",
    end_section_application_id="SECT-0011-PSC-VALUE",
    section_type=SectionTypeParaModel.PSC_VALUE,
    taper_y_variation=TaperVariationParaModel.PARABOLIC,
    taper_z_variation=TaperVariationParaModel.PARABOLIC,
)

tendon_section = SectionDataObject_SolidCircle.create(
    name="dummy",
    description="Tendon duct section (fixture placeholder section)",
    application_id="SECT-0014-STANDARD-SOLID-CIRCLE",
    diameter=0.1,
    unit="m",
)

section_collection = SectionsCollection.create(
    application_id="COL-SECTIONS",
    sections=[
        pile_section,
        pier_section,
        pier_1_section,
        pilecap_section,
        crossbeam_high_section,
        crossbeam_low_section,
        crossbeam_tapered_high_to_low,
        crossbeam_tapered_low_to_high,
        abutment_wall_section,
        psc_box_section_low,
        psc_box_section_high,
        tapered_high_to_low,
        tapered_low_to_high,
        tendon_section,
    ],
)


###############################################################################################
# SUPERSTRUCTURE - SPANS
###############################################################################################

tendon_span_1 = GeometryGroupTendonGroup.create(
    name="tendon_span_1",
    application_id="COL-GEOMGROUP-0001-TENDON-GROUP",
    material_id="MAT-0004-TENDON-AASHTO",
    section_id="SECT-0014-STANDARD-SOLID-CIRCLE",
)

longitudinal_span_1 = GeometryGroupLongitudinalMembers.create(
    application_id="COL-GEOMGROUP-0001-LONGITUDINAL-MEMBERS",
    girders=[
        GeometryGroupGirder.create(
            name="box_girder_1",
            application_id="COL-GEOMGROUP-0001-GIRDER",
            material_id="MAT-0001-CONC-AASHTO",
            section_id="SECT-0010-PSC-VALUE",
            girder_index=0,
            tendon_groups=[tendon_span_1],
        ),
    ],
)

span_1 = GeometryGroupSpan.create(
    application_id="COL-GEOMGROUP-0001-SPAN",
    name="Span_1",
    span_index=0,
    span_length=30.0,
    top_deck_level_at_end=122.0,
    tapered_details=TaperedDetailsParameterGroup.create(
        tapers=[
            (20.0, 27.0, "SECT-0013-TAPERED"),
        ],
    ),
    longitudinal_members=longitudinal_span_1,
)

tendon_span_2 = GeometryGroupTendonGroup.create(
    name="tendon_span_2",
    application_id="COL-GEOMGROUP-0002-TENDON-GROUP",
    material_id="MAT-0004-TENDON-AASHTO",
    section_id="SECT-0014-STANDARD-SOLID-CIRCLE",
)

longitudinal_span_2 = GeometryGroupLongitudinalMembers.create(
    application_id="COL-GEOMGROUP-0002-LONGITUDINAL-MEMBERS",
    girders=[
        GeometryGroupGirder.create(
            name="Box_girder_2",
            application_id="COL-GEOMGROUP-0002-GIRDER",
            material_id="MAT-0001-CONC-AASHTO",
            section_id="SECT-0010-PSC-VALUE",
            girder_index=1,
            tendon_groups=[tendon_span_2],
        ),
    ],
)

span_2 = GeometryGroupSpan.create(
    application_id="COL-GEOMGROUP-0002-SPAN",
    name="Span_2",
    span_index=1,
    span_length=50.0,
    top_deck_level_at_end=121.0,
    tapered_details=TaperedDetailsParameterGroup.create(
        tapers=[
            (3.0, 10.0, "SECT-0012-TAPERED"),
            (40.0, 47.0, "SECT-0013-TAPERED"),
        ],
    ),
    longitudinal_members=longitudinal_span_2,
)

tendon_span_3 = GeometryGroupTendonGroup.create(
    name="tendon_span_3",
    application_id="COL-GEOMGROUP-0003-TENDON-GROUP",
    material_id="MAT-0004-TENDON-AASHTO",
    section_id="SECT-0014-STANDARD-SOLID-CIRCLE",
)

longitudinal_span_3 = GeometryGroupLongitudinalMembers.create(
    application_id="COL-GEOMGROUP-0003-LONGITUDINAL-MEMBERS",
    girders=[
        GeometryGroupGirder.create(
            name="Box_girder_3",
            application_id="COL-GEOMGROUP-0003-GIRDER",
            material_id="MAT-0001-CONC-AASHTO",
            section_id="SECT-0010-PSC-VALUE",
            girder_index=2,
            tendon_groups=[tendon_span_3],
        ),
    ],
)

span_3 = GeometryGroupSpan.create(
    application_id="COL-GEOMGROUP-0003-SPAN",
    name="Span_3",
    span_index=2,
    span_length=30.0,
    top_deck_level_at_end=120.0,
    tapered_details=TaperedDetailsParameterGroup.create(
        tapers=[
            (3.0, 10.0, "SECT-0012-TAPERED"),
        ],
    ),
    longitudinal_members=longitudinal_span_3,
)

superstructure = GeometryGroupSuperstructure.create(
    application_id="COL-GEOMGROUP-0001-SUPERSTRUCTURE",
    name="Main Superstructure",
    total_deck_width=12.0,
    # The fixture states no_of_girders=3, but this deck has a single PSC box
    # girder line running continuously across all 3 spans (segmented per span
    # for tapering/construction, not 3 parallel girders). 3 appears to double
    # count "one girder segment per span" as "3 girders" - corrected to 1 here
    # so the model is dimensionally sensible; see the discrepancy notes below.
    number_of_girders=1,
    girder_spacing_type=SpacingTypeParaModel.UNIFORM,
    girder_spacing_values=[],
    stringcourse_left_barrier_width=0.6,
    stringcourse_right_barrier_width=0.6,
    cantilever_left_width=6.0,
    cantilever_right_width=6.0,
    spans=[span_1, span_2, span_3],
)


###############################################################################################
# SUBSTRUCTURE - ABUTMENT 0
###############################################################################################

abutment_0_wall = GeometryGroupWall.create(
    name="abutment wall",
    application_id="COL-GEOMGROUP-0001-WALL",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0009-STANDARD-SOLID-RECTANGLE",
    element_thickness=1.5,
)

abutment_0_above_ground = GeometryGroupAboveGround.create(
    application_id="COL-GEOMGROUP-0001-ABOVE-GROUND",
    support_type=SupportTypeParaModel.SOLID_TYPE,
    number_of_walls=1,
    vertical_members=GeometryGroupVerticalMembersAboveGround.create(
        application_id="COL-GEOMGROUP-0001-VERTICAL-MEMBERS",
        walls=[abutment_0_wall],
    ),
)

abutment_0_piles = [
    GeometryGroupPile.create(
        name=name,
        application_id=f"COL-GEOMGROUP-{i + 1:04d}-PILE",
        material_id="MAT-0003-CONC-AASHTO",
        section_id="SECT-0001-STANDARD-SOLID-CIRCLE",
        pile_index=i,
        pile_length=12.0,
        offset_along_support_line=offset_along,
        offset_normal_to_support_line=offset_normal,
        spring_spacing=spring_spacing,
    )
    for i, (name, offset_along, offset_normal, spring_spacing) in enumerate(
        [
            # "0ile_0_1" is the fixture's own (typo'd) name, mirrored as-is.
            ("0ile_0_1", 0.0, 0.0, [2.5] * 6),
            ("Pile_0_2", 3.5, 1.5, [1.0]),
            ("Pile_0_3", 3.5, -1.5, [1.0]),
            ("Pile_0_4", -3.5, 1.5, [1.0]),
            ("Pile_0_5", -3.5, -1.5, [1.0]),
        ]
    )
]

abutment_0_pile_cap = GeometryGroupPileCap.create(
    name="Pilecap1",
    application_id="COL-GEOMGROUP-0001-PILE-CAP",
    material_id="MAT-0003-CONC-AASHTO",
    section_id="SECT-0004-STANDARD-SOLID-RECTANGLE",
    top_of_pile_cap_level=101.5,
    element_length=10.0,
)

abutment_0_below_ground = GeometryGroupBelowGround.create(
    application_id="COL-GEOMGROUP-0001-BELOW-GROUND",
    foundation_type=FoundationTypeParaModel.DEEP,
    number_of_piles=5,
    vertical_members=GeometryGroupVerticalMembersBelowGround.create(
        application_id="COL-GEOMGROUP-0005-VERTICAL-MEMBERS",
        piles=abutment_0_piles,
    ),
    horizontal_members=GeometryGroupHorizontalMembersBelowGround.create(
        application_id="COL-GEOMGROUP-0003-HORIZONTAL-MEMBERS",
        pile_cap=abutment_0_pile_cap,
    ),
)

abutment_0 = GeometryGroupSupport.create(
    name="Abutment_0",
    application_id="COL-GEOMGROUP-0001-SUPPORT",
    support_index=0,
    skew_angle=15.0,
    bearing_underside_level=119.0,
    orientation=ElementOrientationParaModel.ORTHOGONAL,
    above_ground=abutment_0_above_ground,
    below_ground=abutment_0_below_ground,
)


###############################################################################################
# SUBSTRUCTURE - PIER 1
###############################################################################################

pier_1_1 = GeometryGroupPier.create(
    name="pier_1_1",
    application_id="COL-GEOMGROUP-0001-PIER",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0003-STANDARD-SOLID-RECTANGLE",
    transverse_offset=3.0,
)

pier_1_2 = GeometryGroupPier.create(
    name="Pier_1_2",
    application_id="COL-GEOMGROUP-0002-PIER",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0003-STANDARD-SOLID-RECTANGLE",
    transverse_offset=-3.0,
)

crossbeam_pier_1 = GeometryGroupCrossbeam.create(
    name="Crossbeam_pier_1",
    application_id="COL-GEOMGROUP-0001-CROSSBEAM",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0005-STANDARD-SOLID-RECTANGLE",
    element_length=10.0,
    tapers=[
        (1.5, 4.0, "SECT-0007-TAPERED"),
    ],
)

pier_1_above_ground = GeometryGroupAboveGround.create(
    application_id="COL-GEOMGROUP-0002-ABOVE-GROUND",
    support_type=SupportTypeParaModel.COLUMN_TYPE,
    number_of_piers=2,
    vertical_members=GeometryGroupVerticalMembersAboveGround.create(
        application_id="COL-GEOMGROUP-0002-VERTICAL-MEMBERS",
        piers=[pier_1_1, pier_1_2],
    ),
    horizontal_members=GeometryGroupHorizontalMembersAboveGround.create(
        application_id="COL-GEOMGROUP-0001-HORIZONTAL-MEMBERS",
        crossbeam=crossbeam_pier_1,
    ),
)

pier_1_piles = [
    GeometryGroupPile.create(
        name=name,
        application_id=f"COL-GEOMGROUP-{i + 6:04d}-PILE",
        material_id="MAT-0003-CONC-AASHTO",
        section_id="SECT-0001-STANDARD-SOLID-CIRCLE",
        pile_index=i,
        pile_length=12.0,
        offset_along_support_line=offset_along,
        offset_normal_to_support_line=offset_normal,
        spring_spacing=spring_spacing,
    )
    for i, (name, offset_along, offset_normal, spring_spacing) in enumerate(
        [
            ("Pile_1_1", 0.0, 0.0, [3.0] * 4),
            ("Pile_1_2", 3.5, 1.5, [1.0, 1.0, 1.0, 1.0, 1.0, 2.5, 2.5, 2.0]),
            ("Pile_1_3", 3.5, -1.5, [3.0] * 4),
            ("Pile_1_4", -3.5, 1.5, [3.0] * 4),
            ("Pile_1_5", -3.5, -1.5, [3.0] * 4),
        ]
    )
]

pier_1_pile_cap = GeometryGroupPileCap.create(
    name="Pilecap_pier_1",
    application_id="COL-GEOMGROUP-0002-PILE-CAP",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0004-STANDARD-SOLID-RECTANGLE",
    top_of_pile_cap_level=101.5,
    element_length=10.0,
)

pier_1_below_ground = GeometryGroupBelowGround.create(
    application_id="COL-GEOMGROUP-0002-BELOW-GROUND",
    foundation_type=FoundationTypeParaModel.DEEP,
    number_of_piles=5,
    vertical_members=GeometryGroupVerticalMembersBelowGround.create(
        application_id="COL-GEOMGROUP-0006-VERTICAL-MEMBERS",
        piles=pier_1_piles,
    ),
    horizontal_members=GeometryGroupHorizontalMembersBelowGround.create(
        application_id="COL-GEOMGROUP-0004-HORIZONTAL-MEMBERS",
        pile_cap=pier_1_pile_cap,
    ),
)

pier_1 = GeometryGroupSupport.create(
    name="Pier_1",
    application_id="COL-GEOMGROUP-0002-SUPPORT",
    support_index=1,
    skew_angle=0.0,
    bearing_underside_level=115.0,
    orientation=ElementOrientationParaModel.ORTHOGONAL,
    above_ground=pier_1_above_ground,
    below_ground=pier_1_below_ground,
)


###############################################################################################
# SUBSTRUCTURE - PIER 2
###############################################################################################

pier_2_1 = GeometryGroupPier.create(
    name="Pier_2_1",
    application_id="COL-GEOMGROUP-0003-PIER",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0002-STANDARD-SOLID-CIRCLE",
    transverse_offset=3.0,
)

pier_2_2 = GeometryGroupPier.create(
    name="Pier_2_2",
    application_id="COL-GEOMGROUP-0004-PIER",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0002-STANDARD-SOLID-CIRCLE",
    transverse_offset=-3.0,
)

pier_2_3 = GeometryGroupPier.create(
    name="Pier_2_3",
    application_id="COL-GEOMGROUP-0005-PIER",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0002-STANDARD-SOLID-CIRCLE",
    transverse_offset=0.0,
)

crossbeam_pier_2 = GeometryGroupCrossbeam.create(
    name="Crossbeam_pier_2",
    application_id="COL-GEOMGROUP-0002-CROSSBEAM",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0005-STANDARD-SOLID-RECTANGLE",
    element_length=10.0,
    tapers=[
        (1.5, 5.0, "SECT-0007-TAPERED"),
    ],
)

pier_2_above_ground = GeometryGroupAboveGround.create(
    application_id="COL-GEOMGROUP-0003-ABOVE-GROUND",
    support_type=SupportTypeParaModel.COLUMN_TYPE,
    number_of_piers=3,
    vertical_members=GeometryGroupVerticalMembersAboveGround.create(
        application_id="COL-GEOMGROUP-0003-VERTICAL-MEMBERS",
        piers=[pier_2_1, pier_2_2, pier_2_3],
    ),
    horizontal_members=GeometryGroupHorizontalMembersAboveGround.create(
        application_id="COL-GEOMGROUP-0002-HORIZONTAL-MEMBERS",
        crossbeam=crossbeam_pier_2,
    ),
)

pier_2_piles = [
    GeometryGroupPile.create(
        name=name,
        application_id=f"COL-GEOMGROUP-{i + 11:04d}-PILE",
        material_id="MAT-0003-CONC-AASHTO",
        section_id="SECT-0001-STANDARD-SOLID-CIRCLE",
        pile_index=i,
        pile_length=15.0,
        offset_along_support_line=offset_along,
        offset_normal_to_support_line=offset_normal,
        spring_spacing=spring_spacing,
    )
    for i, (name, offset_along, offset_normal, spring_spacing) in enumerate(
        [
            ("Pile_2_1", 0.0, 0.0, [2.5] * 6),
            # "pile_2_2" is the fixture's own (lowercase) name, mirrored as-is.
            ("pile_2_2", 3.5, 1.5, [3.0] * 5),
            ("Pile_2_3", 3.5, -1.5, [3.0] * 5),
            ("Pile_2_4", -3.5, 1.5, [3.0] * 5),
            ("Pile_2_5", -3.5, -1.5, [3.0] * 5),
        ]
    )
]

pier_2_pile_cap = GeometryGroupPileCap.create(
    name="Pilecap_pier_2",
    application_id="COL-GEOMGROUP-0003-PILE-CAP",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0004-STANDARD-SOLID-RECTANGLE",
    top_of_pile_cap_level=95.5,
    element_length=10.0,
)

pier_2_below_ground = GeometryGroupBelowGround.create(
    application_id="COL-GEOMGROUP-0003-BELOW-GROUND",
    foundation_type=FoundationTypeParaModel.DEEP,
    number_of_piles=5,
    vertical_members=GeometryGroupVerticalMembersBelowGround.create(
        application_id="COL-GEOMGROUP-0007-VERTICAL-MEMBERS",
        piles=pier_2_piles,
    ),
    horizontal_members=GeometryGroupHorizontalMembersBelowGround.create(
        application_id="COL-GEOMGROUP-0005-HORIZONTAL-MEMBERS",
        pile_cap=pier_2_pile_cap,
    ),
)

pier_2 = GeometryGroupSupport.create(
    name="Pier_2",
    application_id="COL-GEOMGROUP-0003-SUPPORT",
    support_index=2,
    skew_angle=30.0,
    bearing_underside_level=114.0,
    orientation=ElementOrientationParaModel.ORTHOGONAL,
    above_ground=pier_2_above_ground,
    below_ground=pier_2_below_ground,
)


###############################################################################################
# SUBSTRUCTURE - PIER 3
###############################################################################################
# Note: the fixture states "no_of_piers": 2 for Pier_3's above-ground details but only lists
# one pier (pier_3_1). This is mirrored as-is from the fixture.

pier_3_1 = GeometryGroupPier.create(
    name="Pier_3_1",
    application_id="COL-GEOMGROUP-0006-PIER",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0002-STANDARD-SOLID-CIRCLE",
    transverse_offset=0.0,
)

pier_3_above_ground = GeometryGroupAboveGround.create(
    application_id="COL-GEOMGROUP-0004-ABOVE-GROUND",
    support_type=SupportTypeParaModel.COLUMN_TYPE,
    number_of_piers=2,
    vertical_members=GeometryGroupVerticalMembersAboveGround.create(
        application_id="COL-GEOMGROUP-0004-VERTICAL-MEMBERS",
        piers=[pier_3_1],
    ),
)

pier_3_pile_cap = GeometryGroupPileCap.create(
    name="Pilecap_pier_3",
    application_id="COL-GEOMGROUP-0004-PILE-CAP",
    material_id="MAT-0002-CONC-AASHTO",
    section_id="SECT-0004-STANDARD-SOLID-RECTANGLE",
    top_of_pile_cap_level=95.5,
    element_length=10.0,
)

pier_3_below_ground = GeometryGroupBelowGround.create(
    application_id="COL-GEOMGROUP-0004-BELOW-GROUND",
    foundation_type=FoundationTypeParaModel.DEEP,
    number_of_piles=5,
    vertical_members=GeometryGroupVerticalMembersBelowGround.create(
        application_id="COL-GEOMGROUP-0008-VERTICAL-MEMBERS",
        piles=[
            GeometryGroupPile.create(
                name=name,
                application_id=f"COL-GEOMGROUP-{i + 16:04d}-PILE",
                material_id="MAT-0003-CONC-AASHTO",
                section_id="SECT-0001-STANDARD-SOLID-CIRCLE",
                pile_index=i,
                pile_length=15.0,
                offset_along_support_line=offset_along,
                offset_normal_to_support_line=offset_normal,
                spring_spacing=spring_spacing,
            )
            for i, (name, offset_along, offset_normal, spring_spacing) in enumerate(
                [
                    ("Pile_3_1", 0.0, 0.0, [2.5] * 6),
                    ("Pile_3_2", 3.5, 1.5, [3.0] * 5),
                    ("Pile_3_3", 3.5, -1.5, [3.0] * 5),
                    ("Pile_3_4", -3.5, 1.5, [3.0] * 5),
                    ("Pile_3_5", -3.5, -1.5, [3.0] * 5),
                ]
            )
        ],
    ),
    horizontal_members=GeometryGroupHorizontalMembersBelowGround.create(
        application_id="COL-GEOMGROUP-0006-HORIZONTAL-MEMBERS",
        pile_cap=pier_3_pile_cap,
    ),
)

pier_3 = GeometryGroupSupport.create(
    name="Pier_3",
    application_id="COL-GEOMGROUP-0004-SUPPORT",
    support_index=3,
    skew_angle=30.0,
    bearing_underside_level=114.0,
    orientation=ElementOrientationParaModel.ORTHOGONAL,
    above_ground=pier_3_above_ground,
    below_ground=pier_3_below_ground,
)


substructure = GeometryGroupSubstructure.create(
    application_id="COL-GEOMGROUP-0001-SUBSTRUCTURE",
    supports=[abutment_0, pier_1, pier_2, pier_3],
)


###############################################################################################
# LINKAGE
###############################################################################################

linkage = GeometryGroupLinkage.create(
    application_id="COL-GEOMGROUP-0001-LINKAGE",
    connections=[
        GeometryGroupSuperstructureToSubstructureConnections.create(
            application_id="COL-GEOMGROUP-0001-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS",
            support_index=0,
            bearing_configuration_type=BearingConfigurationTypeParaModel.MULTIPLE,
            number_of_bearings=2,
            spacing_type=SpacingTypeParaModel.UNIFORM,
            bearing_spacing=[5.0],
        ),
        GeometryGroupSuperstructureToSubstructureConnections.create(
            application_id="COL-GEOMGROUP-0002-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS",
            support_index=1,
            bearing_configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
        ),
        GeometryGroupSuperstructureToSubstructureConnections.create(
            application_id="COL-GEOMGROUP-0003-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS",
            support_index=2,
            bearing_configuration_type=BearingConfigurationTypeParaModel.MULTIPLE,
            number_of_bearings=3,
            spacing_type=SpacingTypeParaModel.UNIFORM,
            bearing_spacing=[2.0, 2.0],
        ),
        GeometryGroupSuperstructureToSubstructureConnections.create(
            application_id="COL-GEOMGROUP-0004-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS",
            support_index=3,
            bearing_configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
        ),
    ],
)


###############################################################################################
# BRIDGE
###############################################################################################

psc_bridge = GeometryGroupBridge.create(
    application_id="COL-GEOMGROUP-0001-BRIDGE",
    bridge_type=BridgeTypeParaModel.PSC_BOX,
    bridge_idealisation=BridgeIdealisationParaModel.LINE_BEAM,
    number_of_spans=3,
    girder_mesh_divisor=20,
    top_deck_level=123.0,
    top_deck_level_unit="m",
    superstructure=superstructure,
    substructure=substructure,
    linkage=linkage,
)


###############################################################################################
# BOUNDARY CONDITIONS - BEARINGS
###############################################################################################
# fixture bearing_bc.json, one BearingBCDataObject per support (girder_index 0 throughout).

# Support 0: multiple (2), skewed, user-defined stiffness on all 6 DOFs for both bearings.
support_0_bearing_0 = BearingBCDataObject.create_user_defined(
    name="Sup_to_sub_0 bearing 0",
    application_id="BC-BEARING-9001",
    support_index=0,
    girder_index=0,
    bearing_index=0,
    configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
    orientation=ElementOrientationParaModel.SKEWED,
    sdx_value=2_500_000,
    sdy_value=3_000_000,
    sdz_value=10_000_000,
    srx_value=50_000,
    sry_value=50_000,
    srz_value=10_000,
).properties.bearing_boundary_condition_parameters.group_parameters.spring_definitions.group_parameters[
    "bearing-0000"
]

support_0_bearing_1 = BearingBCDataObject.create_user_defined(
    name="Sup_to_sub_0 bearing 1",
    application_id="BC-BEARING-9002",
    support_index=0,
    girder_index=0,
    bearing_index=1,
    configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
    orientation=ElementOrientationParaModel.SKEWED,
    sdx_value=2_500_000,
    sdy_value=3_000_000,
    sdz_value=10_000_000,
    srx_value=50_000,
    sry_value=50_000,
    srz_value=10_000,
).properties.bearing_boundary_condition_parameters.group_parameters.spring_definitions.group_parameters[
    "bearing-0001"
]

bearing_bc_support_0 = BearingBCDataObject.create(
    name="Sup_to_sub_0",
    application_id="BC-BEARING-0001",
    support_index=0,
    girder_index=0,
    bearing_index=0,
    configuration_type=BearingConfigurationTypeParaModel.MULTIPLE,
    orientation=ElementOrientationParaModel.SKEWED,
    spring_definitions={
        "bearing-0000": support_0_bearing_0,
        "bearing-0001": support_0_bearing_1,
    },
)

# Support 1: singular, orthogonal, free in X/RX/RY/RZ, fixed in Y/Z.
bearing_bc_support_1 = BearingBCDataObject.create(
    name="Sup_to_sub_1",
    application_id="BC-BEARING-0002",
    support_index=1,
    girder_index=0,
    bearing_index=0,
    configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
    orientation=ElementOrientationParaModel.ORTHOGONAL,
    spring_definitions=BoundaryConditionSpringParameterGroup.create(
        sdx_dof_type=DofTypeEnumParaModel.FREE,
        sdy_dof_type=DofTypeEnumParaModel.FIXED,
        sdz_dof_type=DofTypeEnumParaModel.FIXED,
        srx_dof_type=DofTypeEnumParaModel.FREE,
        sry_dof_type=DofTypeEnumParaModel.FREE,
        srz_dof_type=DofTypeEnumParaModel.FREE,
    ),
)

# Support 2: multiple (3), skewed, same free/fixed pattern as support 1 on each bearing.
_support_2_dof_pattern = dict(
    sdx_dof_type=DofTypeEnumParaModel.FREE,
    sdy_dof_type=DofTypeEnumParaModel.FIXED,
    sdz_dof_type=DofTypeEnumParaModel.FIXED,
    srx_dof_type=DofTypeEnumParaModel.FREE,
    sry_dof_type=DofTypeEnumParaModel.FREE,
    srz_dof_type=DofTypeEnumParaModel.FREE,
)

support_2_bearings = {
    f"bearing-{bearing_index:04d}": BearingBCDataObject.create(
        name=f"Sup_to_sub_2 bearing {bearing_index}",
        application_id=f"BC-BEARING-{9003 + bearing_index:04d}",
        support_index=2,
        girder_index=0,
        bearing_index=bearing_index,
        configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
        orientation=ElementOrientationParaModel.SKEWED,
        spring_definitions=BoundaryConditionSpringParameterGroup.create(**_support_2_dof_pattern),
    ).properties.bearing_boundary_condition_parameters.group_parameters.spring_definitions.group_parameters[
        f"bearing-{bearing_index:04d}"
    ]
    for bearing_index in range(3)
}

bearing_bc_support_2 = BearingBCDataObject.create(
    name="Sup_to_sub_2",
    application_id="BC-BEARING-0003",
    support_index=2,
    girder_index=0,
    bearing_index=0,
    configuration_type=BearingConfigurationTypeParaModel.MULTIPLE,
    orientation=ElementOrientationParaModel.SKEWED,
    spring_definitions=support_2_bearings,
)

# Support 3: singular, orthogonal, fixed in X/Y/Z, free in RX/RY/RZ.
bearing_bc_support_3 = BearingBCDataObject.create(
    name="Sup_to_sub_3",
    application_id="BC-BEARING-0004",
    support_index=3,
    girder_index=0,
    bearing_index=0,
    configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
    orientation=ElementOrientationParaModel.ORTHOGONAL,
    spring_definitions=BoundaryConditionSpringParameterGroup.create(
        sdx_dof_type=DofTypeEnumParaModel.FIXED,
        sdy_dof_type=DofTypeEnumParaModel.FIXED,
        sdz_dof_type=DofTypeEnumParaModel.FIXED,
        srx_dof_type=DofTypeEnumParaModel.FREE,
        sry_dof_type=DofTypeEnumParaModel.FREE,
        srz_dof_type=DofTypeEnumParaModel.FREE,
    ),
)

boundary_conditions = BoundaryConditionsCollection.create(
    application_id="COL-BOUNDARY-CONDITIONS",
    bearing_conditions=BearingBCCollection.create(
        application_id="COL-BEARING-BC",
        bearing_conditions=[
            bearing_bc_support_0,
            bearing_bc_support_1,
            bearing_bc_support_2,
            bearing_bc_support_3,
        ],
    ),
)


###############################################################################################
# MODEL CONFIG + ROOT
###############################################################################################

model_config = BDA_ModelDataDataObject.create(
    model_unit_system=ModelUnitSystemEnum.METRIC,
    output_software=OutputSoftwareEnum.MIDAS_CIVIL,
    design_code=DesignCodesEnum.AASHTO,
    structure_type=StructureTypeEnum.PSC_BOX,
)

model = ModelRootCollection.create(
    model_config=model_config,
    materials=materials_collection,
    sections=section_collection,
    geometry=psc_bridge,
    boundary_conditions=boundary_conditions,
)

if __name__ == "__main__":
    print(
        model.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    from bda.infrastructure.data_providers.speckle_helpers.speckle_send_object import (
        ingest_ui_json_and_commit,
    )
    
    ingest_ui_json_and_commit(
        json_data=model.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_defaults=False,
            mode="json",
        ),
        pydantic_model=ModelRootCollection,
        speckle_url="https://design.jacobs.com/projects/8f0d636aa6/models/4799a9bc6e",
        commit_message=(
            f"MVP PSC Box Example Model - {datetime.datetime.now():%Y-%m-%d %H:%M}"
        ),
    )
