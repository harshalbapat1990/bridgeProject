import datetime

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_bridge import (
    GeometryGroupBridge
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_superstructure import (
    GeometryGroupSuperstructure
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_span import (
    GeometryGroupSpan,
    CrackedExtentsParameterGroup,
    TaperedDetailsParameterGroup,
    ConstructionSequenceDetailsParameterGroup,
    SplicesParameterGroup
    )

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_longitudinal_members import (
    GeometryGroupLongitudinalMembers
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_girder import (
    GeometryGroupGirder
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_transverse_members import (
    GeometryGroupTransverseMembers
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_diaphragm import (
    GeometryGroupDiaphragm
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_deck_slab import (
    GeometryGroupDeckSlab
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_transverse_bracing import (
    GeometryGroupTransverseBracing
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_brace import (
    GeometryGroupBrace
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_chord import (
    GeometryGroupChord
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_plan_bracing import (
    GeometryGroupPlanBracing
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_substructure import (
    GeometryGroupSubstructure
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_support import (
    GeometryGroupSupport
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_above_ground import (
    GeometryGroupAboveGround
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_vertical_members import (
    GeometryGroupVerticalMembersAboveGround
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_horizontal_members import (
    GeometryGroupHorizontalMembersAboveGround
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_linkage import (
    GeometryGroupLinkage
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_superstructure_to_substructure_connections import (
    GeometryGroupSuperstructureToSubstructureConnections
)


from bda.contracts.paramodel.groups.enums import (
    SpacingTypeParaModel,
    StructuralComponentTypeParaModel,
    BridgeTypeParaModel,
    BridgeIdealisationParaModel,
    ElementOrientationParaModel,
    DiaphragmTypeParaModel,
    BracingTypeParaModel,
    PlanBracingTypeParaModel,
    SupportTypeParaModel,
    BearingConfigurationTypeParaModel
)

from bda.contracts.speckle_contracts.bda_analytical.model_root import ModelRootCollection
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_DataObject import (
    BDA_ModelDataDataObject,
    ModelUnitSystemEnum,
    OutputSoftwareEnum,
    DesignCodesEnum,
    StructureTypeEnum
)

from bda.contracts.speckle_contracts.bda_analytical.materials.materials_collection import (
    MaterialsCollection
)

from bda.contracts.speckle_contracts.bda_analytical.materials.concrete.concrete_material_aashto import (
    ConcreteAASHTOMaterialDataObject
)

from bda.contracts.speckle_contracts.bda_analytical.materials.steel.steel_material_aashto import (
    SteelAASHTOMaterialDataObject
)

from bda.contracts.speckle_contracts.bda_analytical.materials.reinforcement.reinforcement_material_aashto import (
    ReinforcementAASHTOMaterialDataObject
)

from bda.contracts.speckle_contracts.bda_analytical.materials.tendon.tendon_material_aashto import (
    TendonAASHTOMaterialDataObject
)

from bda.contracts.speckle_contracts.bda_analytical.sections.section_collection import (
    SectionsCollection,
    SectionDataObject_Angle,
    SectionDataObject_Box,
    SectionDataObject_Channel,
    SectionDataObject_CompositeIAsymmetric,
    SectionDataObject_CompositeISymmetric,
    SectionDataObject_ISection,
    SectionDataObject_Pipe,
    SectionDataObject_PSCValue,
    SectionDataObject_SolidCircle,
    SectionDataObject_SolidRectangle,
    SectionDataObject_Tapered
)
from bda.contracts.speckle_contracts.bda_analytical.sections.taper_section_group import TaperVariationParaModel, SectionTypeParaModel, TaperYVariationParameter, TaperZVariationParameter

from bda.infrastructure.data_providers.speckle_helpers.speckle_send_object import ingest_ui_json_and_commit

###############################################################################################
# LINKAGE
###############################################################################################

linkage = GeometryGroupLinkage.create(
    application_id="COL-GEOMGROUP-0001-LINKAGE",
    connections=[
        GeometryGroupSuperstructureToSubstructureConnections.create(
            application_id="COL-GEOMGROUP-0001-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS",
            support_index=0,
            bearing_configuration_type=BearingConfigurationTypeParaModel.SINGULAR
        ),
        GeometryGroupSuperstructureToSubstructureConnections.create(
            application_id="COL-GEOMGROUP-0002-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS",
            support_index=1,
            bearing_configuration_type=BearingConfigurationTypeParaModel.SINGULAR
        ),
        GeometryGroupSuperstructureToSubstructureConnections.create(
            application_id="COL-GEOMGROUP-0003-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS",
            support_index=2,
            bearing_configuration_type=BearingConfigurationTypeParaModel.SINGULAR
        ),
        GeometryGroupSuperstructureToSubstructureConnections.create(
            application_id="COL-GEOMGROUP-0004-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS",
            support_index=3,
            bearing_configuration_type=BearingConfigurationTypeParaModel.SINGULAR
        )
    ]
)

###############################################################################################
# SUBSTRUCTURE
###############################################################################################

support_4_substructure = GeometryGroupSupport.create(
    name = "Support No.4",
    application_id = "COL-GEOMGROUP-0004-SUPPORT",
    support_index = 3,
    skew_angle=45.0,
    bearing_underside_level=60.0,
    orientation = ElementOrientationParaModel.SKEWED,
    # above_ground=GeometryGroupAboveGround.create(
    #     application_id="COL-GEOMGROUP-0004-ABOVE-GROUND",
    #     support_type=SupportTypeParaModel.COLUMN_TYPE,
    #     number_of_piers=1,
    #     vertical_members=GeometryGroupVerticalMembersAboveGround.create(application_id="COL-GEOMGROUP-0004-VERTICAL-MEMBERS"),
    #     horizontal_members=GeometryGroupHorizontalMembersAboveGround.create(application_id="COL-GEOMGROUP-0004-HORIZONTAL-MEMBERS")
    # )
)

support_3_substructure = GeometryGroupSupport.create(
    name = "Support No.3",
    application_id = "COL-GEOMGROUP-0003-SUPPORT",
    support_index = 2,
    skew_angle=45.0,
    bearing_underside_level=60.0,
    orientation = ElementOrientationParaModel.SKEWED,
    # above_ground=GeometryGroupAboveGround.create(
    #     application_id="COL-GEOMGROUP-0003-ABOVE-GROUND",
    #     support_type=SupportTypeParaModel.COLUMN_TYPE,
    #     number_of_piers=1,
    #     vertical_members=GeometryGroupVerticalMembersAboveGround.create(application_id="COL-GEOMGROUP-0003-VERTICAL-MEMBERS"),
    #     horizontal_members=GeometryGroupHorizontalMembersAboveGround.create(application_id="COL-GEOMGROUP-0003-HORIZONTAL-MEMBERS")
    # )
)

support_2_substructure = GeometryGroupSupport.create(
    name = "Support No.2",
    application_id = "COL-GEOMGROUP-0002-SUPPORT",
    support_index = 1,
    skew_angle=45.0,
    bearing_underside_level=60.0,
    orientation = ElementOrientationParaModel.SKEWED,
    # above_ground=GeometryGroupAboveGround.create(
    #     application_id="COL-GEOMGROUP-0002-ABOVE-GROUND",
    #     support_type=SupportTypeParaModel.COLUMN_TYPE,
    #     number_of_piers=1,
    #     vertical_members=GeometryGroupVerticalMembersAboveGround.create(application_id="COL-GEOMGROUP-0002-VERTICAL-MEMBERS"),
    #     horizontal_members=GeometryGroupHorizontalMembersAboveGround.create(application_id="COL-GEOMGROUP-0002-HORIZONTAL-MEMBERS")
    # )
)

support_1_substructure = GeometryGroupSupport.create(
    name = "Support No.1",
    application_id = "COL-GEOMGROUP-0001-SUPPORT",
    support_index = 0,
    skew_angle=45.0,
    bearing_underside_level=60.0,
    orientation = ElementOrientationParaModel.SKEWED,
    # above_ground=GeometryGroupAboveGround.create(
    #     application_id="COL-GEOMGROUP-0001-ABOVE-GROUND",
    #     support_type=SupportTypeParaModel.COLUMN_TYPE,
    #     number_of_piers=1,
    #     vertical_members=GeometryGroupVerticalMembersAboveGround.create(application_id="COL-GEOMGROUP-0001-VERTICAL-MEMBERS"),
    #     horizontal_members=GeometryGroupHorizontalMembersAboveGround.create(application_id="COL-GEOMGROUP-0001-HORIZONTAL-MEMBERS")
    # )
)

substructure = GeometryGroupSubstructure.create(
    application_id="COL-GEOMGROUP-0001-SUBSTRUCTURE",
    supports=[
        support_1_substructure,
        support_2_substructure,
        support_3_substructure,
        support_4_substructure
    ]
)


###############################################################################################
# SPAN 3
###############################################################################################

# SPAN 1 PLAN BRACING

span_3_plan_bracing = GeometryGroupPlanBracing.create(
    name = "Plan Bracing at Span",
    application_id="COL-GEOMGROUP-0003-PLAN-BRACING",
    material_id="MAT-0002-STEEL-AASHTO",
    section_id="SECT-0013-STANDARD-SOLID-CIRCLE",
    plan_bracing_type=PlanBracingTypeParaModel.PRATT,
    left_girder_index=1,
    right_girder_index=2
)

# SPAN 1 TRANSVERSE BRACING 1

transverse_bracing_1_span_3 = GeometryGroupTransverseBracing.create(
    name = "Transverse Bracing at Span",
    application_id="COL-GEOMGROUP-0007-TRANSVERSE-BRACING",
    bracing_orientation=ElementOrientationParaModel.ORTHOGONAL,
    number_of_bracings=5,
    x_start_first_bracing=5,
    left_girder_index=1,
    right_girder_index=2,
    spacing_type=SpacingTypeParaModel.UNIFORM,
    spacing_values=[4, 4, 4, 4],
    horizontal_offset_left_girder=0.25,
    horizontal_offset_right_girder=0.25,
    braces=[
        GeometryGroupBrace.create(
            application_id=f"COL-GEOMGROUP-{x+25:04d}-BRACE",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0009-STANDARD-ANGLE",
            brace_type=BracingTypeParaModel.K_TYPE,
            vertical_offset_left_top=0.25,
            vertical_offset_left_bottom=0.95,
            vertical_offset_right_top=0.25,
            vertical_offset_right_bottom=0.95,
            horizontal_offset_left=1.1,
            horizontal_offset_right=1.1,
        )
        for x in range(5)
    ],
    chords=[
        GeometryGroupChord.create(
            application_id=f"COL-GEOMGROUP-{49+2*x+chord_index:04d}-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=vertical_offset,
            vertical_offset_right=vertical_offset,
        )
        for x in range(5)
        for chord_index, vertical_offset in [
            (0, 0.25),
            (1, 1.25),
        ]
    ],
)


# SPAN 1 DIAPHRAGM 2

diaphragm_1_span_3 = GeometryGroupDiaphragm.create(
    name = "Diaphragm No.3",
    application_id="COL-GEOMGROUP-0004-DIAPHRAGM",
    material_id="MAT-0002-STEEL-AASHTO",
    section_id = "SECT-0011-STANDARD-ISECTION",
    support_index=3,
    diaphragm_type=DiaphragmTypeParaModel.STEEL_GIRDER,
    transverse_bracing=None

)


# SPAN 1 - TRANSVERSE

transverse_span_3 = GeometryGroupTransverseMembers.create(
    application_id="COL-GEOMGROUP-0003-TRANSVERSE-MEMBERS",
    deck_slab=GeometryGroupDeckSlab.create(
        application_id="COL-GEOMGROUP-0003-DECK-SLAB",
        material_id="MAT-0001-CONC-AASHTO",
        section_id="SECT-0008-STANDARD-SOLID-RECTANGLE"),
    diaphragms = [
        diaphragm_1_span_3
        ],
    transverse_bracings=[
        transverse_bracing_1_span_3
    ],
    plan_bracing=span_3_plan_bracing
)


# SPAN 1 - LONGITUDINAL

longitudinal_span_3 = GeometryGroupLongitudinalMembers.create(
    application_id="COL-GEOMGROUP-0003-LONGITUDINAL-MEMBERS",
    girders=[
        GeometryGroupGirder.create(
            name="Girder No.1",
            application_id="COL-GEOMGROUP-0011-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0006-COMPOSITE-I-ASYMMETRIC",
            girder_index=0
            ),
        GeometryGroupGirder.create(
            name="Girder No.2",
            application_id="COL-GEOMGROUP-0012-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0001-COMPOSITE-I-SYMMETRIC",
            girder_index=1
            ),
        GeometryGroupGirder.create(
            name="Girder No.3",
            application_id="COL-GEOMGROUP-0013-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0001-COMPOSITE-I-SYMMETRIC",
            girder_index=2
            ),
        GeometryGroupGirder.create(
            name="Girder No.4",
            application_id="COL-GEOMGROUP-0014-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0007-COMPOSITE-I-ASYMMETRIC",
            girder_index=3
            ),
        GeometryGroupGirder.create(
            name="Girder No.5",
            application_id="COL-GEOMGROUP-0015-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0007-COMPOSITE-I-ASYMMETRIC",
            girder_index=4
            ),


    ]
)

#SPAN 3

span_3 = GeometryGroupSpan.create(
    application_id="COL-GEOMGROUP-0003-SPAN",
    name="Span No.3",
    span_index=2,
    top_deck_level_at_end=63.0,
    span_length=30.0,
    cracked_extents= CrackedExtentsParameterGroup.create(
        extents=[(0,10)]
    ),
    construction_sequence_details= ConstructionSequenceDetailsParameterGroup.create(
        segments=[(0,10),(10,20),(20,30)],
        pouring_orientation=ElementOrientationParaModel.SKEWED
    ),
    splices=SplicesParameterGroup.create(
        splices=[
            (15.0,"SECT-0003-COMPOSITE-I-SYMMETRIC")
        ]
    ),
    longitudinal_members=longitudinal_span_3,
    transverse_members=transverse_span_3
)




###############################################################################################
# SPAN 2
###############################################################################################

# SPAN 2 PLAN BRACING

plan_bracing_span_2 = GeometryGroupPlanBracing.create(
    name = "Plan Bracing at Span",
    application_id="COL-GEOMGROUP-0002-PLAN-BRACING",
    material_id="MAT-0002-STEEL-AASHTO",
    section_id="SECT-0013-STANDARD-SOLID-CIRCLE",
    plan_bracing_type=PlanBracingTypeParaModel.X_TYPE,
    left_girder_index=1,
    right_girder_index=2
)

# SPAN 2 TRANSVERSE BRACING 1

transverse_bracing_1_span_2 = GeometryGroupTransverseBracing.create(
    name= "Transverse Bracing at Span",
    application_id="COL-GEOMGROUP-0006-TRANSVERSE-BRACING",
    bracing_orientation=ElementOrientationParaModel.ORTHOGONAL,
    number_of_bracings=9,
    x_start_first_bracing=5,
    left_girder_index=1,
    right_girder_index=2,
    spacing_type=SpacingTypeParaModel.UNIFORM,
    spacing_values=[4, 4, 4, 4, 4, 4, 4, 4],
    horizontal_offset_left_girder=0.25,
    horizontal_offset_right_girder=0.25,
    braces=[
        GeometryGroupBrace.create(
            application_id=f"COL-GEOMGROUP-{x+16:04d}-BRACE",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0009-STANDARD-ANGLE",
            brace_type=BracingTypeParaModel.K_TYPE,
            vertical_offset_left_top=0.25,
            vertical_offset_left_bottom=0.95,
            vertical_offset_right_top=0.25,
            vertical_offset_right_bottom=0.95,
            horizontal_offset_left=1.1,
            horizontal_offset_right=1.1,
        )
        for x in range(9)
    ],
    chords=[
        GeometryGroupChord.create(
            application_id=f"COL-GEOMGROUP-{31+2*x+chord_index:04d}-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=vertical_offset,
            vertical_offset_right=vertical_offset,
        )
        for x in range(9)
        for chord_index, vertical_offset in [
            (0, 0.25),
            (1, 1.25),
        ]
    ],
)


# SPAN 2 DIAPHRAGM 1

diaphragm_1_span_2 = GeometryGroupDiaphragm.create(
    name = "Diaphragm No.1",
    application_id="COL-GEOMGROUP-0003-DIAPHRAGM",
    material_id="MAT-0002-STEEL-AASHTO",
    section_id = "SECT-0011-STANDARD-ISECTION",
    support_index=2,
    diaphragm_type=DiaphragmTypeParaModel.STEEL_GIRDER,
    transverse_bracing=None
)

# SPAN 2 - TRANSVERSE

transverse_span_2 = GeometryGroupTransverseMembers.create(
    application_id="COL-GEOMGROUP-0002-TRANSVERSE-MEMBERS",
    deck_slab=GeometryGroupDeckSlab.create(
        application_id="COL-GEOMGROUP-0002-DECK-SLAB",
        material_id="MAT-0001-CONC-AASHTO",
        section_id="SECT-0008-STANDARD-SOLID-RECTANGLE"),
    diaphragms = [
        diaphragm_1_span_2
        ],
    transverse_bracings=[
        transverse_bracing_1_span_2
    ],
    plan_bracing=plan_bracing_span_2
)


# SPAN 2 - LONGITUDINAL

longitudinal_span_2 = GeometryGroupLongitudinalMembers.create(
    application_id="COL-GEOMGROUP-0002-LONGITUDINAL-MEMBERS",
    girders=[
        GeometryGroupGirder.create(
            name="Girder No.1",
            application_id="COL-GEOMGROUP-0006-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0006-COMPOSITE-I-ASYMMETRIC",
            girder_index=0
            ),
        GeometryGroupGirder.create(
            name="Girder No.2",
            application_id="COL-GEOMGROUP-0007-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0001-COMPOSITE-I-SYMMETRIC",
            girder_index=1
            ),
        GeometryGroupGirder.create(
            name="Girder No.3",
            application_id="COL-GEOMGROUP-0008-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0001-COMPOSITE-I-SYMMETRIC",
            girder_index=2
            ),
        GeometryGroupGirder.create(
            name="Girder No.4",
            application_id="COL-GEOMGROUP-0009-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0007-COMPOSITE-I-ASYMMETRIC",
            girder_index=3
            ),
        GeometryGroupGirder.create(
            name="Girder No.5",
            application_id="COL-GEOMGROUP-0010-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0007-COMPOSITE-I-ASYMMETRIC",
            girder_index=4
            ),


    ]
)

#SPAN 2

span_2 = GeometryGroupSpan.create(
    application_id="COL-GEOMGROUP-0002-SPAN",
    name="Span No.2",
    span_index=1,
    top_deck_level_at_end=64.0,
    span_length=60.0,
    cracked_extents= CrackedExtentsParameterGroup.create(
        extents=[(0,10),(50,60)]
    ),
    construction_sequence_details= ConstructionSequenceDetailsParameterGroup.create(
        segments=[(0,10),(10,20),(20,40),(40,50),(50,60)],
        pouring_orientation=ElementOrientationParaModel.SKEWED
    ),
    splices=SplicesParameterGroup.create(
        splices=[
            (15.0,"SECT-0003-COMPOSITE-I-SYMMETRIC"),
            (45.0,"SECT-0004-COMPOSITE-I-SYMMETRIC"),
        ]
    ),
    longitudinal_members=longitudinal_span_2,
    transverse_members=transverse_span_2
)



###############################################################################################
# SPAN 1
###############################################################################################

# SPAN 1 PLAN BRACING

span_1_plan_bracing = GeometryGroupPlanBracing.create(
    name = "Plan Bracing at Span",
    application_id="COL-GEOMGROUP-0001-PLAN-BRACING",
    material_id="MAT-0002-STEEL-AASHTO",
    section_id="SECT-0013-STANDARD-SOLID-CIRCLE",
    plan_bracing_type=PlanBracingTypeParaModel.WARREN,
    left_girder_index=1,
    right_girder_index=2
)

# SPAN 1 TRANSVERSE BRACING 2

transverse_bracing_1_span_1 = GeometryGroupTransverseBracing.create(
    name = "Transverse Bracing at Span No.2",
    application_id="COL-GEOMGROUP-0006-TRANSVERSE-BRACING",
    bracing_orientation=ElementOrientationParaModel.SKEWED,
    number_of_bracings=6,
    x_start_first_bracing=5,
    left_girder_index=0,
    right_girder_index=1,
    spacing_type=SpacingTypeParaModel.UNIFORM,
    spacing_values=[4, 4, 4, 4, 4],
    horizontal_offset_left_girder=0.25,
    horizontal_offset_right_girder=0.25,
    braces=[
        GeometryGroupBrace.create(
            application_id=f"COL-GEOMGROUP-{x+11:04d}-BRACE",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0009-STANDARD-ANGLE",
            brace_type=BracingTypeParaModel.X_TYPE,
            vertical_offset_left_top=0.25,
            vertical_offset_left_bottom=0.95,
            vertical_offset_right_top=0.25,
            vertical_offset_right_bottom=0.95
        )
        for x in range(6)
    ],
    chords=[
        GeometryGroupChord.create(
            application_id=f"COL-GEOMGROUP-{19+2*x+chord_index:04d}-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=vertical_offset,
            vertical_offset_right=vertical_offset,
        )
        for x in range(6)
        for chord_index, vertical_offset in [
            (0, 0.25),
            (1, 1.25),
        ]
    ],
)


# SPAN 1 TRANSVERSE BRACING 1

transverse_bracing_1_span_1 = GeometryGroupTransverseBracing.create(
    name = "Transverse Bracing at Span No.1",
    application_id="COL-GEOMGROUP-0005-TRANSVERSE-BRACING",
    bracing_orientation=ElementOrientationParaModel.ORTHOGONAL,
    number_of_bracings=6,
    x_start_first_bracing=5,
    left_girder_index=1,
    right_girder_index=2,
    spacing_type=SpacingTypeParaModel.UNIFORM,
    spacing_values=[4, 4, 4, 4, 4],
    horizontal_offset_left_girder=0.25,
    horizontal_offset_right_girder=0.25,
    braces=[
        GeometryGroupBrace.create(
            application_id=f"COL-GEOMGROUP-{x+5:04d}-BRACE",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0009-STANDARD-ANGLE",
            brace_type=BracingTypeParaModel.K_TYPE,
            vertical_offset_left_top=0.25,
            vertical_offset_left_bottom=0.95,
            vertical_offset_right_top=0.25,
            vertical_offset_right_bottom=0.95,
            horizontal_offset_left=1.1,
            horizontal_offset_right=1.1,
        )
        for x in range(6)
    ],
    chords=[
        GeometryGroupChord.create(
            application_id=f"COL-GEOMGROUP-{9+(2*x)+chord_index:04d}-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=vertical_offset,
            vertical_offset_right=vertical_offset,
        )
        for x in range(6)
        for chord_index, vertical_offset in [
            (0, 0.25),
            (1, 1.25),
        ]
    ],
)


# SPAN 1 DIAPHRAGM 2

diaphragm_2_span_1 = GeometryGroupDiaphragm.create(
    name= "Diaphragm No.2",
    application_id= "COL-GEOMGROUP-0002-DIAPHRAGM",
    material_id= "MAT-0002-STEEL-AASHTO",
    section_id = "SECT-0011-STANDARD-ISECTION",
    support_index=1,
    diaphragm_type=DiaphragmTypeParaModel.STEEL_GIRDER,
    transverse_bracing=None

)


# SPAN 1 - DIAPHRAGM 1 - Bracing

bracing_4_diaphragm_1_span_1 = GeometryGroupTransverseBracing.create(
    name = "Transverse Bracing as Diaphragm No.4",
    application_id="COL-GEOMGROUP-0004-TRANSVERSE-BRACING",
    bracing_orientation=ElementOrientationParaModel.SKEWED,
    x_start_first_bracing=0,
    number_of_bracings=1,
    left_girder_index=3,
    right_girder_index=4,
    horizontal_offset_left_girder=0.2,
    horizontal_offset_right_girder=0.2,
    spacing_type=SpacingTypeParaModel.UNIFORM,
    spacing_values=[10.0],
    braces=[
        GeometryGroupBrace.create(
            application_id="COL-GEOMGROUP-0004-BRACE",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0009-STANDARD-ANGLE",
            brace_type = BracingTypeParaModel.K_TYPE,
            vertical_offset_left_top=0.25,
            vertical_offset_left_bottom=0.95,
            vertical_offset_right_top=0.25,
            vertical_offset_right_bottom=0.95,
            horizontal_offset_left=1.5,
            horizontal_offset_right=1.5
        )
    ],
    chords=[
        GeometryGroupChord.create(
            application_id="COL-GEOMGROUP-0007-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=0.25,
            vertical_offset_right=0.25
        ),
        GeometryGroupChord.create(
            application_id="COL-GEOMGROUP-0008-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=1.25,
            vertical_offset_right=1.25
        )
    ]
)

bracing_3_diaphragm_1_span_1 = GeometryGroupTransverseBracing.create(
    name = "Transverse Bracing as Diaphragm No.3",
    application_id="COL-GEOMGROUP-0003-TRANSVERSE-BRACING",
    bracing_orientation=ElementOrientationParaModel.SKEWED,
    x_start_first_bracing=0,
    number_of_bracings=1,
    left_girder_index=2,
    right_girder_index=3,
    horizontal_offset_left_girder=0.2,
    horizontal_offset_right_girder=0.2,
    spacing_type=SpacingTypeParaModel.UNIFORM,
    spacing_values=[10.0],
    braces=[
        GeometryGroupBrace.create(
            application_id="COL-GEOMGROUP-0003-BRACE",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0009-STANDARD-ANGLE",
            brace_type = BracingTypeParaModel.K_TYPE,
            vertical_offset_left_top=0.25,
            vertical_offset_left_bottom=0.95,
            vertical_offset_right_top=0.25,
            vertical_offset_right_bottom=0.95,
            horizontal_offset_left=1.5,
            horizontal_offset_right=1.5
        )
    ],
    chords=[
        GeometryGroupChord.create(
            application_id="COL-GEOMGROUP-0005-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=0.25,
            vertical_offset_right=0.25
        ),
        GeometryGroupChord.create(
            application_id="COL-GEOMGROUP-0006-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=1.25,
            vertical_offset_right=1.25
        )
    ]
)

bracing_2_diaphragm_1_span_1 = GeometryGroupTransverseBracing.create(
    name = "Transverse Bracing as Diaphragm No.2",
    application_id="COL-GEOMGROUP-0002-TRANSVERSE-BRACING",
    bracing_orientation=ElementOrientationParaModel.SKEWED,
    x_start_first_bracing=0,
    number_of_bracings=1,
    left_girder_index=1,
    right_girder_index=2,
    horizontal_offset_left_girder=0.2,
    horizontal_offset_right_girder=0.2,
    spacing_type=SpacingTypeParaModel.UNIFORM,
    spacing_values=[10.0],
    braces=[
        GeometryGroupBrace.create(
            application_id="COL-GEOMGROUP-0002-BRACE",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0009-STANDARD-ANGLE",
            brace_type = BracingTypeParaModel.X_TYPE,
            vertical_offset_left_top=0.25,
            vertical_offset_left_bottom=0.95,
            vertical_offset_right_top=0.25,
            vertical_offset_right_bottom=0.95
        )
    ],
    chords=[
        GeometryGroupChord.create(
            application_id="COL-GEOMGROUP-0003-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=0.25,
            vertical_offset_right=0.25
        ),
        GeometryGroupChord.create(
            application_id="COL-GEOMGROUP-0004-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=1.25,
            vertical_offset_right=1.25
        )
    ]
)

bracing_1_diaphragm_1_span_1 = GeometryGroupTransverseBracing.create(
    name = "Transverse Bracing as Diaphragm No.1",
    application_id="COL-GEOMGROUP-0001-TRANSVERSE-BRACING",
    bracing_orientation=ElementOrientationParaModel.SKEWED,
    x_start_first_bracing=0,
    number_of_bracings=1,
    left_girder_index=0,
    right_girder_index=1,
    horizontal_offset_left_girder=0.2,
    horizontal_offset_right_girder=0.2,
    spacing_type=SpacingTypeParaModel.UNIFORM,
    spacing_values=[10.0],
    braces=[
        GeometryGroupBrace.create(
            application_id="COL-GEOMGROUP-0001-BRACE",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0009-STANDARD-ANGLE",
            brace_type = BracingTypeParaModel.K_TYPE,
            vertical_offset_left_top=0.35,
            vertical_offset_left_bottom=0.95,
            vertical_offset_right_top=0.35,
            vertical_offset_right_bottom=0.95,
            horizontal_offset_left=1.5,
            horizontal_offset_right=1.5
        )
    ],
    chords=[
        GeometryGroupChord.create(
            application_id="COL-GEOMGROUP-0001-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=0.25,
            vertical_offset_right=0.25
        ),
        GeometryGroupChord.create(
            application_id="COL-GEOMGROUP-0002-CHORD",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0010-STANDARD-CHANNEL",
            vertical_offset_left=1.25,
            vertical_offset_right=1.25
        )
    ]
)


# SPAN 1 - DIAPHRAGM 1

diaphragm_1_span_1 = GeometryGroupDiaphragm.create(
    name = "Diaphragm No.1",
    application_id="COL-GEOMGROUP-0001-DIAPHRAGM",
    material_id="MAT-0001-CONC-AASHTO",
    section_id = "SECT-0012-STANDARD-SOLID-RECTANGLE",
    support_index=0,
    diaphragm_type=DiaphragmTypeParaModel.BRACING_ENCASED,
    transverse_bracing=[
        bracing_1_diaphragm_1_span_1,
        bracing_2_diaphragm_1_span_1,
        bracing_3_diaphragm_1_span_1,
        bracing_4_diaphragm_1_span_1
        ]

)


# SPAN 1 - TRANSVERSE

transverse_span_1 = GeometryGroupTransverseMembers.create(
    application_id="COL-GEOMGROUP-0001-TRANSVERSE-MEMBERS",
    deck_slab=GeometryGroupDeckSlab.create(
        name="Deck Slab",
        application_id="COL-GEOMGROUP-0001-DECK-SLAB",
        material_id="MAT-0001-CONC-AASHTO",
        section_id="SECT-0008-STANDARD-SOLID-RECTANGLE"),
    diaphragms = [
        diaphragm_1_span_1,
        diaphragm_2_span_1
        ],
    transverse_bracings=[
        transverse_bracing_1_span_1
    ],
    plan_bracing=span_1_plan_bracing
)


# SPAN 1 - LONGITUDINAL

longitudinal_span_1 = GeometryGroupLongitudinalMembers.create(
    application_id="COL-GEOMGROUP-0001-LONGITUDINAL-MEMBERS",
    girders=[
        GeometryGroupGirder.create(
            name="Girder No.1",
            application_id="COL-GEOMGROUP-0001-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0006-COMPOSITE-I-ASYMMETRIC",
            girder_index=0
            ),
        GeometryGroupGirder.create(
            name="Girder No.2",
            application_id="COL-GEOMGROUP-0002-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0001-COMPOSITE-I-SYMMETRIC",
            girder_index=1
            ),
        GeometryGroupGirder.create(
            name="Girder No.3",
            application_id="COL-GEOMGROUP-0003-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0001-COMPOSITE-I-SYMMETRIC",
            girder_index=2
            ),
        GeometryGroupGirder.create(
            name="Girder No.4",
            application_id="COL-GEOMGROUP-0004-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0007-COMPOSITE-I-ASYMMETRIC",
            girder_index=3
            ),
        GeometryGroupGirder.create(
            name="Girder No.5",
            application_id="COL-GEOMGROUP-0005-GIRDER",
            material_id="MAT-0002-STEEL-AASHTO",
            section_id="SECT-0007-COMPOSITE-I-ASYMMETRIC",
            girder_index=4
            ),


    ]
)

#SPAN 1

span_1 = GeometryGroupSpan.create(
    application_id="COL-GEOMGROUP-0001-SPAN",
    name="Span No.1",
    span_index=0,
    top_deck_level_at_end=65.0,
    span_length=40.0,
    cracked_extents= CrackedExtentsParameterGroup.create(
        extents=[(35,40)]
    ),
    construction_sequence_details= ConstructionSequenceDetailsParameterGroup.create(
        segments=[(0,8),(8,20),(20,40)],
        pouring_orientation=ElementOrientationParaModel.SKEWED
    ),
    splices=SplicesParameterGroup.create(
        splices=[
            (10.0,"SECT-0004-COMPOSITE-I-SYMMETRIC"),
            (27.0,"SECT-0005-COMPOSITE-I-SYMMETRIC"),
        ]
    ),

    longitudinal_members=longitudinal_span_1,
    transverse_members=transverse_span_1
)


###############################################################################################
# SUPERSTRUCTURE
###############################################################################################

superstructure = GeometryGroupSuperstructure.create(
    application_id="COL-GEOMGROUP-0001-SUPERSTRUCTURE",
    name="Superstructure",
    total_deck_width=12,
    number_of_girders=5,
    girder_spacing_type=SpacingTypeParaModel.UNIFORM,
    girder_spacing_values=[2.0, 2.0, 2.0, 2.0],
    stringcourse_left_barrier_width=0.6,
    stringcourse_right_barrier_width=0.75,
    cantilever_left_width=3.0,
    cantilever_right_width=1.0,
    spans=[span_1,span_2,span_3]
)

# BRIDGE

bridge_geom = GeometryGroupBridge.create(
    application_id="COL-GEOMGROUP-0001-BRIDGE",
    bridge_type=BridgeTypeParaModel.STEEL_COMPOSITE,
    bridge_idealisation = BridgeIdealisationParaModel.GRILLAGE,
    number_of_spans = 3,
    girder_mesh_divisor = 20,
    top_deck_level = 65.5,
    top_deck_level_unit = "m",
    superstructure=superstructure,
    substructure=substructure,
    linkage = linkage
    )

# Sections

section_collection = SectionsCollection.create(
    application_id="COL-SECTIONS",
    sections=[
        SectionDataObject_CompositeISymmetric.create(
            name="girder_intermediate",
            description="Intermediate girder section",
            application_id="SECT-0001-COMPOSITE-I-SYMMETRIC",
            slab_width=2.00,
            slab_thickness=0.20,
            slab_girder_spacing=0.0,
            girder_top_flange_width=0.50,
            girder_top_flange_thickness=0.03,
            girder_bottom_flange_width=0.60,
            girder_bottom_flange_thickness=0.05,
            girder_web_thickness=0.025,
            girder_web_height=2.20,
            unit="m",
        ),

        SectionDataObject_CompositeISymmetric.create(
            name="girder_intermediate_high",
            description="Intermediate girder high section",
            application_id="SECT-0002-COMPOSITE-I-SYMMETRIC",
            slab_width=2.00,
            slab_thickness=0.20,
            slab_girder_spacing=0.0,
            girder_top_flange_width=0.50,
            girder_top_flange_thickness=0.03,
            girder_bottom_flange_width=0.60,
            girder_bottom_flange_thickness=0.05,
            girder_web_thickness=0.025,
            girder_web_height=3.20,
            unit="m",
        ),

        SectionDataObject_CompositeISymmetric.create(
            name="splice_section_1",
            description="Splice section 1",
            application_id="SECT-0003-COMPOSITE-I-SYMMETRIC",
            slab_width=2.00,
            slab_thickness=0.20,
            slab_girder_spacing=0.0,
            girder_top_flange_width=0.50,
            girder_top_flange_thickness=0.03,
            girder_bottom_flange_width=0.80,
            girder_bottom_flange_thickness=0.08,
            girder_web_thickness=0.025,
            girder_web_height=2.20,
            unit="m",
        ),

        SectionDataObject_CompositeISymmetric.create(
            name="splice_section_2",
            description="Splice section 2",
            application_id="SECT-0004-COMPOSITE-I-SYMMETRIC",
            slab_width=2.00,
            slab_thickness=0.20,
            slab_girder_spacing=0.0,
            girder_top_flange_width=0.50,
            girder_top_flange_thickness=0.03,
            girder_bottom_flange_width=0.50,
            girder_bottom_flange_thickness=0.02,
            girder_web_thickness=0.025,
            girder_web_height=2.20,
            unit="m",
        ),

        SectionDataObject_CompositeISymmetric.create(
            name="splice_section_3",
            description="Splice section 3",
            application_id="SECT-0005-COMPOSITE-I-SYMMETRIC",
            slab_width=2.00,
            slab_thickness=0.20,
            slab_girder_spacing=0.0,
            girder_top_flange_width=0.50,
            girder_top_flange_thickness=0.03,
            girder_bottom_flange_width=0.50,
            girder_bottom_flange_thickness=0.05,
            girder_web_thickness=0.025,
            girder_web_height=2.20,
            unit="m",
        ),

        SectionDataObject_CompositeIAsymmetric.create(
            name="girder_edge_left",
            description="Edge girder left",
            application_id="SECT-0006-COMPOSITE-I-ASYMMETRIC",
            slab_reference_offset=0.00,
            top_flange_reference_offset=0.75,
            bottom_flange_reference_offset=0.70,
            slab_width=3.00,
            slab_thickness=0.20,
            slab_girder_spacing=0.0,
            girder_top_flange_left_width=0.25,
            girder_top_flange_right_width=0.25,
            girder_top_flange_thickness=0.03,
            girder_bottom_flange_left_width=0.30,
            girder_bottom_flange_right_width=0.30,
            girder_bottom_flange_thickness=0.05,
            girder_web_thickness=0.025,
            girder_web_height=2.20,
            unit="m",
        ),

        SectionDataObject_CompositeIAsymmetric.create(
            name="girder_edge_right",
            description="Edge girder right",
            application_id="SECT-0007-COMPOSITE-I-ASYMMETRIC",
            slab_reference_offset=0.00,
            top_flange_reference_offset=1.75,
            bottom_flange_reference_offset=1.70,
            slab_width=3.00,
            slab_thickness=0.20,
            slab_girder_spacing=0.0,
            girder_top_flange_left_width=0.25,
            girder_top_flange_right_width=0.25,
            girder_top_flange_thickness=0.03,
            girder_bottom_flange_left_width=0.30,
            girder_bottom_flange_right_width=0.30,
            girder_bottom_flange_thickness=0.05,
            girder_web_thickness=0.025,
            girder_web_height=2.20,
            unit="m",
        ),

        SectionDataObject_SolidRectangle.create(
            name="deck slab",
            description="Deck slab section",
            application_id="SECT-0008-STANDARD-SOLID-RECTANGLE",
            height=0.20,
            width=1.00,
            unit="m",
        ),

        SectionDataObject_Angle.create(
            name="standard_angle_1",
            description="Bracing brace angle section",
            application_id="SECT-0009-STANDARD-ANGLE",
            height=0.203,
            width=0.203,
            web_thickness=0.022,
            flange_thickness=0.022,
            unit="m",
        ),

        SectionDataObject_Channel.create(
            name="standard_channel_2",
            description="Bracing chord channel section",
            application_id="SECT-0010-STANDARD-CHANNEL",
            height=0.35,
            top_flange_width=0.20,
            bottom_flange_width=0.22,
            web_thickness=0.014,
            top_flange_thickness=0.018,
            bottom_flange_thickness=0.020,
            web_inner_radius=0.010,
            flange_end_radius=0.008,
            unit="m",
        ),

        SectionDataObject_ISection.create(
            name="standard_I_section",
            description="Diaphragm I section",
            application_id="SECT-0011-STANDARD-ISECTION",
            total_height=1.01,
            top_flange_width=0.41,
            bottom_flange_width=0.50,
            web_thickness=0.015,
            top_flange_thickness=0.020,
            bottom_flange_thickness=0.050,
            web_inner_radius=0.010,
            flange_end_radius=0.010,
            unit="m",
        ),

        SectionDataObject_SolidRectangle.create(
            name="standard_rectangular",
            description="Diaphragm Section",
            application_id="SECT-0012-STANDARD-SOLID-RECTANGLE",
            height=1.50,
            width=0.40,
            unit="m",
        ),

        SectionDataObject_SolidCircle.create(
            name="standard_solid_round",
            description="Diaphragm Section",
            application_id="SECT-0013-STANDARD-SOLID-CIRCLE",
            diameter=0.18,
            unit="m",
        ),

        # SectionDataObject_Tapered.create(
        #     name="tapered_1",
        #     application_id="SECT-0013-TAPERED-ISYMMETRIC",
        #     start_section_application_id="SECT-0001-COMPOSITE-ISYMMETRIC",
        #     end_section_application_id="SECT-0002-COMPOSITE-ISYMMETRIC",
        #     section_type=SectionTypeParaModel.STEEL_I_SYMMETRIC,
        #     taper_y_variation=TaperVariationParaModel.PARABOLIC,
        #     taper_z_variation=TaperVariationParaModel.PARABOLIC,
        # ),

        # SectionDataObject_Tapered.create(
        #     name="tapered_2",
        #     application_id="SECT-0014-TAPERED-ISYMMETRIC",
        #     start_section_application_id="SECT-0002-COMPOSITE-ISYMMETRIC",
        #     end_section_application_id="SECT-0001-COMPOSITE-ISYMMETRIC",
        #     section_type=SectionTypeParaModel.STEEL_I_SYMMETRIC,
        #     taper_y_variation=TaperVariationParaModel.PARABOLIC,
        #     taper_z_variation=TaperVariationParaModel.PARABOLIC,
        # ),
    ],
)


# Materials

materials_collection = MaterialsCollection.create(
    application_id="COL-MATERIALS",
    materials=[
        ConcreteAASHTOMaterialDataObject.create(
            name="Concrete_C5000",
            application_id="MAT-0001-CONC-AASHTO",
            unit_weight=25,
            poissons_ratio=0.2,
            modulus_of_elasticity=20.5,
            elasticity_unit="GPa",
            coefficient_of_thermal_expansion=6.667e-6,
            thermal_coefficient_unit="1/Δ°F",
            expected_concrete_strength=50000,
            specified_concrete_strength=40000
        ),
        SteelAASHTOMaterialDataObject.create(
            name="Steel ASTM A709",
            application_id="MAT-0002-STEEL-AASHTO",
            unit_weight=77.09,
            poissons_ratio=0.3,
            modulus_of_elasticity=200,
            elasticity_unit="GPa",
            coefficient_of_thermal_expansion=6.5e-06,        
            thermal_coefficient_unit="1/Δ°F",
            minimum_steel_tensile_strength=450000,
            expected_steel_tensile_strength=550000,
            minimum_steel_yield_strength=345000,
            expected_steel_yield_strength=415000
        ),
        ReinforcementAASHTOMaterialDataObject.create(
            name="Rebar ASTM A615",
            application_id="MAT-0003-REBAR-AASHTO",
            unit_weight=76.98,                     
            unit_weight_unit="kN/m³",
            modulus_of_elasticity=200,             
            elasticity_unit="GPa",
            poissons_ratio=0.30,
            coefficient_of_thermal_expansion=6.7e-06,
            thermal_coefficient_unit="1/Δ°F",

            minimum_reinforcement_yield_strength=420000,      
            expected_reinforcement_yield_strength=500000,     

            minimum_reinforcement_tensile_strength=620000,    
            expected_reinforcement_tensile_strength=690000,   

            strength_unit="kN/m²",
        )
    ]
)



model_config = BDA_ModelDataDataObject.create(
    model_unit_system=ModelUnitSystemEnum.US_CUSTOMARY,
    output_software=OutputSoftwareEnum.CSI_BRIDGE,
    design_code=DesignCodesEnum.AASHTO,
    structure_type=StructureTypeEnum.STEEL_COMPOSITE
)

model = ModelRootCollection.create(
    model_config=model_config,
    materials=materials_collection,
    sections=section_collection,
    geometry=bridge_geom
)

# print(model.model_dump_json(indent=4,by_alias=True))

ingest_ui_json_and_commit(
    json_data=model.model_dump(
        by_alias=True,
        exclude_none=True,
        exclude_defaults=False,
        mode="json"
    ),
    pydantic_model=ModelRootCollection,
    speckle_url="https://design.jacobs.com/projects/8f0d636aa6/models/0ed6df7cda",
    commit_message=(
            f"MVP Steel Composite Example Model - "
            f"{datetime.datetime.now():%Y-%m-%d %H:%M}"
    )
)