from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
)

from bda.contracts.speckle_contracts.base_objects import UnitlessParameter, ParameterGroup

from bda.contracts.paramodel.groups.enums import (
    SpacingTypeParaModel,
    StructuralComponentTypeParaModel,
    BridgeTypeParaModel,
    BridgeIdealisationParaModel
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_superstructure import (
    GeometryGroupSuperstructure
    )

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_substructure import (
    GeometryGroupSubstructure
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_linkage import (
    GeometryGroupLinkage,
)


from typing import Annotated, ClassVar, Literal, Union
from pydantic import Field, BaseModel, model_validator

from bda.contracts.speckle_contracts.unit_parameters import LengthParameter


## Type Specific Group Parameters

# Bridge Type
class BridgeTypeParameter(UnitlessParameter[BridgeTypeParaModel]):
    name: Literal["Bridge Type"] = "Bridge Type"

    description: Literal[
        "Type of bridge (e.g., Steel Composite or PSC BoX)"
    ] = "Type of bridge (e.g., Steel Composite or PSC BoX)"

    symbol: None = None

    provided_value: BridgeTypeParaModel

# Bridge Idealisation
class BridgeIdealisationParameter(UnitlessParameter[BridgeIdealisationParaModel]):
    name: Literal["Bridge Idealisation"] = "Bridge Idealisation"

    description: Literal[
        "Type of bridge idealisation (e.g., Grillage or LineBeam)"
    ] = "Type of bridge idealisation (e.g., Grillage or LineBeam)"

    symbol: None = None

    provided_value: BridgeIdealisationParaModel

# Number of Spans
class NumberOfSpansParameter(UnitlessParameter[int]):
    name: Literal["Number of Spans"] = "Number of Spans"

    description: Literal[
        "Number of spans in the bridge"
    ] = "Number of spans in the bridge"

    symbol: None = None

    provided_value: int

# Top Deck level

class TopDeckLevelParameter(LengthParameter):
    name: Literal["Top Deck Level"] = "Top Deck Level"

    description: Literal[
        "Level of the top deck in the bridge"
    ] = "Level of the top deck in the bridge"

    symbol: None = None

    provided_unit: Literal["m", "ft"]
    base_unit: Literal["m"] = "m"

    

# Girder Mesh Divisor

class GirderMeshDivisorParameter(UnitlessParameter[int]):
    name: Literal["Girder Mesh Divisor"] = "Girder Mesh Divisor"

    description: Literal[
        "Divisor for girder mesh generation"
    ] = "Divisor for girder mesh generation"

    symbol: None = None

    provided_value: int

# Analysis Setting Parameter Group

class AnalysisSettingsGroupParameters(BaseModel):
    girder_mesh_divisor: GirderMeshDivisorParameter = Field(
        alias="Girder Mesh Divisor"
    )

class AnalysisSettingsParameterGroup(ParameterGroup):
    name: Literal["Analysis Settings"] = "Analysis Settings"

    description: Literal[
        "Analysis setting parameters for the bridge"
    ] = "Analysis setting parameters for the bridge"

    symbol: None = None

    group_parameters: AnalysisSettingsGroupParameters

class BridgeGroupPropertiesParameters(BaseModel):
    bridge_type: BridgeTypeParameter = Field(alias="Bridge Type")
    bridge_idealisation: BridgeIdealisationParameter = Field(alias="Bridge Idealisation")
    number_of_spans: NumberOfSpansParameter = Field(alias="Number of Spans")
    top_deck_level: TopDeckLevelParameter = Field(alias="Top Deck Level")
    analysis_settings: AnalysisSettingsParameterGroup = Field(alias="Analysis Settings")

class BridgeGroupProperties(GeometryGroupParameterProperties):
    group_parameters: BridgeGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        bridge_type: BridgeTypeParaModel,
        bridge_idealisation: BridgeIdealisationParaModel,
        number_of_spans: int,
        top_deck_level: float,
        girder_mesh_divisor: int,
        top_deck_level_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "BridgeGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                BridgeGroupPropertiesParameters(
                    **{
                        "Bridge Type":
                            BridgeTypeParameter(
                                isUser=isUser,
                                provided_value=bridge_type,
                            ),

                        "Bridge Idealisation":
                            BridgeIdealisationParameter(
                                isUser=isUser,
                                provided_value=bridge_idealisation,
                            ),

                        "Number of Spans":
                            NumberOfSpansParameter(
                                isUser=isUser,
                                provided_value=number_of_spans,
                            ),

                        "Top Deck Level":
                            TopDeckLevelParameter(
                                isUser=isUser,
                                provided_value=top_deck_level,
                                provided_unit=top_deck_level_unit,
                                base_value=top_deck_level,
                            ),

                        "Analysis Settings":
                            AnalysisSettingsParameterGroup(
                                isUser=isUser,
                                group_parameters=(
                                    AnalysisSettingsGroupParameters(
                                        **{
                                            "Girder Mesh Divisor":
                                                GirderMeshDivisorParameter(
                                                    isUser=isUser,
                                                    provided_value=(
                                                        girder_mesh_divisor
                                                    ),
                                                )
                                        }
                                    )
                                ),
                            ),
                    }
                )
            ),
        )
    

class BridgeStructureComponentGroupType(StructureComponentGroupType):
    provided_value: StructuralComponentTypeParaModel = StructuralComponentTypeParaModel.BRIDGE

class GeometryGroupPropertiesBridge(GeometryGroupProperties):
    structural_component_type: BridgeStructureComponentGroupType = Field(
        alias="Structural Component Type")
    
    group_properties: BridgeGroupProperties = Field(
        alias="Geometry Group Properties"
    )

class GeometryGroupParametersBridge(GeometryGroupParameters):
    """
    Mandatory child object that stores all metadata
    associated with a GeometryGroup.
    """

    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Bridge"
    ] = Field(
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Bridge",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Bridge"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-BRIDGE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesBridge

BridgeGroupElements = Annotated[
    Union[
        GeometryGroupParametersBridge,
        GeometryGroupSuperstructure,
        GeometryGroupSubstructure,
        GeometryGroupLinkage,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupBridge(GeometryGroupBase):
    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Bridge"
    ] = Field(
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Bridge",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Bridge"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-BRIDGE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    name: Literal["Bridge"] = "Bridge"

    elements: list[BridgeGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one bridge properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_Bridge"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # Optional, max one superstructure
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Superstructure"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                {
                    # Optional, max one substructure
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Substructure"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                {
                    # Optional, max one linkage
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Linkage"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
            ],
        },
    )

    @model_validator(mode="after")
    def validate_bridge_elements(self) -> "GeometryGroupBridge":

        bridge_properties_count = sum(
            1
            for element in self.elements
            if element.speckle_type
            == (
                "Objects.Data.DataObject:"
                "BDA_Geometry_Group_Properties_Bridge"
            )
        )

        superstructure_count = sum(
            1
            for element in self.elements
            if element.speckle_type
            == (
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Superstructure"
            )
        )

        substructure_count = sum(
            1
            for element in self.elements
            if element.speckle_type
            == (
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Substructure"
            )
        )

        linkage_count = sum(
            1
            for element in self.elements
            if element.speckle_type
            == (
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Linkage"
            )
        )

        if bridge_properties_count != 1:
            raise ValueError(
                "GeometryGroupBridge.elements must contain exactly one "
                "BDA_Geometry_Group_Properties_Bridge object. "
                f"Found {bridge_properties_count}."
            )

        if superstructure_count > 1:
            raise ValueError(
                "GeometryGroupBridge.elements may contain at most one "
                "BDA_Geometry_Group_Superstructure collection. "
                f"Found {superstructure_count}."
            )

        if substructure_count > 1:
            raise ValueError(
                "GeometryGroupBridge.elements may contain at most one "
                "BDA_Geometry_Group_Substructure collection. "
                f"Found {substructure_count}."
            )

        if linkage_count > 1:
            raise ValueError(
                "GeometryGroupBridge.elements may contain at most one "
                "BDA_Geometry_Group_Linkage collection. "
                f"Found {linkage_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        bridge_type: BridgeTypeParaModel,
        bridge_idealisation: BridgeIdealisationParaModel,
        number_of_spans: int,
        top_deck_level: float,
        girder_mesh_divisor: int,
        top_deck_level_unit: Literal["m", "ft"] = "m",
        superstructure: GeometryGroupSuperstructure | None = None,
        substructure: GeometryGroupSubstructure | None = None,
        linkage: GeometryGroupLinkage | None = None,
        application_id: str = "COL-GEOMGROUP-0001-BRIDGE",
        isUser: bool = True,
    ) -> "GeometryGroupBridge":

        elements: list[BridgeGroupElements] = [
            GeometryGroupParametersBridge(
                **{
                    "id": None,
                    "applicationId": application_id.replace(
                        "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                    ),
                    "bda_speckle_type": (
                        "Objects.Data.DataObject:"
                        "BDA_Geometry_Group_Properties_Bridge"
                    ),
                    "properties": GeometryGroupPropertiesBridge(
                        **{
                            "Structural Component Type":
                                BridgeStructureComponentGroupType(),

                            "Geometry Group Properties":
                                BridgeGroupProperties.create(
                                    bridge_type=bridge_type,
                                    bridge_idealisation=(
                                        bridge_idealisation
                                    ),
                                    number_of_spans=(
                                        number_of_spans
                                    ),
                                    top_deck_level=(
                                        top_deck_level
                                    ),
                                    girder_mesh_divisor=(
                                        girder_mesh_divisor
                                    ),
                                    top_deck_level_unit=(
                                        top_deck_level_unit
                                    ),
                                    isUser=isUser,
                                ),
                        }
                    ),
                }
            )
        ]

        if superstructure is not None:
            elements.append(superstructure)

        if substructure is not None:
            elements.append(substructure)

        if linkage is not None:
            elements.append(linkage)

        return cls(
            id=None,
            applicationId=application_id,
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Bridge"
            ),
            elements=elements,
        )

if __name__ == "__main__":

    bridge = GeometryGroupBridge.create(
        bridge_type=BridgeTypeParaModel.STEEL_COMPOSITE,
        bridge_idealisation=BridgeIdealisationParaModel.GRILLAGE,
        number_of_spans=1,
        top_deck_level=25.0,
        girder_mesh_divisor=10,
        application_id="COL-GEOMGROUP-0001-BRIDGE",
    )

    print(
        bridge.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )