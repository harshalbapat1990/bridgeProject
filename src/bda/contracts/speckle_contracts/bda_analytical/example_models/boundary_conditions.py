from bda.infrastructure.data_providers.speckle_helpers.speckle_send_object import ingest_ui_json_and_commit
import datetime

from bda.contracts.speckle_contracts.bda_analytical.model_root import ModelRootCollection
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_DataObject import (
    BDA_ModelDataDataObject,
    ModelUnitSystemEnum,
    OutputSoftwareEnum,
    DesignCodesEnum,
    StructureTypeEnum
)

import json

from bda.contracts.paramodel.groups.enums import (
    BearingConfigurationTypeParaModel,
    ElementOrientationParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.boundary_conditions_collection import BoundaryConditionsCollection

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.foundation_bc_collection import FoundationBCCollection

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_bc_collection import BearingBCCollection

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_bc_data_object import (
    BearingBCDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.lumped_foundation_data_object import (
    LumpedFoundationDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.pile_interaction_foundation_data_object import (
    PileDefinitionInput,
    PileInteractionFoundationDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.spring_parameters import (
    BoundaryConditionSpringParameterGroup,
    BoundaryConditionTranslationalSpringParameterGroup,
)
from bda.contracts.paramodel.foundations.enums import DofTypeEnumParaModel, FoundationModelTypeParaModel, \
    FoundationApplicationTypeEnumParaModel, SoilProfileTypeEnumParaModel

# -----------------------------
# Bearing BC examples
# -----------------------------
free_bearing = BearingBCDataObject.create_free(
    name="Free Bearing Example",
    application_id="BC-BEARING-0001",
    support_index=0,
    girder_index=0,
    bearing_index=0,
    configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
    orientation=ElementOrientationParaModel.ORTHOGONAL,
)

fixed_bearing = BearingBCDataObject.create_fixed(
    name="Fixed Bearing Example",
    application_id="BC-BEARING-0002",
    support_index=0,
    girder_index=1,
    bearing_index=1,
    configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
    orientation=ElementOrientationParaModel.ORTHOGONAL,
)

custom_bearing = BearingBCDataObject.create_user_defined(
    name="Custom Bearing Example",
    application_id="BC-BEARING-0003",
    support_index=1,
    girder_index=2,
    bearing_index=2,
    configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
    orientation=ElementOrientationParaModel.SKEWED,
    sdx_value=100000,
    sdy_value=110000,
    sdz_value=120000,
    srx_value=25000,
    sry_value=27500,
    srz_value=30000,
)

bearing_collection = BearingBCCollection.create(
    bearing_conditions=[
        free_bearing,
        fixed_bearing,
        custom_bearing,
    ]
)

# -----------------------------
# Foundation BC examples
# -----------------------------
spring_definition = BoundaryConditionSpringParameterGroup.create(
    sdx_dof_type="free",
    sdy_dof_type="free",
    sdz_dof_type="fixed",
    srx_dof_type="free",
    sry_dof_type="free",
    srz_dof_type="fixed",
)

translational_spring_definition = BoundaryConditionTranslationalSpringParameterGroup.create(
    sdx_dof_type=DofTypeEnumParaModel.FREE,
    sdy_dof_type=DofTypeEnumParaModel.FREE,
    sdz_dof_type=DofTypeEnumParaModel.FIXED,
)

lumped_bearing_based = LumpedFoundationDataObject.create(
    name="Lumped Bearing-Based Foundation",
    application_id="BC-FOUNDATION-LUMPED-0001",
    support_index=1,
    foundation_model_type=FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL,
    foundation_application_type=FoundationApplicationTypeEnumParaModel.BEARING_BASED,
    orientation=ElementOrientationParaModel.ORTHOGONAL,
    vertical_offset=0.5,
    vertical_offset_unit="m",
    spring_definition=spring_definition,
)

lumped_substructure_based = LumpedFoundationDataObject.create(
    name="Lumped Substructure-Based Foundation",
    application_id="BC-FOUNDATION-LUMPED-0002",
    support_index=2,
    foundation_model_type=FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL,
    foundation_application_type=FoundationApplicationTypeEnumParaModel.SUBSTRUCTURE_ELEMENT_BASED,
    orientation=ElementOrientationParaModel.SKEWED,
    spring_definition=spring_definition,
)

pile_foundation = PileInteractionFoundationDataObject.create(
    name="Pile Interaction Foundation",
    application_id="BC-FOUNDATION-PILE-0001",
    support_index=3,
    foundation_model_type=FoundationModelTypeParaModel.PILE_INTERACTION_MODEL,
    pile_definitions=[
        PileDefinitionInput(
            pile_index=1,
            soil_profile_type=SoilProfileTypeEnumParaModel.UNIFORM,
            top_node_spring_definition=translational_spring_definition,
            bottom_node_spring_definition=translational_spring_definition,
            intermediate_node_spring_definition=translational_spring_definition,
        )
    ],
)

foundation_collection = FoundationBCCollection.create(
    foundations=[
        lumped_bearing_based,
        lumped_substructure_based,
        pile_foundation,
    ]
)

combined_collection = BoundaryConditionsCollection.create(
    bearing_conditions=bearing_collection,
    foundation_conditions=foundation_collection,
)


# model_config
model_config = BDA_ModelDataDataObject.create(
    model_unit_system=ModelUnitSystemEnum.METRIC,
    output_software=OutputSoftwareEnum.CSI_BRIDGE,
    design_code=DesignCodesEnum.AASHTO,
    structure_type=StructureTypeEnum.STEEL_COMPOSITE
)

model = ModelRootCollection.create(
    model_config=model_config,
    boundary_conditions= combined_collection
)


ingest_ui_json_and_commit(
    json_data=model.model_dump(
        by_alias=True,
        mode="json"
    ),
    pydantic_model=ModelRootCollection,
    speckle_url="https://design.jacobs.com/projects/8f0d636aa6/models/092db8e740",
    commit_message=(
        f"Boundary Conditions model - "
        f"{datetime.datetime.now():%Y-%m-%d %H:%M}"
    )
)