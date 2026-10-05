from bda.domain.enums import MaterialType, MaterialModelType
from bda.domain.models.submodels import MaterialBase, MaterialConcrete, MaterialSteel, MaterialReinforcement, \
    MaterialTendon
from bda.domain.models.submodels.material import GeneralMaterialIsotropicProperties
from bda.domain.units.export_units import ExportUnits, to_float


class CsiMaterialExporter:
    def __init__(self, sapModel, eu: ExportUnits):
        self.sapModel = sapModel
        self._eu: ExportUnits = eu

    def export_material(self, material: MaterialBase):
        sapModel = self.sapModel
        eu = self._eu

        if not isinstance(material, MaterialBase):
            raise Exception(f"Fail to export custom material {material.name}."
                            f"Invalid object {type(material)}")

        eMatType = CSI_MAT_TYPE_BY_MATERIAL_TYPE.get(material.material_type, 3)

        # Get the specific properties setter for concrete, steel, rebar or tendon
        prop_setter = self._get_set_properties_registry().get(material.material_type, None)
        if prop_setter is None:
            raise Exception(f"Fail to set material properties {material.name}. "
                            f"Unsupported material type {material.material_type}")

        # First set general material type
        ret = sapModel.PropMaterial.SetMaterial(material.name, eMatType)
        if ret != 0:
            raise Exception(f"Fail to export material {material.name}")

        # Then set basic material properties for isotropic type
        if material.material_model_type == MaterialModelType.ISOTROPIC and \
                isinstance(material.general_properties, GeneralMaterialIsotropicProperties):

            gen_prop: GeneralMaterialIsotropicProperties = material.general_properties
            ret = sapModel.PropMaterial.SetMPIsotropic(
                material.name,
                to_float(gen_prop.modulus_of_elasticity, eu.pressure),
                gen_prop.poissons_ratio,                                          # dimensionless
                to_float(gen_prop.thermal_coefficient, eu.temperature_coef),
            )
            if ret != 0:
                raise Exception(f"Fail to set material properties {material.name}")

            # Set specific properties for material
            prop_setter(material)

        else:
            raise NotImplementedError(f"Non isotropic materials are not yet implemented. Material: {material.name}.")


    def set_concrete_properties(self, material: MaterialConcrete) -> None:
        m : MaterialConcrete = material
        eu = self._eu

        if not isinstance(material, MaterialConcrete):
            raise Exception(f"Fail to set concrete material properties {m.name}"
                            f"Invalid object {type(material)}")

        sapModel = self.sapModel

        # Get current material properties
        mat_data = sapModel.PropMaterial.GetOConcrete_1(m.name)

        ret = mat_data[-1]
        if ret != 0:
            raise Exception(f"Fail to get default concrete material properties {m.name}")

        # Set concrete properties replacing only the concrete compressive strength
        ret = sapModel.PropMaterial.SetOConcrete_1(
            m.name,
            to_float(m.design_properties.characteristic_compressive_strength_fck, eu.pressure),
            mat_data[1], mat_data[2], mat_data[3], mat_data[4],
            mat_data[5], mat_data[6], mat_data[7],
        )
        if ret != 0:
            raise Exception(f"Fail to set default concrete material properties {m.name}")


    def set_steel_properties(self, material: MaterialSteel) -> None:
        m : MaterialSteel = material
        eu = self._eu

        if not isinstance(material, MaterialSteel):
            raise Exception(f"Fail to set steel material properties {m.name}"
                            f"Invalid object {type(material)}")

        sapModel = self.sapModel

        # Get current material properties
        mat_data = sapModel.PropMaterial.GetOSteel_1(m.name)

        ret = mat_data[-1]
        if ret != 0:
            raise Exception(f"Fail to get default steel material properties {m.name}")

        # Set steel properties replacing only the yield and tensile parameters
        ret = sapModel.PropMaterial.SetOSteel_1(
            m.name,
            to_float(m.design_properties.characteristic_yield_strength_fyk, eu.pressure),
            to_float(m.design_properties.characteristic_ultimate_tensile_strength_fuk, eu.pressure),
            to_float(m.design_properties.mean_yield_strength_fym, eu.pressure),
            to_float(m.design_properties.mean_ultimate_tensile_strength_fum, eu.pressure),
            mat_data[4], mat_data[5], mat_data[6], mat_data[7],
            mat_data[8], mat_data[9], mat_data[10],
        )
        if ret != 0:
            raise Exception(f"Fail to set default steel material properties {m.name}")


    def set_rebar_properties(self, material: MaterialReinforcement) -> None:
        m : MaterialReinforcement = material
        eu = self._eu

        if not isinstance(material, MaterialReinforcement):
            raise Exception(f"Fail to set reinforcement material properties {m.name}"
                            f"Invalid object {type(material)}")

        sapModel = self.sapModel

        # Get current material properties
        mat_data = sapModel.PropMaterial.GetORebar_1(m.name)

        ret = mat_data[-1]
        if ret != 0:
            raise Exception(f"Fail to get default rebar material properties {m.name}")

        # Set rebar properties replacing only the yield and tensile parameters
        ret = sapModel.PropMaterial.SetORebar_1(
            m.name,
            to_float(m.design_properties.characteristic_yield_strength_fyk, eu.pressure),
            to_float(m.design_properties.characteristic_ultimate_tensile_strength_fuk, eu.pressure),
            to_float(m.design_properties.mean_yield_strength_fym, eu.pressure),
            to_float(m.design_properties.mean_ultimate_tensile_strength_fum, eu.pressure),
            mat_data[4], mat_data[5], mat_data[6], mat_data[7],
            mat_data[8], mat_data[9], mat_data[10],
        )
        if ret != 0:
            raise Exception(f"Fail to set default rebar material properties {m.name}")


    def set_tendon_properties(self, material: MaterialTendon) -> None:
        m : MaterialTendon = material
        eu = self._eu

        if not isinstance(material, MaterialTendon):
            raise Exception(f"Fail to set tendon material properties {m.name}"
                            f"Invalid object {type(material)}")

        sapModel = self.sapModel

        # Get current material properties
        mat_data = sapModel.PropMaterial.GetOTendon_1(m.name)

        ret = mat_data[-1]
        if ret != 0:
            raise Exception(f"Fail to get default tendon material properties {m.name}")

        # Set tendon properties replacing only the yield and tensile parameters
        ret = sapModel.PropMaterial.SetOTendon_1(
            m.name,
            to_float(m.design_properties.characteristic_yield_strength_fyk, eu.pressure),
            to_float(m.design_properties.characteristic_ultimate_tensile_strength_fuk, eu.pressure),
            mat_data[2], mat_data[3], mat_data[4], mat_data[5],
        )
        if ret != 0:
            raise Exception(f"Fail to set default tendon material properties {m.name}")


    def _get_set_properties_registry(self) -> dict:
        return {
            MaterialType.STEEL: self.set_steel_properties,
            MaterialType.REINFORCEMENT: self.set_rebar_properties,
            MaterialType.CONCRETE: self.set_concrete_properties,
            MaterialType.TENDON: self.set_tendon_properties
        }

CSI_MAT_TYPE_BY_MATERIAL_TYPE = {
    MaterialType.STEEL: 1,
    MaterialType.CONCRETE: 2,
    MaterialType.REINFORCEMENT: 6,
    MaterialType.TENDON: 7,
}

