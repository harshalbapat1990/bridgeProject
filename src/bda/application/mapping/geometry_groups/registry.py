from typing import Callable, TypeVar, Type

from bda.contracts.paramodel.groups import PropertiesBaseParaModel
from bda.contracts.paramodel.groups.enums import StructuralComponentTypeParaModel
from bda.domain.models.submodels.geometry_group import GroupProperties

PROPERTIES_MAPPERS: dict[StructuralComponentTypeParaModel, Callable[
    [PropertiesBaseParaModel], GroupProperties
]] = {}


P = TypeVar("P", bound=PropertiesBaseParaModel)
R = TypeVar("R", bound=GroupProperties)


def register_properties_mapper(
    component_type: StructuralComponentTypeParaModel,
) -> Callable[[Callable[[P], R]], Callable[[P], R]]:
    def wrapper(func: Callable[[P], R]) -> Callable[[P], R]:
        PROPERTIES_MAPPERS[component_type] = func
        return func
    return wrapper
