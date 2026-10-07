from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, Field, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    DiaphragmTypeParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
    MaterialIdOptional,
    SectionIdOptional,
    create_optional_material_id,
    create_optional_section_id,
)

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup,
    UnitlessParameter,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_transverse_bracing import (
    GeometryGroupTransverseBracing,
)

from bda.contracts.speckle_contracts.bda_analytical.common_parameters import (
    SupportIndexParameter,
)
from bda.contracts.speckle_contracts.unit_parameters import LengthParameter


# =============================================================================
# DIAPHRAGM PARAMETERS
# =============================================================================


class DiaphragmTypeParameter(
    UnitlessParameter[DiaphragmTypeParaModel]
):
    name: Literal["Diaphragm Type"] = "Diaphragm Type"

    description: Literal[
        "Type of diaphragm"
    ] = "Type of diaphragm"

    symbol: None = None

    isUser: bool = False

    provided_value: DiaphragmTypeParaModel


class DiaphragmThickness(LengthParameter):
    name: Literal[
        "Diaphragm Thickness"
    ] = "Diaphragm Thickness"

    description: Literal[
        "Thickness of the diaphragm"
    ] = "Thickness of the diaphragm"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


# =============================================================================
# FIXED DIAPHRAGM TYPE PARAMETERS
# =============================================================================


class DiaphragmTypeBracingEncasedParameter(
    DiaphragmTypeParameter
):
    provided_value: Literal[
        DiaphragmTypeParaModel.BRACING_ENCASED
    ] = DiaphragmTypeParaModel.BRACING_ENCASED


class DiaphragmTypeSteelGirderParameter(
    DiaphragmTypeParameter
):
    provided_value: Literal[
        DiaphragmTypeParaModel.STEEL_GIRDER
    ] = DiaphragmTypeParaModel.STEEL_GIRDER


class DiaphragmTypeConcreteNonModelledParameter(
    DiaphragmTypeParameter
):
    provided_value: Literal[
        DiaphragmTypeParaModel.CONCRETE_NON_MODELLED
    ] = (
        DiaphragmTypeParaModel.CONCRETE_NON_MODELLED
    )


# =============================================================================
# GEOMETRY DETAILS PARAMETER GROUPS
# =============================================================================


class GeometryDetailsGroupParameters_BracingEncased(
    BaseModel
):
    diaphragm_type: (
        DiaphragmTypeBracingEncasedParameter
    ) = Field(
        alias="Diaphragm Type"
    )


class GeometryDetailsGroupParameters_SteelGirder(
    BaseModel
):
    diaphragm_type: (
        DiaphragmTypeSteelGirderParameter
    ) = Field(
        alias="Diaphragm Type"
    )


class GeometryDetailsGroupParameters_ConcreteNonModelled(
    BaseModel
):
    diaphragm_type: (
        DiaphragmTypeConcreteNonModelledParameter
    ) = Field(
        alias="Diaphragm Type"
    )

    diaphragm_thickness: DiaphragmThickness = Field(
        alias="Diaphragm Thickness"
    )


GeometryDetailsGroupParameters = Union[
    GeometryDetailsGroupParameters_BracingEncased,
    GeometryDetailsGroupParameters_SteelGirder,
    GeometryDetailsGroupParameters_ConcreteNonModelled,
]


# =============================================================================
# GEOMETRY DETAILS PARAMETER GROUP
# =============================================================================


class GeometryDetailsParameterGroup(ParameterGroup):
    name: Literal[
        "Geometry Details"
    ] = "Geometry Details"

    description: Literal[
        "Geometry details of diaphragm"
    ] = "Geometry details of diaphragm"

    symbol: None = None

    group_parameters: GeometryDetailsGroupParameters

    @classmethod
    def create(
        cls,
        diaphragm_type: DiaphragmTypeParaModel,
        diaphragm_thickness: float | None = None,
        diaphragm_thickness_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "GeometryDetailsParameterGroup":

        if diaphragm_type == DiaphragmTypeParaModel.BRACING_ENCASED:
            return cls(
                isUser=isUser,
                group_parameters=(
                    GeometryDetailsGroupParameters_BracingEncased(
                        **{
                            "Diaphragm Type":
                                DiaphragmTypeBracingEncasedParameter()
                        }
                    )
                ),
            )

        if diaphragm_type == DiaphragmTypeParaModel.STEEL_GIRDER:
            return cls(
                isUser=isUser,
                group_parameters=(
                    GeometryDetailsGroupParameters_SteelGirder(
                        **{
                            "Diaphragm Type":
                                DiaphragmTypeSteelGirderParameter()
                        }
                    )
                ),
            )

        if (
            diaphragm_type
            == DiaphragmTypeParaModel.CONCRETE_NON_MODELLED
        ):
            if diaphragm_thickness is None:
                raise ValueError(
                    "diaphragm_thickness is required for "
                    "CONCRETE_NON_MODELLED diaphragms."
                )

            return cls(
                isUser=isUser,
                group_parameters=(
                    GeometryDetailsGroupParameters_ConcreteNonModelled(
                        **{
                            "Diaphragm Type":
                                DiaphragmTypeConcreteNonModelledParameter(),

                            "Diaphragm Thickness":
                                DiaphragmThickness(
                                    isUser=isUser,
                                    provided_value=diaphragm_thickness,
                                    provided_unit=(
                                        diaphragm_thickness_unit
                                    ),
                                    base_value=diaphragm_thickness,
                                ),
                        }
                    )
                ),
            )

        raise ValueError(
            f"Unsupported diaphragm type: {diaphragm_type}"
        )


# =============================================================================
# DIAPHRAGM PROPERTY SET
# =============================================================================


class DiaphragmGroupPropertiesParameters(BaseModel):
    support_index: SupportIndexParameter = Field(
        alias="Support Index"
    )

    geometry_details: GeometryDetailsParameterGroup = Field(
        alias="Geometry Details"
    )


class DiaphragmGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: DiaphragmGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        support_index: int,
        diaphragm_type: DiaphragmTypeParaModel,
        diaphragm_thickness: float | None = None,
        diaphragm_thickness_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "DiaphragmGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                DiaphragmGroupPropertiesParameters(
                    **{
                        "Support Index":
                            SupportIndexParameter(
                                isUser=isUser,
                                provided_value=support_index,
                            ),

                        "Geometry Details":
                            GeometryDetailsParameterGroup.create(
                                diaphragm_type=diaphragm_type,
                                diaphragm_thickness=(
                                    diaphragm_thickness
                                ),
                                diaphragm_thickness_unit=(
                                    diaphragm_thickness_unit
                                ),
                                isUser=isUser,
                            ),
                    }
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class DiaphragmStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.DIAPHRAGM
    ] = StructuralComponentTypeParaModel.DIAPHRAGM


# =============================================================================
# DIAPHRAGM METADATA
# =============================================================================


class GeometryGroupPropertiesDiaphragm(
    GeometryGroupProperties
):
    structural_component_type: (
        DiaphragmStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdOptional = Field(
        alias="Material ID",
    )

    section_id: SectionIdOptional = Field(
        alias="Section ID",
    )

    group_properties: DiaphragmGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersDiaphragm(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_DIAPHRAGM
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_DIAPHRAGM.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-DIAPHRAGM$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesDiaphragm


# =============================================================================
# DIAPHRAGM GROUP
# =============================================================================


DiaphragmGroupElements = Annotated[
    Union[
        GeometryGroupParametersDiaphragm,
        GeometryGroupTransverseBracing,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupDiaphragm(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_DIAPHRAGM
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_DIAPHRAGM.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-DIAPHRAGM$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[DiaphragmGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one diaphragm properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_Diaphragm"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # Any number of Transverse Bracing objects
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Transverse_Bracing"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 0,
                },
            ],
        },
    )

    @model_validator(mode="after")
    def validate_diaphragm_elements(self) -> "GeometryGroupDiaphragm":
        diaphragm_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Diaphragm"
        )

        diaphragm_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == diaphragm_properties_speckle_type
        )

        if diaphragm_properties_count != 1:
            raise ValueError(
                "GeometryGroupDiaphragm.elements must contain "
                "exactly one "
                f"{diaphragm_properties_speckle_type} object. "
                f"Found {diaphragm_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str | None,
        section_id: str | None,
        support_index: int,
        diaphragm_type: DiaphragmTypeParaModel,
        transverse_bracing: (
            list[GeometryGroupTransverseBracing] | None
        ) = None,
        diaphragm_thickness: float | None = None,
        diaphragm_thickness_unit: Literal["m", "ft"] = "m",
        application_id: str = "COL-GEOMGROUP-0001-DIAPHRAGM",
        name: str | None = None,
        isUser: bool = True,
    ) -> "GeometryGroupDiaphragm":

        elements: list[DiaphragmGroupElements] = [
            GeometryGroupParametersDiaphragm(
                **{
                    "id": None,
                    "applicationId": application_id.replace(
                        "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                    ),
                    "bda_speckle_type": (
                        "Objects.Data.DataObject:"
                        "BDA_Geometry_Group_Properties_Diaphragm"
                    ),
                    "properties": (
                        GeometryGroupPropertiesDiaphragm(
                            **{
                                "Structural Component Type":
                                    DiaphragmStructureComponentGroupType(),

                                "Material ID":
                                    create_optional_material_id(
                                        material_id=material_id,
                                        isUser=False,
                                    ),

                                "Section ID":
                                    create_optional_section_id(
                                        section_id=section_id,
                                        isUser=False,
                                    ),

                                "Geometry Group Properties":
                                    DiaphragmGroupProperties.create(
                                        support_index=support_index,
                                        diaphragm_type=diaphragm_type,
                                        diaphragm_thickness=(
                                            diaphragm_thickness
                                        ),
                                        diaphragm_thickness_unit=(
                                            diaphragm_thickness_unit
                                        ),
                                        isUser=isUser,
                                    ),
                            }
                        )
                    ),
                }
            )
        ]

        if transverse_bracing:
            elements.extend(transverse_bracing)

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else f"Diaphragm_{support_index}", #TODO: Improve Autonaming
            elements=elements,
        )


if __name__ == "__main__":

    diaphragm_with_ids = GeometryGroupDiaphragm.create(
        material_id="steel",
        section_id="D1",
        support_index=1,
        diaphragm_type=(
            DiaphragmTypeParaModel.STEEL_GIRDER
        ),
    )

    print(
        diaphragm_with_ids.model_dump_json(
            indent=4
        )
    )

    diaphragm_without_ids = GeometryGroupDiaphragm.create(
        material_id=None,
        section_id=None,
        support_index=1,
        diaphragm_type=(
            DiaphragmTypeParaModel.STEEL_GIRDER
        ),
        application_id="COL-GEOMGROUP-0002-DIAPHRAGM",
    )

    print(
        diaphragm_without_ids.model_dump_json(
            indent=4
        )
    )