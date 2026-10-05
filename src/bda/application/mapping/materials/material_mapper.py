"""
Mapper: MaterialParaModel  →  MaterialBase domain objects.

Usage
-----
::

    from bda.contracts.materials import MaterialParaModelAdapter
    from bda.application.mapping.materials.material_mapper import MaterialMapper

    adapter = MaterialParaModelAdapter.model_validate(raw_data)
    domain_objects = MaterialMapper.to_domain_list(adapter.materials)
"""

from __future__ import annotations

from typing import List, Callable

from bda.contracts.paramodel.materials import (
    DesignParametersConcreteAashtoParaModel,
    ReinforcementDesignParametersAashtoParaModel,
    SteelDesignParametersAashtoParaModel,
    TendonDesignParametersAashtoParaModel,
    MaterialBaseParaModel,
    MaterialParaModel,
)
from bda.domain.models.submodels import (MaterialBase, MaterialConcrete, MaterialSteel,
                                         MaterialReinforcement, MaterialTendon)
from bda.application.mapping.base import to_pint, to_uuid
from bda.domain.models.submodels.material import GeneralMaterialIsotropicProperties, DesignPropertiesConcrete, \
    DesignPropertiesSteel, DesignPropertiesReinforcement, DesignPropertiesTendon
from bda.contracts.paramodel.materials.materials_para_model import (
    GeneralMaterialIsotropicProperties as GenMatIsoPropParaModel, MaterialModelTypeParaModel, MaterialTypeParaModel,
    StandardCodeParaModel)

# ---------------------------------------------------------------------------
# MaterialRegistry class
# ---------------------------------------------------------------------------

MaterialKey = tuple[MaterialModelTypeParaModel, MaterialTypeParaModel, StandardCodeParaModel]
MaterialMapperFunc = Callable[[MaterialBaseParaModel], MaterialBase]

class _RegistryMappingFunctions:
    """
    Registry for materials mapping functions.

    This class maintains a mapping between
    `(MaterialModelTypeParaModel, MaterialTypeParaModel, StandardCode)`
    keys and corresponding mapper functions. Each mapper function converts a
    `MaterialBaseParaModel` instance into a domain-level `MaterialBase` object.

    Mappers are registered using the `register` decorator and retrieved
    automatically at runtime via the `map` method.

    Example:
        @_MaterialRegistry.register(
            MaterialModelTypeParaModel.ISOTROPIC,
            MaterialTypeParaModel.CONCRETE,
            StandardCodeParaModel.AASHTO
        )
        def _map_user_angle(sec: MaterialBaseParaModel) -> MaterialBase:
            ...

        result = _MaterialRegistry.map(mat)

    Notes:
        - Each (material_model_type, material_type, standard_code) pair can have only one mapper.
        - Attempting to register a duplicate mapper raises a RuntimeError.
        - Calling `map` with an unregistered key raises NotImplementedError.
    """

    _registry: dict[MaterialKey, MaterialMapperFunc] = {}

    @classmethod
    def available_keys(cls) -> list[MaterialKey]:
        return list(cls._registry.keys())

    @classmethod
    def register(
            cls,
            material_model_type: MaterialModelTypeParaModel,
            material_type: MaterialTypeParaModel,
            standard_code: StandardCodeParaModel
            ) -> Callable[[MaterialMapperFunc], MaterialMapperFunc]:
        """
        Register a material-mapping function for the given material family and type.

        This method is used as a decorator that associates a mapping function
        with a specific `(material_model_type, material_type)` pair.

        Args:
            material_model_type (MaterialModelTypeParaModel): Material model type identifier.
            material_type (MaterialTypeParaModel): Material type identifier.
            standard_code (StandardCodeParaModel): Standard code identifier.

        Returns:
            Callable: A decorator that registers the mapping function.

        Raises:
            RuntimeError: If a mapper for the given key is already registered.

        Example:
            @_MaterialRegistry.register(
                MaterialModelTypeParaModel.USER,
                MaterialTypeParaModel.ANGLE,
                StandardCodeParaModel.AASHTO)
            def _map_concrete(sec: MaterialBaseParaModel) -> MaterialBase:
                ...
        """

        def decorator(func: MaterialMapperFunc) -> MaterialMapperFunc:
            key = (material_model_type, material_type, standard_code)

            if key in cls._registry:
                raise RuntimeError(f"Duplicate mapper for {key}")

            cls._registry[key] = func
            return func

        return decorator

    @classmethod
    def map(cls, mat: MaterialBaseParaModel) -> MaterialBase:
        """
            Map a parameter model material to its corresponding domain material.

            This method looks up a registered mapper based on the
            `(material_model_type, material_type)` attributes of the given
            `MaterialBaseParaModel` instance and applies it to produce
            a `MaterialBase` domain object.

            Args:
                mat (MaterialBaseParaModel): Input material model to be mapped.

            Returns:
                MaterialBase: Mapped domain material object.

            Raises:
                NotImplementedError: If no mapper is registered for the given
                    `(material_model_type, material_type, standard_code)` pair.
            """

        if mat.design_parameters is None:
            raise ValueError(f"Material: {mat.name} does not contain design parameters. Material skipped.")

        key = (mat.material_model_type, mat.material_type, mat.standard_code)

        try:
            mapper = cls._registry[key](mat)
            return mapper
        except KeyError:
            raise NotImplementedError(
                f"No mapper registered for material: {mat.name}"
                f"Material type: {mat.material_type}, material model type: {mat.material_model_type},"
                f"standard code: {mat.standard_code} is not implemented."
            )


# ---------------------------------------------------------------------------
# Private sub-mappers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Mapping functions: ISOTROPIC, AASHTO, CONCRETE
# ---------------------------------------------------------------------------

@_RegistryMappingFunctions.register(MaterialModelTypeParaModel.ISOTROPIC,
                                    MaterialTypeParaModel.CONCRETE,
                                    StandardCodeParaModel.AASHTO)
def _map_concrete_isotropic_aashto(mat: MaterialBaseParaModel) -> MaterialBase:
    if not isinstance(mat.general_properties, GenMatIsoPropParaModel):
        raise ValueError(f"Isotropic material type should have general properties "
                         f"of type {GenMatIsoPropParaModel.__name__}. Material: {mat.name}")
    gen_prop: GenMatIsoPropParaModel = mat.general_properties

    if not isinstance(mat.design_parameters, DesignParametersConcreteAashtoParaModel):
        raise ValueError(f"Concrete material type should have design properties "
                         f"of type {DesignParametersConcreteAashtoParaModel.__name__}. "
                         f"Material: {mat.name}")
    des_prop: DesignParametersConcreteAashtoParaModel = mat.design_parameters

    return MaterialConcrete(
        guid=to_uuid(mat.material_id),
        source_id=mat.material_id,
        name=mat.name,
        general_properties=GeneralMaterialIsotropicProperties(
            unit_weight=to_pint(mat.general_properties.unit_weight),
            modulus_of_elasticity=to_pint(gen_prop.modulus_of_elasticity),
            poissons_ratio=gen_prop.poissons_ratio.value,
            thermal_coefficient=to_pint(gen_prop.thermal_coefficient),
        ),
        design_properties=DesignPropertiesConcrete(
            characteristic_compressive_strength_fck=
            to_pint(des_prop.specified_minimum_compressive_strength),
            mean_compressive_strength_fcm=
            to_pint(des_prop.expected_compressive_strength),
        )
    )

# ---------------------------------------------------------------------------
# Mapping functions: ISOTROPIC, AASHTO, STEEL
# ---------------------------------------------------------------------------

@_RegistryMappingFunctions.register(MaterialModelTypeParaModel.ISOTROPIC,
                                    MaterialTypeParaModel.STEEL,
                                    StandardCodeParaModel.AASHTO)
def _map_steel_isotropic_aashto(mat: MaterialBaseParaModel) -> MaterialBase:
    if not isinstance(mat.general_properties, GenMatIsoPropParaModel):
        raise ValueError(f"Isotropic material type should have general properties "
                         f"of type {GenMatIsoPropParaModel.__name__}. Material: {mat.name}")
    gen_prop: GenMatIsoPropParaModel = mat.general_properties

    if not isinstance(mat.design_parameters, SteelDesignParametersAashtoParaModel):
        raise ValueError(f"Steel material type should have design properties "
                         f"of type {SteelDesignParametersAashtoParaModel.__name__}. "
                         f"Material: {mat.name}")
    des_prop: SteelDesignParametersAashtoParaModel = mat.design_parameters

    return MaterialSteel(
        guid=to_uuid(mat.material_id),
        source_id=mat.material_id,
        name=mat.name,
        general_properties=GeneralMaterialIsotropicProperties(
            unit_weight=to_pint(mat.general_properties.unit_weight),
            modulus_of_elasticity=to_pint(gen_prop.modulus_of_elasticity),
            poissons_ratio=gen_prop.poissons_ratio.value,
            thermal_coefficient=to_pint(gen_prop.thermal_coefficient),
        ),
        design_properties=DesignPropertiesSteel(
            characteristic_yield_strength_fyk=
            to_pint(des_prop.specified_minimum_yield_strength),
            characteristic_ultimate_tensile_strength_fuk=
            to_pint(des_prop.specified_minimum_tensile_strength),
            mean_yield_strength_fym=
            to_pint(des_prop.expected_yield_strength),
            mean_ultimate_tensile_strength_fum=
            to_pint(des_prop.expected_tensile_strength)
        )
    )

# ---------------------------------------------------------------------------
# Mapping functions: ISOTROPIC, AASHTO, REINFORCEMENT
# ---------------------------------------------------------------------------

@_RegistryMappingFunctions.register(MaterialModelTypeParaModel.ISOTROPIC,
                                    MaterialTypeParaModel.REINFORCEMENT,
                                    StandardCodeParaModel.AASHTO)
def _map_reinforcement_isotropic_aashto(mat: MaterialBaseParaModel) -> MaterialBase:
    if not isinstance(mat.general_properties, GenMatIsoPropParaModel):
        raise ValueError(f"Isotropic material type should have general properties "
                         f"of type {GenMatIsoPropParaModel.__name__}. Material: {mat.name}")
    gen_prop: GenMatIsoPropParaModel = mat.general_properties

    if not isinstance(mat.design_parameters, ReinforcementDesignParametersAashtoParaModel):
        raise ValueError(f"Reinforcement material type should have design properties "
                         f"of type {ReinforcementDesignParametersAashtoParaModel.__name__}. "
                         f"Material: {mat.name}")
    des_prop: ReinforcementDesignParametersAashtoParaModel = mat.design_parameters

    return MaterialReinforcement(
        guid=to_uuid(mat.material_id),
        source_id=mat.material_id,
        name=mat.name,
        general_properties=GeneralMaterialIsotropicProperties(
            unit_weight=to_pint(mat.general_properties.unit_weight),
            modulus_of_elasticity=to_pint(gen_prop.modulus_of_elasticity),
            poissons_ratio=gen_prop.poissons_ratio.value,
            thermal_coefficient=to_pint(gen_prop.thermal_coefficient),
        ),
        design_properties=DesignPropertiesReinforcement(
            characteristic_yield_strength_fyk=
            to_pint(des_prop.specified_minimum_yield_strength),
            characteristic_ultimate_tensile_strength_fuk=
            to_pint(des_prop.specified_minimum_tensile_strength),
            mean_yield_strength_fym=
            to_pint(des_prop.expected_yield_strength),
            mean_ultimate_tensile_strength_fum=
            to_pint(des_prop.expected_tensile_strength)
        )
    )

# ---------------------------------------------------------------------------
# Mapping functions: ISOTROPIC, AASHTO, TENDON
# ---------------------------------------------------------------------------

@_RegistryMappingFunctions.register(MaterialModelTypeParaModel.ISOTROPIC,
                                    MaterialTypeParaModel.TENDON,
                                    StandardCodeParaModel.AASHTO)
def _map_tendon_isotropic_aashto(mat: MaterialBaseParaModel) -> MaterialBase:
    if not isinstance(mat.general_properties, GenMatIsoPropParaModel):
        raise ValueError(f"Isotropic material type should have general properties "
                         f"of type {GenMatIsoPropParaModel.__name__}. Material: {mat.name}")
    gen_prop: GenMatIsoPropParaModel = mat.general_properties

    if not isinstance(mat.design_parameters, TendonDesignParametersAashtoParaModel):
        raise ValueError(f"Tendon material type should have design properties "
                         f"of type {TendonDesignParametersAashtoParaModel.__name__}. "
                         f"Material: {mat.name}")
    des_prop: TendonDesignParametersAashtoParaModel = mat.design_parameters

    return MaterialTendon(
        guid=to_uuid(mat.material_id),
        source_id=mat.material_id,
        name=mat.name,
        general_properties=GeneralMaterialIsotropicProperties(
            unit_weight=to_pint(mat.general_properties.unit_weight),
            modulus_of_elasticity=to_pint(gen_prop.modulus_of_elasticity),
            poissons_ratio=gen_prop.poissons_ratio.value,
            thermal_coefficient=to_pint(gen_prop.thermal_coefficient),
        ),
        design_properties=DesignPropertiesTendon(
            characteristic_yield_strength_fyk=
            to_pint(des_prop.specified_minimum_yield_strength),
            characteristic_ultimate_tensile_strength_fuk=
            to_pint(des_prop.specified_minimum_tensile_strength)
        )
    )

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class MaterialMapper:
    """
    Entry point for mapping ``MaterialParaModel`` contracts to domain objects.

    Maps grouped ParaModel contracts to domain objects.
    """

    @staticmethod
    def to_domain(para_model: MaterialParaModel) -> MaterialBase:
        """Map a single ``MaterialParaModel`` to its domain counterpart.

        """
        return _RegistryMappingFunctions.map(para_model)

    @staticmethod
    def to_domain_list(para_models: List[MaterialParaModel]) -> List[MaterialBase]:
        """Map a list of ParaModels to domain objects, preserving order.

        If a ParaModel carries a non-None ``id`` field it is forwarded to
        ``set_id()`` on the resulting domain object so that downstream
        consumers (e.g. group consistency checks) can resolve references.
        """
        return [MaterialMapper.to_domain(mat) for mat in para_models]
