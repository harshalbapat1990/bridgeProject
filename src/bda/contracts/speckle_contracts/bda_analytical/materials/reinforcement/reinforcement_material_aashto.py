from __future__ import annotations

from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes

from typing import Literal, ClassVar

from pydantic import BaseModel, Field

from bda.contracts.paramodel.materials.materials_para_model import (
    MaterialModelTypeParaModel,
)

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    MaterialDesignCode_AASHTO,
    UnitWeight,
    ModulusOfElasticity,
    PoissonsRatio,
    CoefficientOfThermalExpansion,
    Isotropy,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.reinforcement.reinforcement_material_base import (
    MaterialType_Reinforcement,
    ReinforcementGeneralMaterialParameters,
    ReinforcementGeneralMaterialParameterGroup,
    ReinforcementMaterialDataObject_Properties,
    ReinforcementMaterialDataObject,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.shared.material_strength_parameters import (
    ExpectedYieldStrength,
    SpecifiedMinimumYieldStrength,
    ExpectedTensileStrength,
    SpecifiedMinimumTensileStrength,
)


# ==========================================================
# GENERAL MATERIAL PARAMETERS OVERRIDE
# ==========================================================

class ReinforcementAASHTOGeneralMaterialParameters(
    ReinforcementGeneralMaterialParameters
):
    material_design_code: MaterialDesignCode_AASHTO = Field(
        alias="Material Design Code"
    )


class ReinforcementAASHTOGeneralMaterialParameterGroup(
    ReinforcementGeneralMaterialParameterGroup
):
    group_parameters: (
        ReinforcementAASHTOGeneralMaterialParameters
    )


# ==========================================================
# REINFORCEMENT STRENGTH PARAMETERS
# ==========================================================

class SpecifiedMinimumYieldStrengthReinforcement(
    SpecifiedMinimumYieldStrength
):
    name: Literal[
        "Specified Minimum Reinforcement Yield Strength"
    ] = (
        "Specified Minimum Reinforcement Yield Strength"
    )

    description: Literal[
        "Specified minimum yield strength of reinforcement"
    ] = (
        "Specified minimum yield strength of reinforcement"
    )


class ExpectedYieldStrengthReinforcement(
    ExpectedYieldStrength
):
    name: Literal[
        "Expected Reinforcement Yield Strength"
    ] = (
        "Expected Reinforcement Yield Strength"
    )

    description: Literal[
        "Expected yield strength of reinforcement"
    ] = (
        "Expected yield strength of reinforcement"
    )


class SpecifiedMinimumTensileStrengthReinforcement(
    SpecifiedMinimumTensileStrength
):
    name: Literal[
        "Specified Minimum Reinforcement Tensile Strength"
    ] = (
        "Specified Minimum Reinforcement Tensile Strength"
    )

    description: Literal[
        "Specified minimum tensile strength of reinforcement"
    ] = (
        "Specified minimum tensile strength of reinforcement"
    )


class ExpectedTensileStrengthReinforcement(
    ExpectedTensileStrength
):
    name: Literal[
        "Expected Reinforcement Tensile Strength"
    ] = (
        "Expected Reinforcement Tensile Strength"
    )

    description: Literal[
        "Expected tensile strength of reinforcement"
    ] = (
        "Expected tensile strength of reinforcement"
    )


# ==========================================================
# DESIGN MATERIAL PARAMETERS
# ==========================================================

class ReinforcementAASHTODesignMaterialParameters(
    BaseModel
):
    expected_reinforcement_yield_strength: (
        ExpectedYieldStrengthReinforcement
    ) = Field(
        alias="Expected Reinforcement Yield Strength"
    )

    minimum_reinforcement_yield_strength: (
        SpecifiedMinimumYieldStrengthReinforcement
    ) = Field(
        alias="Minimum Reinforcement Yield Strength"
    )

    expected_reinforcement_tensile_strength: (
        ExpectedTensileStrengthReinforcement
    ) = Field(
        alias="Expected Reinforcement Tensile Strength"
    )

    minimum_reinforcement_tensile_strength: (
        SpecifiedMinimumTensileStrengthReinforcement
    ) = Field(
        alias="Minimum Reinforcement Tensile Strength"
    )


# ==========================================================
# DESIGN MATERIAL PARAMETER GROUP
# ==========================================================

class ReinforcementAASHTODesignMaterialParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Reinforcement Material Properties"
    ] = "Reinforcement Material Properties"

    description: Literal[
        "Reinforcement material properties"
    ] = "Reinforcement material properties"

    group_parameters: (
        ReinforcementAASHTODesignMaterialParameters
    )


# ==========================================================
# DATA OBJECT PROPERTIES
# ==========================================================

class ReinforcementAASHTOMaterialDataObjectProperties(
    ReinforcementMaterialDataObject_Properties
):
    general_material_properties: (
        ReinforcementAASHTOGeneralMaterialParameterGroup
    ) = Field(
        alias="General Material Properties"
    )

    reinforcement_material_properties: (
        ReinforcementAASHTODesignMaterialParameterGroup
    ) = Field(
        alias="Design Material Properties"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class ReinforcementAASHTOMaterialDataObject(
    ReinforcementMaterialDataObject
):
    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^MAT-\d{4}-REBAR-AASHTO$"
    )

    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN
    )

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_REINFORCEMENT_MATERIAL_AASHTO
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_REINFORCEMENT_MATERIAL_AASHTO.value, frozen=True)

    properties: (
        ReinforcementAASHTOMaterialDataObjectProperties
    )

    @classmethod
    def create(
        cls,
        name: str,
        unit_weight: float,
        modulus_of_elasticity: float,
        poissons_ratio: float,
        coefficient_of_thermal_expansion: float,
        expected_reinforcement_yield_strength: float,
        minimum_reinforcement_yield_strength: float,
        expected_reinforcement_tensile_strength: float,
        minimum_reinforcement_tensile_strength: float,
        unit_weight_unit: Literal["kN/m³", "kips/ft³"] = "kN/m³",
        strength_unit: Literal["kN/m²", "lbf/ft²"] = "kN/m²",
        elasticity_unit: Literal[
            "Pa",
            "kPa",
            "GPa",
            "kips/in²",
            "kN/m²",
        ] = "Pa",
        thermal_coefficient_unit: Literal[
            "1/Δ°C",
            "1/Δ°F",
        ] = "1/Δ°C",
        application_id: str = "reinforcement_aashto_1",
        isUser: bool = True,
    ) -> "ReinforcementAASHTOMaterialDataObject":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            properties=(
                ReinforcementAASHTOMaterialDataObjectProperties(
                    **{
                        "General Material Properties":
                            ReinforcementAASHTOGeneralMaterialParameterGroup(
                                isUser=isUser,
                                group_parameters=(
                                    ReinforcementAASHTOGeneralMaterialParameters(
                                        **{
                                            "Material Type":
                                                MaterialType_Reinforcement(
                                                    isUser=False
                                                ),

                                            "Material Design Code":
                                                MaterialDesignCode_AASHTO(
                                                    isUser=False
                                                ),

                                            "Isotropy":
                                                Isotropy(
                                                    isUser=isUser,
                                                    provided_value=(
                                                        MaterialModelTypeParaModel.ISOTROPIC
                                                    ),
                                                ),

                                            "Unit Weight":
                                                UnitWeight(
                                                    isUser=isUser,
                                                    provided_value=unit_weight,
                                                    provided_unit=unit_weight_unit,
                                                    base_value=unit_weight,
                                                ),

                                            "Modulus of Elasticity":
                                                ModulusOfElasticity(
                                                    isUser=isUser,
                                                    provided_value=modulus_of_elasticity,
                                                    provided_unit=elasticity_unit,
                                                    base_value=modulus_of_elasticity,
                                                ),

                                            "Poisson's Ratio":
                                                PoissonsRatio(
                                                    isUser=isUser,
                                                    provided_value=poissons_ratio,
                                                ),

                                            "Coefficient of Thermal Expansion":
                                                CoefficientOfThermalExpansion(
                                                    isUser=isUser,
                                                    provided_value=coefficient_of_thermal_expansion,
                                                    provided_unit=thermal_coefficient_unit,
                                                    base_value=coefficient_of_thermal_expansion,
                                                ),
                                        }
                                    )
                                ),
                            ),

                        "Design Material Properties":
                            ReinforcementAASHTODesignMaterialParameterGroup(
                                isUser=isUser,
                                group_parameters=(
                                    ReinforcementAASHTODesignMaterialParameters(
                                        **{
                                            "Expected Reinforcement Yield Strength":
                                                ExpectedYieldStrengthReinforcement(
                                                    isUser=isUser,
                                                    provided_value=expected_reinforcement_yield_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=expected_reinforcement_yield_strength,
                                                ),

                                            "Minimum Reinforcement Yield Strength":
                                                SpecifiedMinimumYieldStrengthReinforcement(
                                                    isUser=isUser,
                                                    provided_value=minimum_reinforcement_yield_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=minimum_reinforcement_yield_strength,
                                                ),

                                            "Expected Reinforcement Tensile Strength":
                                                ExpectedTensileStrengthReinforcement(
                                                    isUser=isUser,
                                                    provided_value=expected_reinforcement_tensile_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=expected_reinforcement_tensile_strength,
                                                ),

                                            "Minimum Reinforcement Tensile Strength":
                                                SpecifiedMinimumTensileStrengthReinforcement(
                                                    isUser=isUser,
                                                    provided_value=minimum_reinforcement_tensile_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=minimum_reinforcement_tensile_strength,
                                                ),
                                        }
                                    )
                                ),
                            ),
                    }
                )
            ),
        )


if __name__ == "__main__":

    reinforcement = (
        ReinforcementAASHTOMaterialDataObject.create(
            name="AASHTO Grade 60 Reinforcement",

            application_id="MAT-0001-REBAR-AASHTO",     #if you use something else like "Caru-Canu", the validation will fail

            unit_weight=77.0,

            modulus_of_elasticity=200,
            elasticity_unit="GPa",

            poissons_ratio=0.30,

            coefficient_of_thermal_expansion=1.2e-5,

            expected_reinforcement_yield_strength=480e6,
            minimum_reinforcement_yield_strength=420e6,

            expected_reinforcement_tensile_strength=680e6,
            minimum_reinforcement_tensile_strength=620e6,
        )
    )

    print(
        reinforcement.model_dump_json(
            indent=4,
            by_alias=True,
        )
    )

    import json                             #can be commented out after testing

    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            ReinforcementAASHTOMaterialDataObject.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )