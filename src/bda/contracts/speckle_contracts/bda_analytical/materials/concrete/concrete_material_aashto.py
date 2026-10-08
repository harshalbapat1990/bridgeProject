from __future__ import annotations

from typing import Literal, ClassVar
from pydantic import Field, StrictFloat, BaseModel

from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    MaterialDesignCode_AASHTO,
    UnitWeight,
    ModulusOfElasticity,
    PoissonsRatio,
    CoefficientOfThermalExpansion,
    Isotropy,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.concrete.concrete_material_base import (
    ConcreteGeneralMaterialParameters,
    ConcreteGeneralMaterialParameterGroup,
    ConcreteMaterialDataObject_Properties,
    ConcreteMaterialDataObject,
    MaterialType_Concrete
)

from bda.contracts.paramodel.materials.materials_para_model import (
    MaterialModelTypeParaModel
)

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup,
)
from bda.contracts.speckle_contracts.unit_parameters import StrictPressureParameter

# ==========================================================
# GENERAL MATERIAL PARAMETERS OVERRIDE
# ==========================================================

class ConcreteAASHTOGeneralMaterialParameters(
    ConcreteGeneralMaterialParameters
):
    material_design_code: MaterialDesignCode_AASHTO = Field(
        alias="Material Design Code"
    )


class ConcreteAASHTOGeneralMaterialParameterGroup(
    ConcreteGeneralMaterialParameterGroup
):
    group_parameters: ConcreteAASHTOGeneralMaterialParameters


# ==========================================================
# DESIGN MATERIAL PARAMETERS
# ==========================================================

class SpecifiedMinimumCompressiveStrength(StrictPressureParameter):
    name: Literal[
        "Specified Minimum Compressive Strength"
    ] = "Specified Minimum Compressive Strength"

    symbol: Literal["fc,min"] = "fc,min"

    description: Literal[
        "Specified minimum compressive strength of concrete"
    ] = "Specified minimum compressive strength of concrete"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "kips/in²"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool


class ExpectedCompressiveStrength(StrictPressureParameter):
    name: Literal[
        "Expected Compressive Strength"
    ] = "Expected Compressive Strength"

    symbol: Literal["fc,exp"] = "fc,exp"

    description: Literal[
        "Expected compressive strength of concrete at 28 days"
    ] = "Expected compressive strength of concrete at 28 days"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "kips/in²"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool


class ConcreteAASHTODesignMaterialParameters(BaseModel):
    expected_concrete_strength: ExpectedCompressiveStrength = Field(
        alias="Expected Concrete Strength"
    )

    specified_concrete_strength: (
        SpecifiedMinimumCompressiveStrength
    ) = Field(
        alias="Specified Concrete Strength"
    )


# ==========================================================
# DESIGN MATERIAL PARAMETER GROUP
# ==========================================================

class ConcreteAASHTODesignMaterialParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Concrete Material Properties"
    ] = "Concrete Material Properties"

    description: Literal[
        "Concrete material properties"
    ] = "Concrete material properties"

    group_parameters: ConcreteAASHTODesignMaterialParameters


# ==========================================================
# DATA OBJECT PROPERTIES
# ==========================================================

class ConcreteAASHTOMaterialDataObjectProperties(
    ConcreteMaterialDataObject_Properties
):
    general_material_properties: (
        ConcreteAASHTOGeneralMaterialParameterGroup
    ) = Field(
        alias="General Material Properties"
    )

    concrete_material_properties: (
        ConcreteAASHTODesignMaterialParameterGroup
    ) = Field(
        alias="Design Material Properties"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class ConcreteAASHTOMaterialDataObject(
    ConcreteMaterialDataObject
):

    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^MAT-\d{4}-CONC-AASHTO$"
    )

    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN
    )

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Concrete_Material_AASHTO"
    ] = (
        "Objects.Data.DataObject:"
        "BDA_Concrete_Material_AASHTO"
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Concrete_Material_AASHTO"
    ] = Field(
        ...,
        frozen=True
    )

    properties: (
        ConcreteAASHTOMaterialDataObjectProperties
    )

    @classmethod
    def create(
        cls,
        name: str,
        unit_weight: float,
        modulus_of_elasticity: float,
        poissons_ratio: float,
        coefficient_of_thermal_expansion: float,
        expected_concrete_strength: float,
        specified_concrete_strength: float,
        unit_weight_unit: Literal["kN/m³", "kips/ft³"] = "kN/m³",
        concrete_strength_unit: Literal["kN/m²", "kips/in²"]="kN/m²",
        elasticity_unit: Literal["kN/m²", "kips/in²","GPa"]="kN/m²",
        thermal_coefficient_unit:Literal["1/Δ°C", "1/Δ°F"]="1/Δ°C",
        application_id: str = "concrete_aashto_1",
        isUser: bool = True,
    ) -> "ConcreteAASHTOMaterialDataObject":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Concrete_Material_AASHTO"
            ),
            bda_speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Concrete_Material_AASHTO"
            ),
            properties=(
                ConcreteAASHTOMaterialDataObjectProperties(
                    **{
                        "General Material Properties":
                            ConcreteAASHTOGeneralMaterialParameterGroup(
                                isUser=isUser,
                                group_parameters=(
                                    ConcreteAASHTOGeneralMaterialParameters(
                                        **{
                                            "Material Type":
                                                MaterialType_Concrete(
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
                            ConcreteAASHTODesignMaterialParameterGroup(
                                isUser=isUser,
                                group_parameters=(
                                    ConcreteAASHTODesignMaterialParameters(
                                        **{
                                            "Expected Concrete Strength":
                                                ExpectedCompressiveStrength(
                                                    isUser=isUser,
                                                    provided_value=expected_concrete_strength,
                                                    provided_unit=concrete_strength_unit,
                                                    base_value=expected_concrete_strength,
                                                ),

                                            "Specified Concrete Strength":
                                                SpecifiedMinimumCompressiveStrength(
                                                    isUser=isUser,
                                                    provided_value=specified_concrete_strength,
                                                    provided_unit=concrete_strength_unit,
                                                    base_value=specified_concrete_strength,
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

    concrete = ConcreteAASHTOMaterialDataObject.create(
        name="AASHTO Concrete C50",
        application_id="MAT-0001-CONC-AASHTO", #if you use something else like "Humpty-Dumpty", the validation will fail
        unit_weight=24.0,
        modulus_of_elasticity=3.5e10,
        poissons_ratio=0.20,
        coefficient_of_thermal_expansion=1.0e-5,
        expected_concrete_strength=55e6,
        specified_concrete_strength=50e6,
    )

    print(
        concrete.model_dump_json(
            indent=4
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing

    print(
        json.dumps(
            ConcreteAASHTOMaterialDataObject.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )