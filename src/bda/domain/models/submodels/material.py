from abc import ABC
from dataclasses import dataclass, field
from itertools import count
from uuid import UUID, uuid4
from typing import Optional

from bda.domain.base.multi_model_object import MultiModelObjectBase
from bda.domain.enums import MaterialModelType, MaterialType
from bda.domain.units.quantities import *

_material_id_counter = count(1)

def next_material_id() -> int:
    return next(_material_id_counter)

@dataclass(kw_only=True)
class MaterialBase(MultiModelObjectBase, ABC):
    guid: UUID = field(default_factory=uuid4)
    source_id: str | None = None
    model_id: int = field(default_factory=next_material_id, init=False, doc="Identifier of the material, "
                                                        "used exclusively for export to analytical software.")
    name: str
    material_type: MaterialType
    material_model_type: MaterialModelType
    general_properties: GeneralMaterialPropertiesBase
    design_properties: Optional[DesignPropertiesBase]

    def set_id(self, material_id: int):
        """
        Set the material model identifier.

        The identifier is used exclusively when exporting data to analytical
        software.

        Parameters
        ----------
        material_id : int
            Model identifier to assign to the material.

        Returns
        -------
        None
        """
        self.model_id = material_id

    def __deepcopy__(self, memo):
        from copy import deepcopy

        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        for k, v in self.__dict__.items():
            if k == "guid":
                setattr(result, k, uuid4())
            elif k == "model_id":
                setattr(result, k, next_material_id())
            else:
                setattr(result, k, deepcopy(v, memo))
        return result


Material = MaterialBase


@dataclass
class MaterialConcrete(MaterialBase):
    material_model_type: MaterialModelType = field(default=MaterialModelType.ISOTROPIC, init=False)
    material_type: MaterialType = field(default=MaterialType.CONCRETE, init=False)
    general_properties: GeneralMaterialIsotropicProperties
    design_properties: DesignPropertiesConcrete


@dataclass
class MaterialSteel(MaterialBase):
    material_model_type: MaterialModelType = field(default=MaterialModelType.ISOTROPIC, init=False)
    material_type: MaterialType = field(default=MaterialType.STEEL, init=False)
    general_properties: GeneralMaterialIsotropicProperties
    design_properties: DesignPropertiesSteel


@dataclass
class MaterialReinforcement(MaterialBase):
    material_model_type: MaterialModelType = field(default=MaterialModelType.ISOTROPIC, init=False)
    material_type: MaterialType = field(default=MaterialType.REINFORCEMENT, init=False)
    general_properties: GeneralMaterialIsotropicProperties
    design_properties: DesignPropertiesReinforcement


@dataclass
class MaterialTendon(MaterialBase):
    material_model_type: MaterialModelType = field(default=MaterialModelType.ISOTROPIC, init=False)
    material_type: MaterialType = field(default=MaterialType.TENDON, init=False)
    general_properties: GeneralMaterialIsotropicProperties
    design_properties: DesignPropertiesTendon


@dataclass
class GeneralMaterialPropertiesBase(ABC):
    unit_weight: WeightDensity


@dataclass
class GeneralMaterialIsotropicProperties(GeneralMaterialPropertiesBase):
    modulus_of_elasticity: Pressure
    thermal_coefficient: TemperatureCoefficient
    poissons_ratio: float


@dataclass
class GeneralMaterialOrthotropicProperties(GeneralMaterialPropertiesBase):
    modulus_of_elasticity: tuple = None
    thermal_coefficient: tuple = None
    poissons_ratio: tuple = None

    def __post_init__(self):
        raise NotImplementedError("Orthotropic Material Properties is not yet implemented.")


@dataclass
class DesignPropertiesBase(ABC):
    pass


@dataclass
class DesignPropertiesConcrete(DesignPropertiesBase):
    characteristic_compressive_strength_fck: Pressure
    mean_compressive_strength_fcm: Pressure


@dataclass
class DesignPropertiesGeneralSteelBase(DesignPropertiesBase, ABC):
    characteristic_yield_strength_fyk: Pressure
    characteristic_ultimate_tensile_strength_fuk: Pressure


@dataclass
class DesignPropertiesSteel(DesignPropertiesGeneralSteelBase):
    mean_yield_strength_fym: Pressure
    mean_ultimate_tensile_strength_fum: Pressure


@dataclass
class DesignPropertiesReinforcement(DesignPropertiesGeneralSteelBase):
    mean_yield_strength_fym: Pressure
    mean_ultimate_tensile_strength_fum: Pressure


@dataclass
class DesignPropertiesTendon(DesignPropertiesGeneralSteelBase):
    pass

