
"""
One-time utility used to generate golden fixture files for

material contract validation tests.

Not executed by pytest.

"""

import json
from pathlib import Path

from bda.contracts.speckle_contracts.bda_analytical.materials.concrete.concrete_material_aashto import (
    ConcreteAASHTOMaterialDataObject,
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
import json
from pathlib import Path

# imports here...

fixture_dir = Path("tests/unit/fixtures/speckle")
fixture_dir.mkdir(parents=True, exist_ok=True)

# Concrete
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

with open(
    fixture_dir / "concrete_material_aashto.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(concrete.model_dump(by_alias=True), f, indent=4)

# Steel
steel = SteelAASHTOMaterialDataObject.create(
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

with open(
    fixture_dir / "steel_material_aashto.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(steel.model_dump(by_alias=True), f, indent=4)

# Reinforcement
reinforcement = ReinforcementAASHTOMaterialDataObject.create(
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

with open(
    fixture_dir / "reinforcement_material_aashto.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(reinforcement.model_dump(by_alias=True), f, indent=4)

# Tendon
tendon = TendonAASHTOMaterialDataObject.create(
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

with open(
    fixture_dir / "tendon_material_aashto.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(tendon.model_dump(by_alias=True), f, indent=4)