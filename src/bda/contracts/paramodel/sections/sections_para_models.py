"""
Section ParaModels – raw JSON shape for all section families.

Discriminator strategy
----------------------
``section_type`` is NOT globally unique (``"angle"`` may exist for both ``db``
and ``user`` families).  The :class:`SectionParaModelAdapter` therefore
dispatches via a ``(section_family, section_type)`` lookup table instead of
Pydantic's built-in discriminated union.

Families
--------
* ``user``      → :class:`SectionUserAngleParaModel` … :class:`SectionUserSolidRoundParaModel`
* ``composite`` → :class:`SectionCompositeSteelISymmetricParaModel`, :class:`SectionCompositeSteelIAsymmetricParaModel`
* ``psc``       → :class:`SectionPSCValueParaModel`, :class:`SectionPSC1CellParaModel`, :class:`SectionPSC2CellParaModel`
* ``tapered``   → :class:`SectionTaperedParaModel`
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, Union, Tuple, Literal, Annotated

from pydantic import BaseModel, model_validator, AliasChoices, Field, AliasPath, field_validator

from bda.contracts.paramodel.sections.dimensions_para_models import (
    DimensionsAngleParaModel,
    DimensionsISectionParaModel,
    DimensionsBoxParaModel,
    DimensionsChannelParaModel,
    DimensionsSolidRectangleParaModel,
    DimensionsSolidRoundParaModel,
    DimensionsPipeParaModel,
    DimensionsCompositeSteelISymmetricParaModel,
    DimensionsCompositeSteelIAsymmetricParaModel,
    DimensionsPSCValueParaModel,
    DimensionsPSC1or2CellsParaModel, DimensionsTendonUserParaModel,
)
from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel
from bda.contracts.paramodel.shared.case_insensitive_enum import CaseInsensitiveEnum
from bda.contracts.shared import QuantityParaModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SectionTypeParaModel(CaseInsensitiveEnum):
    ANGLE = "Angle"
    I_SECTION = "i-section"
    BOX = "box"
    CHANNEL = "channel"
    SOLID_RECTANGLE = "solid rectangle"
    SOLID_ROUND = "solid circle"
    PIPE = "pipe"
    STEEL_I_SYMMETRIC = "composite I symmetric"
    STEEL_I_ASYMMETRIC = "composite I asymmetric"
    PSC_VALUE = "psc value"
    PSC_1CELL = "psc 1cell"
    PSC_2CELLS = "psc 2cells"
    TENDON_USER = "tendon-user"


class SectionFamilyParaModel(CaseInsensitiveEnum):
    STANDARD_SHAPE = "standard shape"
    COMPOSITE = "composite"
    PSC = "psc"
    TAPERED = "tapered"
    TENDON = "tendon"

# removed from MVP implementation for section, but leaving here for future development
# and usage in other areas of the codebase (e.g., tendon geometry)
class SectionOffsetParaModel(CaseInsensitiveEnum):
    CENTER_TOP = "center-top"
    LEFT_TOP = "left-top"
    RIGHT_TOP = "right-top"
    CENTER_CENTER = "center-center"
    LEFT_CENTER = "left-center"
    RIGHT_CENTER = "right-center"
    CENTER_BOTTOM = "center-bottom"
    LEFT_BOTTOM = "left-bottom"
    RIGHT_BOTTOM = "right-bottom"


class TaperVariationParaModel(CaseInsensitiveEnum):
    LINEAR = "linear"
    PARABOLIC = "parabolic"
    CUBIC = "cubic"


# ---------------------------------------------------------------------------
# Base section ParaModel
# ---------------------------------------------------------------------------

class SectionBaseParaModel(BaseModelParaModel):
    """Common fields present in every section entry."""
    section_id: str = Field(validation_alias=AliasChoices("applicationId", "section_id"))

    name: str

    description: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "description",
            AliasPath("properties", "Section Description", "provided_value")))

    section_family: SectionFamilyParaModel = Field(
        validation_alias=AliasChoices(
        "section_family",
            AliasPath("properties", "Section Family", "provided_value")))

    section_type: SectionTypeParaModel = Field(
        validation_alias=AliasChoices(
        "section_type",
            AliasPath("properties", "Section Type", "provided_value")))

    # removed from MVP implementation, but leaving here for future development
    #
    # offset: SectionOffsetParaModel = Field(
    #     validation_alias=AliasChoices(
    #     "offset",
    #         AliasPath("properties", "Section Offset", "provided_value")),
    #     default=SectionOffsetParaModel.CENTER_CENTER)


class WithDimensionsMixin(BaseModelParaModel):
    dimensions: Union[
        DimensionsAngleParaModel,
        DimensionsISectionParaModel,
        DimensionsBoxParaModel,
        DimensionsChannelParaModel,
        DimensionsSolidRectangleParaModel,
        DimensionsSolidRoundParaModel,
        DimensionsPipeParaModel,
        DimensionsCompositeSteelISymmetricParaModel,
        DimensionsCompositeSteelIAsymmetricParaModel,
        DimensionsPSCValueParaModel,
        DimensionsPSC1or2CellsParaModel,
        DimensionsTendonUserParaModel
    ] = Field(validation_alias=AliasChoices(
        "dimensions",
        AliasPath("properties", "Section Dimensions", "group_parameters")
    ))

# ---------------------------------------------------------------------------
# STANDARD - standard shapes sections
# ---------------------------------------------------------------------------

class SectionStandardAngleParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


class SectionStandardISectionParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


class SectionStandardBoxParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


class SectionStandardChannelParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


class SectionStandardSolidRectangleParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


class SectionStandardSolidRoundParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


class SectionStandardPipeParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


# ---------------------------------------------------------------------------
# Composite sections
# ---------------------------------------------------------------------------


class SectionCompositeSteelISymmetricParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


class SectionCompositeSteelIAsymmetricParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


# ---------------------------------------------------------------------------
# PSC sections
# SectionPSC1CellParaModel and SectionPSC2CellParaModel are not included in the
# MVP implementation and are reserved for future development.
# ---------------------------------------------------------------------------


class SectionPSCValueParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


class SectionPSC1CellParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


class SectionPSC2CellParaModel(SectionBaseParaModel, WithDimensionsMixin):
    pass


# ---------------------------------------------------------------------------
# Tapered sections
# ---------------------------------------------------------------------------

class SectionTaperedParaModel(SectionBaseParaModel):
    section_start_id: str = Field(
        validation_alias=AliasChoices(
            "section_start_id",
            AliasPath("properties", "Section Start ID", "provided_value")))

    section_end_id: str = Field(
        validation_alias=AliasChoices(
            "section_end_id",
            AliasPath("properties", "Section End ID", "provided_value")))

    taper_y_variation: TaperVariationParaModel = Field(
        validation_alias=AliasChoices(
            "taper_y_variation",
            AliasPath("properties", "Taper Y Variation", "provided_value")))

    taper_z_variation: TaperVariationParaModel = Field(
        validation_alias=AliasChoices(
            "taper_z_variation",
            AliasPath("properties", "Taper Z Variation", "provided_value")))


class BondTypeEnumParaModel(CaseInsensitiveEnum):
    BONDED = "Bonded"
    UNBONDED = "Unbonded"


class TendonTypeEnumParaModel(CaseInsensitiveEnum):
    # INTERNAL_PRE_TENSION = "Internal Pre-Tension"
    INTERNAL_POST_TENSION = "Internal Post-Tension"
    # EXTERNAL_POST_TENSION = "External Post-Tension"


class RelaxationClassCEBFIP1990EnumParaModel(CaseInsensitiveEnum):
    CLASS_1_NORMAL = "Class 1 (normal relaxation)"
    CLASS_2_LOW = "Class 2 (low relaxation)"


class RelaxationCodeEnumParaModel(CaseInsensitiveEnum):
    CEB_FIP_1990 = "CEB-FIP-1990"


class TendonGeneralPropertiesBaseParaModel(BaseModelParaModel):
    tendon_type: TendonTypeEnumParaModel


class InternalPostTensionPropertiesBaseParaModel(BaseModelParaModel):
    duct_diameter: QuantityParaModel
    bond_type: BondTypeEnumParaModel
    anchorage_set_slip: QuantityParaModel
    curvature_coefficient: float
    wobble_coefficient: QuantityParaModel


class TendonPropertiesInternalPostParaModel(
    TendonGeneralPropertiesBaseParaModel,
    InternalPostTensionPropertiesBaseParaModel
):
    tendon_type: Literal[
        TendonTypeEnumParaModel.INTERNAL_POST_TENSION
    ] = TendonTypeEnumParaModel.INTERNAL_POST_TENSION


_TendonGeneralPropertiesBaseParaModel = Annotated[
    Union[
        TendonPropertiesInternalPostParaModel,
    ],
    Field(discriminator="tendon_type"),
]


class RelaxationParamsBaseParaModel(BaseModelParaModel):
    relaxation_code: RelaxationCodeEnumParaModel


class RelaxationParamsCEBFIP1990ParaModel(RelaxationParamsBaseParaModel):
    relaxation_code: Literal[
        RelaxationCodeEnumParaModel.CEB_FIP_1990
    ] = RelaxationCodeEnumParaModel.CEB_FIP_1990
    relaxation_class: RelaxationClassCEBFIP1990EnumParaModel
    relaxation_1000_hours_value: float = Field(ge=0.0)


_RelaxationParamsBaseParaModel = Annotated[
    Union[
        RelaxationParamsCEBFIP1990ParaModel,
    ],
    Field(discriminator="relaxation_code")
]


class SectionTendonBaseParaModel(SectionBaseParaModel):
    general_properties: _TendonGeneralPropertiesBaseParaModel
    relaxation_parameters: _RelaxationParamsBaseParaModel


class SectionTendonUserParaModel(SectionTendonBaseParaModel, WithDimensionsMixin):
    pass

# ---------------------------------------------------------------------------
# Type alias (union for type hints / documentation only)
# ---------------------------------------------------------------------------

SectionParaModel = Union[
    SectionStandardAngleParaModel,
    SectionStandardISectionParaModel,
    SectionStandardBoxParaModel,
    SectionStandardChannelParaModel,
    SectionStandardSolidRectangleParaModel,
    SectionStandardSolidRoundParaModel,
    SectionStandardPipeParaModel,
    SectionCompositeSteelISymmetricParaModel,
    SectionCompositeSteelIAsymmetricParaModel,
    SectionPSCValueParaModel,
    SectionPSC1CellParaModel,
    SectionPSC2CellParaModel,
    SectionTaperedParaModel,
    SectionTendonUserParaModel
]

# ---------------------------------------------------------------------------
# Dispatch table  (section_family, section_type | None) → model class
# ---------------------------------------------------------------------------
# section_type=None is a wildcard that matches any type within that family.

_SECTION_CLASS_BY_SECTION_FAMILY_AND_TYPE: Dict[
    Tuple[SectionFamilyParaModel, SectionTypeParaModel | None],
    Type[SectionParaModel]] = {
    # Standard
    (SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.ANGLE): SectionStandardAngleParaModel,
    (SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.I_SECTION): SectionStandardISectionParaModel,
    (SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.BOX): SectionStandardBoxParaModel,
    (SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.CHANNEL): SectionStandardChannelParaModel,
    (SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.SOLID_RECTANGLE): SectionStandardSolidRectangleParaModel,
    (SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.SOLID_ROUND): SectionStandardSolidRoundParaModel,
    (SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.PIPE): SectionStandardPipeParaModel,
    # Composite
    (SectionFamilyParaModel.COMPOSITE, SectionTypeParaModel.STEEL_I_SYMMETRIC): SectionCompositeSteelISymmetricParaModel,
    (SectionFamilyParaModel.COMPOSITE, SectionTypeParaModel.STEEL_I_ASYMMETRIC): SectionCompositeSteelIAsymmetricParaModel,
    # PSC
    (SectionFamilyParaModel.PSC, SectionTypeParaModel.PSC_VALUE): SectionPSCValueParaModel,
    (SectionFamilyParaModel.PSC, SectionTypeParaModel.PSC_1CELL): SectionPSC1CellParaModel,
    (SectionFamilyParaModel.PSC, SectionTypeParaModel.PSC_2CELLS): SectionPSC2CellParaModel,
    # Tapered – one model regardless of section_type
    (SectionFamilyParaModel.TAPERED, None):              SectionTaperedParaModel,
    # Tendons
    (SectionFamilyParaModel.TENDON, SectionTypeParaModel.TENDON_USER): SectionTendonUserParaModel,
}


class SectionParaModelAdapter(BaseModelParaModel):
    section: SectionParaModel

    @model_validator(mode="before")
    @classmethod
    def _dispatch_sections(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        raw_section_family = data.get("section_family")
        if raw_section_family is None:
            raw_section_family = (
                data.get("properties", {})
                .get("Section Family", {})
                .get("provided_value"))

        raw_section_type = data.get("section_type")
        if raw_section_type is None:
            raw_section_type = (
                data.get("properties", {})
                .get("Section Type", {})
                .get("provided_value"))

        try:
            section_family = (
                raw_section_family
                if isinstance(raw_section_family, SectionFamilyParaModel)
                else SectionFamilyParaModel(raw_section_family)
            )
        except (TypeError, ValueError):
            raise ValueError(
                f"Unknown section family '{raw_section_family}'"
            ) from None

        try:
            section_type = (
                raw_section_type
                if isinstance(raw_section_type, SectionTypeParaModel)
                else SectionTypeParaModel(raw_section_type)
            )
        except (TypeError, ValueError):
            raise ValueError(
                f"Unknown section type '{raw_section_type}'"
            ) from None

        if section_family == SectionFamilyParaModel.TAPERED:
            section_type = None

        section_cls = _SECTION_CLASS_BY_SECTION_FAMILY_AND_TYPE.get((section_family, section_type))
        if section_cls is None:
            raise ValueError(
                f"No section model for section family '{section_family}' "
                f"and section type '{section_type}'"
            )
        return {"section": section_cls.model_validate(data)}

    @classmethod
    def parse(cls, data: dict) -> SectionParaModel:
        return cls.model_validate(data).section
