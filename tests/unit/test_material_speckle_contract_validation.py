import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from bda.contracts.speckle_contracts.bda_analytical.materials.concrete.concrete_material_aashto import (
    ConcreteAASHTOMaterialDataObject,
)

from bda.contracts.paramodel.materials.materials_para_model import (
    MaterialParaModel,
    MaterialTypeParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.steel.steel_material_aashto import (
    SteelAASHTOMaterialDataObject,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.reinforcement.reinforcement_material_aashto import (
    ReinforcementAASHTOMaterialDataObject,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.tendon.tendon_material_aashto import (
    TendonAASHTOMaterialDataObject,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.materials_collection import (
    MaterialsCollection,
)

# Resolve fixtures relative to THIS test file so tests work regardless of the
# current working directory pytest is launched from.
FIXTURES_SPECKLE_DIR = Path(__file__).parent / "fixtures" / "speckle"

#Mixed Materials Collection tests
def test_concrete_contract_create():

    material = ConcreteAASHTOMaterialDataObject.create(
        name="Concrete",
        application_id="MAT-0001-CONC-AASHTO",
        unit_weight=24.0,
        modulus_of_elasticity=35,
        elasticity_unit="GPa",
        poissons_ratio=0.2,
        coefficient_of_thermal_expansion=1e-5,
        expected_concrete_strength=55e6,
        specified_concrete_strength=50e6,
    )

    assert material.applicationId == "MAT-0001-CONC-AASHTO"


def test_steel_contract_create():

    material = SteelAASHTOMaterialDataObject.create(
        name="Steel",
        application_id="MAT-0001-STEEL-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=200,
        elasticity_unit="GPa",
        poissons_ratio=0.3,
        coefficient_of_thermal_expansion=1.2e-5,
        expected_steel_yield_strength=380e6,
        minimum_steel_yield_strength=345e6,
        expected_steel_tensile_strength=520e6,
        minimum_steel_tensile_strength=450e6,
    )

    assert material.applicationId == "MAT-0001-STEEL-AASHTO"


def test_reinforcement_contract_create():

    material = ReinforcementAASHTOMaterialDataObject.create(
        name="Rebar",
        application_id="MAT-0001-REBAR-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=200,
        elasticity_unit="GPa",
        poissons_ratio=0.3,
        coefficient_of_thermal_expansion=1.2e-5,
        expected_reinforcement_yield_strength=480e6,
        minimum_reinforcement_yield_strength=420e6,
        expected_reinforcement_tensile_strength=680e6,
        minimum_reinforcement_tensile_strength=620e6,
    )

    assert material.applicationId == "MAT-0001-REBAR-AASHTO"


def test_tendon_contract_create():

    material = TendonAASHTOMaterialDataObject.create(
        name="Tendon",
        application_id="MAT-0001-TENDON-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=195,
        elasticity_unit="GPa",
        poissons_ratio=0.3,
        coefficient_of_thermal_expansion=1.2e-5,
        tendon_yield_strength=1670e6,
        tendon_specified_minimum_tensile_strength=1860e6,
    )

    assert material.applicationId == "MAT-0001-TENDON-AASHTO"


def test_invalid_application_id():

    with pytest.raises(ValidationError):

        ConcreteAASHTOMaterialDataObject.create(
            name="Bad",
            application_id="Humpty-Dumpty",
            unit_weight=24.0,
            modulus_of_elasticity=35,
            elasticity_unit="GPa",
            poissons_ratio=0.2,
            coefficient_of_thermal_expansion=1e-5,
            expected_concrete_strength=55e6,
            specified_concrete_strength=50e6,
        )


def test_concrete_round_trip():

    material = ConcreteAASHTOMaterialDataObject.create(
        name="Concrete",
        application_id="MAT-0001-CONC-AASHTO",
        unit_weight=24.0,
        modulus_of_elasticity=35,
        elasticity_unit="GPa",
        poissons_ratio=0.2,
        coefficient_of_thermal_expansion=1e-5,
        expected_concrete_strength=55e6,
        specified_concrete_strength=50e6,
    )

    payload = material.model_dump(by_alias=True)

    restored = ConcreteAASHTOMaterialDataObject.model_validate(payload)

    assert restored.applicationId == material.applicationId


def test_materials_collection_validation():

    concrete = ConcreteAASHTOMaterialDataObject.create(
        name="Concrete",
        application_id="MAT-0001-CONC-AASHTO",
        unit_weight=24.0,
        modulus_of_elasticity=35,
        elasticity_unit="GPa",
        poissons_ratio=0.2,
        coefficient_of_thermal_expansion=1e-5,
        expected_concrete_strength=55e6,
        specified_concrete_strength=50e6,
    )

    collection = MaterialsCollection.create(
        [concrete],
        application_id="COL-MATERIALS",
    )

    assert len(collection.elements) == 1


def test_invalid_collection_id():

    with pytest.raises(ValidationError):
        MaterialsCollection.create(
            [],
            application_id="BAD-COLLECTION",
        )


def test_invalid_unit_rejected():

    with pytest.raises(ValidationError):
        ConcreteAASHTOMaterialDataObject.create(
            name="Concrete",
            application_id="MAT-0001-CONC-AASHTO",
            unit_weight=24.0,
            unit_weight_unit="banana",
            modulus_of_elasticity=35,
            elasticity_unit="GPa",
            poissons_ratio=0.20,
            coefficient_of_thermal_expansion=1e-5,
            expected_concrete_strength=55e6,
            specified_concrete_strength=50e6,
        )

def test_materials_collection_with_all_material_types():

    concrete = ConcreteAASHTOMaterialDataObject.create(
        name="Concrete",
        application_id="MAT-0001-CONC-AASHTO",
        unit_weight=24.0,
        modulus_of_elasticity=35,
        elasticity_unit="GPa",
        poissons_ratio=0.20,
        coefficient_of_thermal_expansion=1e-5,
        expected_concrete_strength=55e6,
        specified_concrete_strength=50e6,
    )

    steel = SteelAASHTOMaterialDataObject.create(
        name="Steel",
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
        name="Rebar",
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
        name="Tendon",
        application_id="MAT-0004-TENDON-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=195,
        elasticity_unit="GPa",
        poissons_ratio=0.30,
        coefficient_of_thermal_expansion=1.2e-5,
        tendon_yield_strength=1670e6,
        tendon_specified_minimum_tensile_strength=1860e6,
    )

    collection = MaterialsCollection.create(
        [concrete, steel, reinforcement, tendon],
        application_id="COL-MATERIALS",
    )

    assert len(collection.elements) == 4

#Unknown Discrimnitator tests
def test_unknown_material_discriminator():

    payload = {
        "applicationId": "COL-MATERIALS",
        "elements": [
            {
                "speckle_type": "Objects.Data.DataObject:UNKNOWN",
                "applicationId": "MAT-9999-UNKNOWN",
                "name": "Unknown"
            }
        ]
    }

    with pytest.raises(ValidationError):
        MaterialsCollection.model_validate(payload)

#Negative Unitweight validation tests

def test_negative_unit_weight_rejected():

    with pytest.raises(ValidationError):

        ConcreteAASHTOMaterialDataObject.create(
            name="Concrete",
            application_id="MAT-0001-CONC-AASHTO",
            unit_weight=-1,
            modulus_of_elasticity=35,
            elasticity_unit="GPa",
            poissons_ratio=0.20,
            coefficient_of_thermal_expansion=1e-5,
            expected_concrete_strength=55e6,
            specified_concrete_strength=50e6,
        )

#Negative poison ratio Validaiton
def test_negative_poissons_ratio_rejected():

    with pytest.raises(ValidationError):

        ConcreteAASHTOMaterialDataObject.create(
            name="Concrete",
            application_id="MAT-0001-CONC-AASHTO",
            unit_weight=24,
            modulus_of_elasticity=35,
            elasticity_unit="GPa",
            poissons_ratio=-0.1,
            coefficient_of_thermal_expansion=1e-5,
            expected_concrete_strength=55e6,
            specified_concrete_strength=50e6,
        )

#Strict Float/ String Rejection
def test_string_unit_weight_rejected():

    with pytest.raises(ValidationError):

        ConcreteAASHTOMaterialDataObject.create(
            name="Concrete",
            application_id="MAT-0001-CONC-AASHTO",
            unit_weight="24",
            modulus_of_elasticity=35,
            elasticity_unit="GPa",
            poissons_ratio=0.20,
            coefficient_of_thermal_expansion=1e-5,
            expected_concrete_strength=55e6,
            specified_concrete_strength=50e6,
        )

def test_steel_round_trip():

    material = SteelAASHTOMaterialDataObject.create(
        name="Steel",
        application_id="MAT-0001-STEEL-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=200,
        elasticity_unit="GPa",
        poissons_ratio=0.3,
        coefficient_of_thermal_expansion=1.2e-5,
        expected_steel_yield_strength=380e6,
        minimum_steel_yield_strength=345e6,
        expected_steel_tensile_strength=520e6,
        minimum_steel_tensile_strength=450e6,
    )

    payload = material.model_dump(by_alias=True)

    restored = SteelAASHTOMaterialDataObject.model_validate(payload)

    assert restored.applicationId == material.applicationId
    assert restored.name == material.name

def test_reinforcement_round_trip():

    material = ReinforcementAASHTOMaterialDataObject.create(
        name="Rebar",
        application_id="MAT-0001-REBAR-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=200,
        elasticity_unit="GPa",
        poissons_ratio=0.3,
        coefficient_of_thermal_expansion=1.2e-5,
        expected_reinforcement_yield_strength=480e6,
        minimum_reinforcement_yield_strength=420e6,
        expected_reinforcement_tensile_strength=680e6,
        minimum_reinforcement_tensile_strength=620e6,
    )

    payload = material.model_dump(by_alias=True)

    restored = ReinforcementAASHTOMaterialDataObject.model_validate(payload)

    assert restored.applicationId == material.applicationId
    assert restored.name == material.name

def test_tendon_round_trip():

    material = TendonAASHTOMaterialDataObject.create(
        name="Tendon",
        application_id="MAT-0001-TENDON-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=195,
        elasticity_unit="GPa",
        poissons_ratio=0.3,
        coefficient_of_thermal_expansion=1.2e-5,
        tendon_yield_strength=1670e6,
        tendon_specified_minimum_tensile_strength=1860e6,
    )

    payload = material.model_dump(by_alias=True)

    restored = TendonAASHTOMaterialDataObject.model_validate(payload)

    assert restored.applicationId == material.applicationId
    assert restored.name == material.name


def test_concrete_fixture_contract():

    fixture = FIXTURES_SPECKLE_DIR / "concrete_material_aashto.json"

    with open(fixture, encoding="utf-8") as f:
        payload = json.load(f)

    material = ConcreteAASHTOMaterialDataObject.model_validate(payload)

    assert material.applicationId == "MAT-0001-CONC-AASHTO"

def test_steel_fixture_contract():

    fixture = FIXTURES_SPECKLE_DIR / "steel_material_aashto.json"

    with open(fixture, encoding="utf-8") as f:
        payload = json.load(f)

    material = SteelAASHTOMaterialDataObject.model_validate(payload)

    assert material.applicationId == "MAT-0001-STEEL-AASHTO"

def test_reinforcement_fixture_contract():

    fixture = FIXTURES_SPECKLE_DIR / "reinforcement_material_aashto.json"

    with open(fixture, encoding="utf-8") as f:
        payload = json.load(f)

    material = ReinforcementAASHTOMaterialDataObject.model_validate(payload)

    assert material.applicationId == "MAT-0001-REBAR-AASHTO"

def test_tendon_fixture_contract():

    fixture = FIXTURES_SPECKLE_DIR / "tendon_material_aashto.json"

    with open(fixture, encoding="utf-8") as f:
        payload = json.load(f)

    material = TendonAASHTOMaterialDataObject.model_validate(payload)

    assert material.applicationId == "MAT-0001-TENDON-AASHTO"

def test_concrete_contract_maps_to_paramodel():
    material = ConcreteAASHTOMaterialDataObject.create(
        name="Concrete",
        application_id="MAT-0001-CONC-AASHTO",
        unit_weight=24.0,
        modulus_of_elasticity=35,
        elasticity_unit="GPa",
        poissons_ratio=0.2,
        coefficient_of_thermal_expansion=1e-5,
        expected_concrete_strength=55e6,
        specified_concrete_strength=50e6,
    )

    paramodel = MaterialParaModel.model_validate(
        material.model_dump(mode="json", by_alias=True)
    )

    assert paramodel.name == "Concrete"
    assert paramodel.material_type == MaterialTypeParaModel.CONCRETE


def test_steel_contract_maps_to_paramodel():
    material = SteelAASHTOMaterialDataObject.create(
        name="Steel",
        application_id="MAT-0001-STEEL-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=200,
        elasticity_unit="GPa",
        poissons_ratio=0.3,
        coefficient_of_thermal_expansion=1.2e-5,
        expected_steel_yield_strength=380e6,
        minimum_steel_yield_strength=345e6,
        expected_steel_tensile_strength=520e6,
        minimum_steel_tensile_strength=450e6,
    )

    paramodel = MaterialParaModel.model_validate(
        material.model_dump(mode="json", by_alias=True)
    )

    assert paramodel.name == "Steel"
    assert paramodel.material_type == MaterialTypeParaModel.STEEL


def test_reinforcement_contract_maps_to_paramodel():
    material = ReinforcementAASHTOMaterialDataObject.create(
        name="Rebar",
        application_id="MAT-0001-REBAR-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=200,
        elasticity_unit="GPa",
        poissons_ratio=0.3,
        coefficient_of_thermal_expansion=1.2e-5,
        expected_reinforcement_yield_strength=480e6,
        minimum_reinforcement_yield_strength=420e6,
        expected_reinforcement_tensile_strength=680e6,
        minimum_reinforcement_tensile_strength=620e6,
    )

    paramodel = MaterialParaModel.model_validate(
        material.model_dump(mode="json", by_alias=True)
    )

    assert paramodel.name == "Rebar"
    assert (
        paramodel.material_type
        == MaterialTypeParaModel.REINFORCEMENT
    )


def test_tendon_contract_maps_to_paramodel():
    material = TendonAASHTOMaterialDataObject.create(
        name="Tendon",
        application_id="MAT-0001-TENDON-AASHTO",
        unit_weight=77.0,
        modulus_of_elasticity=195,
        elasticity_unit="GPa",
        poissons_ratio=0.3,
        coefficient_of_thermal_expansion=1.2e-5,
        tendon_yield_strength=1670e6,
        tendon_specified_minimum_tensile_strength=1860e6,
    )

    paramodel = MaterialParaModel.model_validate(
        material.model_dump(mode="json", by_alias=True)
    )

    assert paramodel.name == "Tendon"
    assert paramodel.material_type == MaterialTypeParaModel.TENDON