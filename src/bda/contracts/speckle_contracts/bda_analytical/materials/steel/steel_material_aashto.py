from __future__ import annotations

from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes

from operator import index
from typing import Literal, ClassVar

from pydantic import BaseModel, Field, StrictFloat

from bda.contracts.paramodel.materials.materials_para_model import (
    MaterialModelTypeParaModel,
)

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup
)

from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    MaterialDesignCode_AASHTO,
    UnitWeight,
    ModulusOfElasticity,
    PoissonsRatio,
    CoefficientOfThermalExpansion,
    Isotropy,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.steel.steel_material_base import (
    MaterialType_Steel,
    SteelGeneralMaterialParameters,
    SteelGeneralMaterialParameterGroup,
    SteelMaterialDataObject_Properties,
    SteelMaterialDataObject,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.shared.material_strength_parameters import (
    ExpectedTensileStrength,
    ExpectedYieldStrength,
    SpecifiedMinimumTensileStrength,
    SpecifiedMinimumYieldStrength
)

# ==========================================================
# GENERAL MATERIAL PARAMETERS OVERRIDE
# ==========================================================

class SteelAASHTOGeneralMaterialParameters(
    SteelGeneralMaterialParameters
):
    material_design_code: MaterialDesignCode_AASHTO = Field(
        alias="Material Design Code"
    )


class SteelAASHTOGeneralMaterialParameterGroup(
    SteelGeneralMaterialParameterGroup
):
    group_parameters: SteelAASHTOGeneralMaterialParameters

# ----------------------------
# Steel Strength Parameters
# ----------------------------

class SpecifiedMinimumYieldStrengthSteel(SpecifiedMinimumYieldStrength):
    name: Literal["Specified Minimum Steel Yield Strength"] = "Specified Minimum Steel Yield Strength"
    symbol: Literal["fy,min"] = "fy,min"
    description: Literal[
        "Specified Minimum yield strength of steel"
    ] = "Specified Minimum yield strength of steel"


class ExpectedYieldStrengthSteel(ExpectedYieldStrength):
    name: Literal["Expected Steel Yield Strength"] = "Expected Steel Yield Strength"
    symbol: Literal["fy,exp"] = "fy,exp"
    description: Literal[
        "Expected yield strength of steel"
    ] = "Expected yield strength of steel"


class SpecifiedMinimumTensileStrengthSteel(SpecifiedMinimumTensileStrength):
    name: Literal["Specified Minimum Steel Tensile Strength"] = "Specified Minimum Steel Tensile Strength"
    symbol: Literal["fu,min"] = "fu,min"
    description: Literal[
        "Specified minimum tensile strength of steel"
    ] = "Specified minimum tensile strength of steel"


class ExpectedTensileStrengthSteel(ExpectedTensileStrength):
    name: Literal["Expected Steel Tensile Strength"] = "Expected Steel Tensile Strength"
    symbol: Literal["fu,exp"] = "fu,exp"
    description: Literal[
        "Expected tensile strength of steel"
    ] = "Expected tensile strength of steel"

class SteelAASHTODesignMaterialParameters(
    BaseModel
):
    expected_steel_yield_strength: (
        ExpectedYieldStrengthSteel
    ) = Field(
        alias="Expected Steel Yield Strength"
    )

    minimum_steel_yield_strength: (
        SpecifiedMinimumYieldStrengthSteel
    ) = Field(
        alias="Minimum Steel Yield Strength"
    )

    expected_steel_tensile_strength: (
        ExpectedTensileStrengthSteel
    ) = Field(
        alias="Expected Steel Tensile Strength"
    )

    minimum_steel_tensile_strength: (
        SpecifiedMinimumTensileStrengthSteel
    ) = Field(
        alias="Minimum Steel Tensile Strength"
    )

class SteelAASHTODesignMaterialParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Steel Material Properties"
    ] = "Steel Material Properties"

    description: Literal[
        "Steel material properties"
    ] = "Steel material properties"

    group_parameters: (
        SteelAASHTODesignMaterialParameters
    )

class SteelAASHTOMaterialDataObjectProperties(
    SteelMaterialDataObject_Properties
):
    general_material_properties: (
        SteelAASHTOGeneralMaterialParameterGroup
    ) = Field(
        alias="General Material Properties"
    )

    steel_material_properties: (
        SteelAASHTODesignMaterialParameterGroup
    ) = Field(
        alias="Design Material Properties"
    )

class SteelAASHTOMaterialDataObject(
    SteelMaterialDataObject
):

    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^MAT-\d{4}-STEEL-AASHTO$"
    )

    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN
    )

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_STEEL_MATERIAL_AASHTO
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_STEEL_MATERIAL_AASHTO.value, frozen=True)

    properties: (
        SteelAASHTOMaterialDataObjectProperties
    )

    @classmethod
    def create(
        cls,
        name: str,
        unit_weight: float,
        modulus_of_elasticity: float,
        poissons_ratio: float,
        coefficient_of_thermal_expansion: float,
        expected_steel_yield_strength: float,
        minimum_steel_yield_strength: float,
        expected_steel_tensile_strength: float,
        minimum_steel_tensile_strength: float,
        unit_weight_unit: Literal["kN/m³", "kips/ft³"] = "kN/m³",
        strength_unit: Literal["kN/m²", "lbf/ft²"] = "kN/m²",
        elasticity_unit: Literal["Pa", "kPa", "GPa", "kips/in²", "kN/m²"] = "Pa",
        thermal_coefficient_unit: Literal["1/Δ°C", "1/Δ°F"] = "1/Δ°C",
        application_id: str = "steel_aashto_1",
        isUser: bool = True,
    ) -> "SteelAASHTOMaterialDataObject":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            properties=(
                SteelAASHTOMaterialDataObjectProperties(
                    **{
                        "General Material Properties":
                            SteelAASHTOGeneralMaterialParameterGroup(
                                isUser=isUser,
                                group_parameters=(
                                    SteelAASHTOGeneralMaterialParameters(
                                        **{
                                            "Material Type":
                                                MaterialType_Steel(
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
                            SteelAASHTODesignMaterialParameterGroup(
                                isUser=isUser,
                                group_parameters=(
                                    SteelAASHTODesignMaterialParameters(
                                        **{
                                            "Expected Steel Yield Strength":
                                                ExpectedYieldStrengthSteel(
                                                    isUser=isUser,
                                                    provided_value=expected_steel_yield_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=expected_steel_yield_strength,
                                                ),

                                            "Minimum Steel Yield Strength":
                                                SpecifiedMinimumYieldStrengthSteel(
                                                    isUser=isUser,
                                                    provided_value=minimum_steel_yield_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=minimum_steel_yield_strength,
                                                ),

                                            "Expected Steel Tensile Strength":
                                                ExpectedTensileStrengthSteel(
                                                    isUser=isUser,
                                                    provided_value=expected_steel_tensile_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=expected_steel_tensile_strength,
                                                ),

                                            "Minimum Steel Tensile Strength":
                                                SpecifiedMinimumTensileStrengthSteel(
                                                    isUser=isUser,
                                                    provided_value=minimum_steel_tensile_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=minimum_steel_tensile_strength,
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

    steel = SteelAASHTOMaterialDataObject.create(
        name="AASHTO Grade 50",

        application_id="MAT-0001-STEEL-AASHTO", #if you use something else like "Hicor-Dicori-Doc", the validation will fail

        unit_weight=77.0,
        modulus_of_elasticity=200,
        elasticity_unit="GPa",
        poissons_ratio=0.30,
        coefficient_of_thermal_expansion=1.2e-5,

        expected_steel_yield_strength=380e6,
        minimum_steel_yield_strength=345e6,

        expected_steel_tensile_strength=520e6,
        minimum_steel_tensile_strength=450e6,
    )

    print(
        steel.model_dump_json(
            indent=4,
            by_alias=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing

    print(
        json.dumps(
            SteelAASHTOMaterialDataObject.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )