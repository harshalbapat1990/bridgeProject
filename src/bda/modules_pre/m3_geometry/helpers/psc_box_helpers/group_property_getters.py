from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.substructure_properties import GroupPropertiesPileCap, \
    GroupPropertiesSupport, GroupPropertiesAboveGround, GroupPropertiesBelowGround, GroupPropertiesCrossbeam, \
    GroupPropertiesPile
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import GroupPropertiesSpan


class GroupPropertyGetter:

    @staticmethod
    def get_span_properties(group: GeometryGroup) -> GroupPropertiesSpan:
        if not group.component_type == StructuralComponentType.SPAN:
            raise ValueError(f"Provided group {group.name} is not of component type: {StructuralComponentType.SPAN}")
        if not isinstance(group.properties, GroupPropertiesSpan):
            raise TypeError(f"Group '{group.name}' properties are not of type GroupPropertiesSpan.")
        return group.properties

    @staticmethod
    def get_support_properties(group: GeometryGroup) -> GroupPropertiesSupport:
        if not group.component_type == StructuralComponentType.SUPPORT:
            raise ValueError(f"Provided group {group.name} is not of component type: {StructuralComponentType.SUPPORT}")
        if not isinstance(group.properties, GroupPropertiesSupport):
            raise TypeError(f"Group '{group.name}' properties are not of type GroupPropertiesSupport.")
        return group.properties

    @staticmethod
    def get_crosshead_properties(group: GeometryGroup) -> GroupPropertiesCrossbeam:
        if not group.component_type == StructuralComponentType.CROSSBEAM:
            raise ValueError(f"Provided group {group.name} is not of component type: {StructuralComponentType.CROSSBEAM}")
        if not isinstance(group.properties, GroupPropertiesCrossbeam):
            raise TypeError(f"Group '{group.name}' properties are not of type GroupPropertiesCrossbeam.")
        return group.properties

    @staticmethod
    def get_pilecap_properties(group: GeometryGroup) -> GroupPropertiesPileCap:
        if not group.component_type == StructuralComponentType.PILE_CAP:
            raise ValueError(f"Provided group {group.name} is not of component type: {StructuralComponentType.PILE_CAP}")
        if not isinstance(group.properties, GroupPropertiesPileCap):
            raise TypeError(f"Group '{group.name}' properties are not of type GroupPropertiesPilecap.")
        return group.properties

    @staticmethod
    def get_above_ground_properties(group: GeometryGroup) -> GroupPropertiesAboveGround:
        if not group.component_type == StructuralComponentType.ABOVE_GROUND:
            raise ValueError(f"Provided group {group.name} is not of component type: {StructuralComponentType.ABOVE_GROUND}")
        if not isinstance(group.properties, GroupPropertiesAboveGround):
            raise TypeError(f"Group '{group.name}' properties are not of type GroupPropertiesAboveGround.")
        return group.properties

    @staticmethod
    def get_below_ground_properties(group: GeometryGroup) -> GroupPropertiesBelowGround:
        if not group.component_type == StructuralComponentType.BELOW_GROUND:
            raise ValueError(f"Provided group {group.name} is not of component type: {StructuralComponentType.BELOW_GROUND}")
        if not isinstance(group.properties, GroupPropertiesBelowGround):
            raise TypeError(f"Group '{group.name}' properties are not of type GroupPropertiesBelowGround.")
        return group.properties

    @staticmethod
    def get_pile_properties(group: GeometryGroup) -> GroupPropertiesPile:
        if not group.component_type == StructuralComponentType.PILE:
            raise ValueError(f"Provided group {group.name} is not of component type: {StructuralComponentType.PILE}")
        if not isinstance(group.properties, GroupPropertiesPile):
            raise TypeError(f"Group '{group.name}' properties are not of type GroupPropertiesPile.")
        return group.properties