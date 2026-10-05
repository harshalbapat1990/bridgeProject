import re

from bda.domain.enums import MaterialType
from bda.domain.models.submodels import MaterialBase, MaterialConcrete, MaterialSteel, MaterialReinforcement, \
    MaterialTendon
from bda.domain.models.submodels.material import GeneralMaterialIsotropicProperties
from bda.domain.units.export_units import ExportUnits, to_float


class MidasMaterialExporter:

    def __init__(self, eu: ExportUnits):
        self._eu = eu
        from midas_civil import Material
        self.MidasMaterial = Material


    def _get_registry(self) -> dict:
        return {
            MaterialType.STEEL: self._export_steel,
            MaterialType.TENDON: self._export_steel,
            MaterialType.REINFORCEMENT: self._export_steel,
            MaterialType.CONCRETE: self._export_concrete,
            None: self._export_user_defined,
        }


    def export_material(self, material: MaterialBase) -> None:
        material.name = self._normalize_name(material.name)
        export_func = self._get_registry().get(material.material_type)
        if export_func is None:
            raise ValueError(f"Unsupported material type: {material.material_type} "
                             f"for material '{material.name}'")
        export_func(material)


    def _export_steel(self, material: MaterialBase) -> None:
        eu = self._eu
        if isinstance(material, MaterialSteel) or \
            isinstance(material, MaterialReinforcement) or \
            isinstance(material, MaterialTendon):
            prop: GeneralMaterialIsotropicProperties = material.general_properties
            self.MidasMaterial.STEEL.User(
                name=material.name,
                E=to_float(prop.modulus_of_elasticity, eu.pressure),
                mass=to_float(prop.unit_weight, eu.weight_density),
                pois=prop.poissons_ratio,
                therm=to_float(prop.thermal_coefficient, eu.temperature_coef),
                id=material.model_id,
            )
        else:
            raise ValueError(f"Unsupported material object: {type(material)} for material '{material.name}'")


    def _export_concrete(self, material: MaterialConcrete) -> None:
        eu = self._eu
        if isinstance(material, MaterialConcrete):
            m: MaterialConcrete = material
            self.MidasMaterial.CONC.User(
                name=material.name,
                E=to_float(m.general_properties.modulus_of_elasticity, eu.pressure),
                mass=to_float(m.general_properties.unit_weight, eu.weight_density),
                pois=m.general_properties.poissons_ratio,
                therm=to_float(m.general_properties.thermal_coefficient, eu.temperature_coef),
                id=material.model_id,
            )
        else:
            raise ValueError(f"Unsupported material object: {type(material)} for material '{material.name}'")


    def _export_user_defined(self, material: MaterialBase) -> None:
        eu = self._eu
        m: MaterialBase = material
        if isinstance(material.general_properties, GeneralMaterialIsotropicProperties):
            iso_prop: GeneralMaterialIsotropicProperties = material.general_properties
            self.MidasMaterial.USER(
                name=material.name,
                E=to_float(iso_prop.modulus_of_elasticity, eu.pressure),
                mass=to_float(iso_prop.unit_weight, eu.weight_density),
                pois=iso_prop.poissons_ratio,
                therm=to_float(iso_prop.thermal_coefficient, eu.temperature_coef),
                id=material.model_id,
            )
        else:
            raise NotImplementedError(f"Non isotropic material type is not yet implemented. Material: {material.name}")


    @staticmethod
    def _normalize_name(name: str) -> str:
        """Convert input string to concatenated CamelCase words, remove spaces/underscores,
        and trim to 16 chars (MIDAS Civil limit)."""
        parts = re.split(r"[ _]+", name.strip())
        words = [p for p in parts if p]
        camel = "".join(w[:1].upper() + w[1:].lower() for w in words)
        camel = camel.replace(" ", "").replace("_", "")
        return name[:16]

