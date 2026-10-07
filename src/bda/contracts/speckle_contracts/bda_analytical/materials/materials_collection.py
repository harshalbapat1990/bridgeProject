import re

from bda.contracts.paramodel.materials import MaterialBaseParaModel
from bda.contracts.speckle_contracts.base_objects import BridgeCollection

from pydantic import Field, field_validator
from typing import ClassVar, Literal

import json

from bda.contracts.speckle_contracts.bda_analytical.materials.concrete.concrete_material_aashto import ConcreteAASHTOMaterialDataObject
from bda.contracts.speckle_contracts.bda_analytical.materials.steel.steel_material_aashto import SteelAASHTOMaterialDataObject
from bda.contracts.speckle_contracts.bda_analytical.materials.reinforcement.reinforcement_material_aashto import ReinforcementAASHTOMaterialDataObject
from bda.contracts.speckle_contracts.bda_analytical.materials.tendon.tendon_material_aashto import TendonAASHTOMaterialDataObject


from typing import Union, Annotated


Material_AASHTO = Annotated[
    Union[
        ConcreteAASHTOMaterialDataObject,
        SteelAASHTOMaterialDataObject,
        ReinforcementAASHTOMaterialDataObject,
        TendonAASHTOMaterialDataObject
    ],
    Field(discriminator="bda_speckle_type"),
]


class MaterialsCollection(BridgeCollection):
    COLLECTION_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^COL-MATERIALS$"
    )
    applicationId: str = Field(
        pattern=r"^COL-MATERIALS$"
    )
    name: Literal["Materials"] = "Materials"

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = Field("Speckle.Core.Models.Collections.Collection", frozen=True)

    elements: list[Material_AASHTO] = Field(
        default_factory=list
    )  # type: ignore[reportIncompatibleVariableOverride]

    @classmethod
    def create(
        cls,
        materials: list[Material_AASHTO] | None = None,
        application_id: str = "COL-MATERIALS",
    ) -> "MaterialsCollection":
        return cls(
            applicationId=application_id,
            elements=materials or [],
        )

    @field_validator("applicationId")
    @classmethod
    def validate_application_id(
        cls,
        value: str,
    ):

        if not cls.COLLECTION_ID_PATTERN.match(value):
            raise ValueError(
                "Materials collection applicationId must be COL-MATERIALS"
            )

        return value

if __name__ == "__main__":
    # Example usage
    # print("\n=== General Material Dataobject json schema ===")
    material_collection_schema = MaterialsCollection.model_json_schema()
    # print(json.dumps(material_collection_schema, indent=2))
    with open("material_collection_schema.txt", "w", encoding="utf-8") as f:
        json.dump(material_collection_schema, f, indent=2, ensure_ascii=False)

    concrete = ConcreteAASHTOMaterialDataObject.create(
        name="AASHTO Concrete C50",
        application_id="MAT-0001-CONC-AASHTO",

        unit_weight=24.0,
        modulus_of_elasticity=35,
        elasticity_unit="GPa",
        poissons_ratio=0.20,
        coefficient_of_thermal_expansion=1.0e-5,

        expected_concrete_strength=55e6,
        specified_concrete_strength=50e6,
    )

    steel = SteelAASHTOMaterialDataObject.create(
        name="AASHTO Grade 50 Steel",
        application_id="MAT-0002-STEEL-AASHTO",

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

    reinforcement = ReinforcementAASHTOMaterialDataObject.create(
        name="AASHTO Grade 60 Reinforcement",
        application_id="MAT-0003-REBAR-AASHTO",

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

    tendon = TendonAASHTOMaterialDataObject.create(
        name="AASHTO 1860 MPa Strand",
        application_id="MAT-0004-TENDON-AASHTO",

        unit_weight=77.0,
        modulus_of_elasticity=195,
        elasticity_unit="GPa",
        poissons_ratio=0.30,
        coefficient_of_thermal_expansion=1.2e-5,

        tendon_yield_strength=1670e6,
        tendon_specified_minimum_tensile_strength=1860e6,
    )

    materials = MaterialsCollection.create(
        [
            concrete,
            steel,
            reinforcement,
            tendon,
        ],
        application_id="COL-MATERIALS",
    )

    print(
        materials.model_dump_json(
            indent=4,
            by_alias=True,
        )
    )