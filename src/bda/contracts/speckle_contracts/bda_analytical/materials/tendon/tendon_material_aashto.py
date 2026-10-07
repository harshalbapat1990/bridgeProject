from __future__ import annotations

from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes

from typing import Literal, ClassVar

from pydantic import BaseModel, Field, StrictFloat

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

from bda.contracts.speckle_contracts.bda_analytical.materials.tendon.tendon_material_base import (
    MaterialType_Tendon,
    TendonGeneralMaterialParameters,
    TendonGeneralMaterialParameterGroup,
    TendonMaterialDataObject_Properties,
    TendonMaterialDataObject,
)
from bda.contracts.speckle_contracts.unit_parameters import StrictPressureParameter


# ==========================================================
# GENERAL MATERIAL PARAMETERS OVERRIDE
# ==========================================================

class TendonAASHTOGeneralMaterialParameters(
    TendonGeneralMaterialParameters
):
    material_design_code: MaterialDesignCode_AASHTO = Field(
        alias="Material Design Code"
    )


class TendonAASHTOGeneralMaterialParameterGroup(
    TendonGeneralMaterialParameterGroup
):
    group_parameters: (
        TendonAASHTOGeneralMaterialParameters
    )


# ==========================================================
# TENDON STRENGTH PARAMETERS
# ==========================================================

class TendonYieldStrength(StrictPressureParameter):
    name: Literal[
        "Prestressing/Post-Tensioning Steel Yield Strength"
    ] = (
        "Prestressing/Post-Tensioning Steel Yield Strength"
    )

    symbol: Literal["fy,min"] = "fy,min"

    description: Literal[
        "Yield strength of prestressing or post-tensioning steel"
    ] = (
        "Yield strength of prestressing or post-tensioning steel"
    )

    provided_value: StrictFloat

    provided_unit: Literal[
        "kN/m²",
        "kips/in²",
    ]

    base_unit: Literal["Pa"] = "Pa"

    base_value: StrictFloat

    isUser: bool


class TendonSpecifiedMinimumTensileStrength(StrictPressureParameter):
    name: Literal[
        "Prestressing/Post-Tensioning Steel Specified Minimum Tensile Strength"
    ] = (
        "Prestressing/Post-Tensioning Steel Specified Minimum Tensile Strength"
    )

    symbol: Literal["fu,min"] = "fu,min"

    description: Literal[
        "Minimum tensile strength of tendon"
    ] = (
        "Minimum tensile strength of tendon"
    )

    provided_value: StrictFloat

    provided_unit: Literal[
        "kN/m²",
        "kips/in²",
    ]

    base_unit: Literal["Pa"] = "Pa"

    base_value: StrictFloat

    isUser: bool


# ==========================================================
# DESIGN MATERIAL PARAMETERS
# ==========================================================

class TendonAASHTODesignMaterialParameters(
    BaseModel
):
    tendon_yield_strength: (
        TendonYieldStrength
    ) = Field(
        alias="Tendon Yield Strength"
    )

    tendon_specified_minimum_tensile_strength: (
        TendonSpecifiedMinimumTensileStrength
    ) = Field(
        alias="Tendon Specified Minimum Tensile Strength"
    )


# ==========================================================
# DESIGN MATERIAL PARAMETER GROUP
# ==========================================================

class TendonAASHTODesignMaterialParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Tendon Material Properties"
    ] = "Tendon Material Properties"

    description: Literal[
        "Tendon material properties"
    ] = "Tendon material properties"

    group_parameters: (
        TendonAASHTODesignMaterialParameters
    )


# ==========================================================
# DATA OBJECT PROPERTIES
# ==========================================================

class TendonAASHTOMaterialDataObjectProperties(
    TendonMaterialDataObject_Properties
):
    general_material_properties: (
        TendonAASHTOGeneralMaterialParameterGroup
    ) = Field(
        alias="General Material Properties"
    )

    tendon_material_properties: (
        TendonAASHTODesignMaterialParameterGroup
    ) = Field(
        alias="Design Material Properties"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class TendonAASHTOMaterialDataObject(
    TendonMaterialDataObject
):
    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^MAT-\d{4}-TENDON-AASHTO$"
    )

    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN
    )

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_TENDON_MATERIAL_AASHTO
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_TENDON_MATERIAL_AASHTO.value, frozen=True)

    properties: (
        TendonAASHTOMaterialDataObjectProperties
    )

    @classmethod
    def create(
        cls,
        name: str,
        unit_weight: float,
        modulus_of_elasticity: float,
        poissons_ratio: float,
        coefficient_of_thermal_expansion: float,
        tendon_yield_strength: float,
        tendon_specified_minimum_tensile_strength: float,
        unit_weight_unit: Literal["kN/m³", "kips/ft³"] = "kN/m³",
        strength_unit: Literal["kN/m²", "kips/in²"] = "kN/m²",
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
        application_id: str = "tendon_aashto_1",
        isUser: bool = True,
    ) -> "TendonAASHTOMaterialDataObject":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            properties=(
                TendonAASHTOMaterialDataObjectProperties(
                    **{
                        "General Material Properties":
                            TendonAASHTOGeneralMaterialParameterGroup(
                                isUser=isUser,
                                group_parameters=(
                                    TendonAASHTOGeneralMaterialParameters(
                                        **{
                                            "Material Type":
                                                MaterialType_Tendon(
                                                    isUser=False,
                                                ),

                                            "Material Design Code":
                                                MaterialDesignCode_AASHTO(
                                                    isUser=False,
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
                            TendonAASHTODesignMaterialParameterGroup(
                                isUser=isUser,
                                group_parameters=(
                                    TendonAASHTODesignMaterialParameters(
                                        **{
                                            "Tendon Yield Strength":
                                                TendonYieldStrength(
                                                    isUser=isUser,
                                                    provided_value=tendon_yield_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=tendon_yield_strength,
                                                ),

                                            "Tendon Specified Minimum Tensile Strength":
                                                TendonSpecifiedMinimumTensileStrength(
                                                    isUser=isUser,
                                                    provided_value=tendon_specified_minimum_tensile_strength,
                                                    provided_unit=strength_unit,
                                                    base_value=tendon_specified_minimum_tensile_strength,
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

    tendon = (
        TendonAASHTOMaterialDataObject.create(
            name="AASHTO 1860 MPa Strand",

            application_id="MAT-0001-TENDON-AASHTO", #if you use something else like "Bore-Da", the validation will fail

            unit_weight=77.0,

            modulus_of_elasticity=195,
            elasticity_unit="GPa",

            poissons_ratio=0.30,

            coefficient_of_thermal_expansion=1.2e-5,

            tendon_yield_strength=1670e6,

            tendon_specified_minimum_tensile_strength=1860e6,
        )
    )

    print(
        tendon.model_dump_json(
            indent=4,
            by_alias=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            TendonAASHTOMaterialDataObject.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )