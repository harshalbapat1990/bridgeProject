"""Material ParaModels for grouped material properties and design parameters.

The contract follows the architecture:

* ``material_type`` and ``material_model_type`` identify the material.
* ``general_properties`` contains model-level common properties.
* ``design_parameters`` contains type-specific design parameters.
"""

from __future__ import annotations

from typing import Any, Dict,  Optional, Type, Union, Tuple

from pydantic import field_validator, Field, AliasPath, AliasChoices

from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel
from bda.contracts.paramodel.shared.case_insensitive_enum import CaseInsensitiveEnum
from bda.contracts.shared import QuantityParaModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MaterialTypeParaModel(CaseInsensitiveEnum):
    CONCRETE = 'concrete'
    STEEL = 'steel'
    REINFORCEMENT = 'steel reinforcement'
    TENDON = 'tendon'


class StandardCodeParaModel(CaseInsensitiveEnum):
    AASHTO = 'AASHTO'
    EUROCODE = "EUROCODE"


class MaterialModelTypeParaModel(CaseInsensitiveEnum):
    ISOTROPIC = 'isotropic'
    ORTHOTROPIC = 'orthotropic'


# ---------------------------------------------------------------------------
# Base material ParaModel
# ---------------------------------------------------------------------------


class MaterialBaseParaModel(BaseModelParaModel):
    """Single material entry with grouped fields."""

    material_id: str = Field(validation_alias=AliasChoices("material_id", "applicationId"))
    name: str
    material_type: MaterialTypeParaModel = Field(
        validation_alias=AliasChoices(
            "material_type",
            AliasPath( "properties",
                             "General Material Properties",
                                   "group_parameters",
                                   "Material Type",
                                   "provided_value")))

    material_model_type: MaterialModelTypeParaModel = Field(
        validation_alias=AliasChoices(
            "material_model_type",
            AliasPath( "properties",
                             "General Material Properties",
                      "group_parameters",
                      "Isotropy",
                      "provided_value")))

    standard_code: StandardCodeParaModel = Field(
        validation_alias=AliasChoices(
            "standard_code",
            AliasPath( "properties",
                             "General Material Properties",
                      "group_parameters",
                      "Material Design Code",
                      "provided_value")))

    general_properties: GeneralMaterialPropertiesParaModel = Field(
        validation_alias=AliasChoices(
            "general_properties",
            AliasPath( "properties",
                             "General Material Properties",
                      "group_parameters")))

    design_parameters: Optional[DesignParametersParaModel] = Field(
        validation_alias=AliasChoices(
            "design_parameters",
            AliasPath( "properties",
                             "Design Material Properties",
                      "group_parameters"),
            AliasPath( "properties",
                             "Concrete Material Properties",
                      "group_parameters"),
            AliasPath( "properties",
                             "Steel Material Properties",
                      "group_parameters"),
            AliasPath( "properties",
                             "Tendon Material Properties",
                      "group_parameters")),
        default=None)


    @field_validator("design_parameters", mode="after")
    @classmethod
    def _map_design_parameters(cls, v: Any, info):
        if v is None:
            return v

        material_type = info.data.get("material_type")
        standard_code = info.data.get("standard_code")

        if material_type is None or standard_code is None:
            return v

        parameters_cls = _DESIGN_PARAMETERS_BY_MATERIAL_TYPE.get(
            (standard_code, material_type)
        )
        if parameters_cls is None:
            raise ValueError(
                f"No design parameters model for "
                f"standard_code={standard_code} and material_type={material_type}"
            )
        # return v
        return parameters_cls.model_validate(v.model_dump())


    @field_validator("general_properties", mode="after")
    @classmethod
    def _map_general_properties(cls, v: Any, info):
        if v is None:
            return v

        model_type = info.data.get("material_model_type")
        if model_type is None:
            return v

        parameters_cls = _GENERAL_PROPERTIES_BY_MODEL_TYPE.get(model_type)
        if parameters_cls is None:
            raise ValueError(f"No general properties model for {model_type}")

        return parameters_cls.model_validate(v)


# ---------------------------------------------------------------------------
# General properties
# ---------------------------------------------------------------------------


class GeneralMaterialPropertiesBase(BaseModelParaModel):
    """Common properties for all material model types."""

    unit_weight: QuantityParaModel = Field(validation_alias=AliasChoices(
        "unit_weight", "Density", "Unit Weight"))


class GeneralMaterialIsotropicProperties(GeneralMaterialPropertiesBase):
    """General properties for isotropic material model."""

    modulus_of_elasticity: QuantityParaModel = Field(validation_alias=AliasChoices(
        "modulus_of_elasticity", "Modulus of Elasticity"))
    thermal_coefficient: QuantityParaModel = Field(validation_alias=AliasChoices(
        "thermal_coefficient", "Coefficient of Thermal Expansion"))
    poissons_ratio: QuantityParaModel = Field(validation_alias=AliasChoices(
        "poissons_ratio", "Poisson's Ratio"))


class GeneralMaterialOrthotropicProperties(GeneralMaterialPropertiesBase):
    """Placeholder for orthotropic properties (not included in MVP)."""
    pass

GeneralMaterialPropertiesParaModel = Union[
    GeneralMaterialIsotropicProperties,
    GeneralMaterialOrthotropicProperties,
]


# ---------------------------------------------------------------------------
# Design parameters
# ---------------------------------------------------------------------------


class DesignParametersBase(BaseModelParaModel):
    """Base type for type-specific design parameters."""
    pass


class DesignParametersConcreteAashtoParaModel(DesignParametersBase):
    specified_minimum_compressive_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "specified_minimum_compressive_strength", "Specified Concrete Strength"))
    expected_compressive_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "expected_compressive_strength", "Expected Concrete Strength"))
    initial_concrete_comp_strength_at_casting: Optional[QuantityParaModel] = None
    friction_factor: Optional[QuantityParaModel] = None


class GeneralSteelDesignParametersAashtoParaModelBase(DesignParametersBase):
    specified_minimum_yield_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "specified_minimum_yield_strength", "Minimum Steel Yield Strength"))
    specified_minimum_tensile_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "specified_minimum_tensile_strength", "Minimum Steel Tensile Strength"))


class SteelDesignParametersAashtoParaModel(GeneralSteelDesignParametersAashtoParaModelBase):
    expected_yield_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "expected_yield_strength", 'Expected Steel Yield Strength'))
    expected_tensile_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "expected_tensile_strength", "Expected Steel Tensile Strength"))


class ReinforcementDesignParametersAashtoParaModel(GeneralSteelDesignParametersAashtoParaModelBase):
    expected_yield_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "expected_yield_strength", 'Expected Steel Yield Strength'))
    expected_tensile_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "expected_tensile_strength", "Expected Steel Tensile Strength"))


class TendonDesignParametersAashtoParaModel(DesignParametersBase):
    specified_minimum_yield_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "specified_minimum_yield_strength",
        "Prestressing/Post-Tensioning Steel Yield Strength"))
    specified_minimum_tensile_strength: QuantityParaModel = Field(validation_alias=AliasChoices(
        "specified_minimum_tensile_strength",
        "Prestressing/Post-Tensioning Steel Specified Minimum Tensile Strength"))

class DesignParametersConcreteEurocodeParaModel(DesignParametersBase):
    specified_minimum_compressive_strength: QuantityParaModel
    expected_compressive_strength: QuantityParaModel
    initial_concrete_comp_strength_at_casting: Optional[QuantityParaModel] = None
    friction_factor: Optional[QuantityParaModel] = None


class GeneralSteelDesignParametersEurocodeParaModelBase(DesignParametersBase):
    """Placeholder for eurocode properties (not included in MVP)."""
    pass


class SteelDesignParametersEurocodeParaModel(GeneralSteelDesignParametersEurocodeParaModelBase):
    """Placeholder for eurocode properties (not included in MVP)."""
    pass


class ReinforcementDesignParametersEurocodeParaModel(GeneralSteelDesignParametersEurocodeParaModelBase):
    """Placeholder for eurocode properties (not included in MVP)."""
    pass


class TendonDesignParametersEurocodeParaModel(GeneralSteelDesignParametersEurocodeParaModelBase):
    """Placeholder for eurocode properties (not included in MVP)."""
    pass


DesignParametersParaModel = Union[
    DesignParametersConcreteAashtoParaModel,
    SteelDesignParametersAashtoParaModel,
    ReinforcementDesignParametersAashtoParaModel,
    TendonDesignParametersAashtoParaModel,
    # MODELS FOR EUROCODES TO BE ADDED HERE
]


_DESIGN_PARAMETERS_BY_MATERIAL_TYPE: Dict[
    Tuple[StandardCodeParaModel, MaterialTypeParaModel],
    Type[DesignParametersBase]] = {
    (StandardCodeParaModel.AASHTO, MaterialTypeParaModel.CONCRETE): DesignParametersConcreteAashtoParaModel,
    (StandardCodeParaModel.AASHTO, MaterialTypeParaModel.STEEL): SteelDesignParametersAashtoParaModel,
    (StandardCodeParaModel.AASHTO, MaterialTypeParaModel.REINFORCEMENT): ReinforcementDesignParametersAashtoParaModel,
    (StandardCodeParaModel.AASHTO, MaterialTypeParaModel.TENDON): TendonDesignParametersAashtoParaModel,
    # DESIGN PARAMETERS FOR EUROCODE ARE NOT INCLUDED IN MVP, BUT PLACEHOLDERS ARE DEFINED FOR FUTURE EXTENSION
    # MAPPING TO BE DEFINED HERE
}

_GENERAL_PROPERTIES_BY_MODEL_TYPE = {
    MaterialModelTypeParaModel.ISOTROPIC: GeneralMaterialIsotropicProperties,
    MaterialModelTypeParaModel.ORTHOTROPIC: GeneralMaterialOrthotropicProperties,
}


MaterialParaModel = MaterialBaseParaModel
