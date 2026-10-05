from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator

from .geometry_elements import ParaElement
from .enums import StructuralComponentTypeParaModel
from .component_properties.properties_base import PropertiesBaseParaModel
from .component_properties.properties_mapping import _PROPERTIES_BY_GROUP_TYPE
# -------------------------
# Main geometry group
# -------------------------

class GeometryGroupParaModel(BaseModel):
    group_id: str
    structural_component_type: StructuralComponentTypeParaModel
    name: str

    material_id: str | None = Field(default=None) # material_id: str
    section_id: str | None = Field(default=None) # section_id: str

    elements: List[ParaElement] = Field(default_factory=list) # empty

    nested_groups: List["GeometryGroupParaModel"] = Field(default_factory=list) # empty
    parent_group_id: str | None = Field(default=None)

    properties: PropertiesBaseParaModel | None = Field(default=None)

    model_config = {
        "frozen": True,
        "extra": "allow",
    }

    @field_validator("properties", mode="before")
    @classmethod
    def _map_properties(cls, v: str, info):
        if v is None:
            return v

        group_type = info.data.get("structural_component_type")
        if group_type is None:
            return v

        parameters_cls = _PROPERTIES_BY_GROUP_TYPE.get(group_type)
        if parameters_cls is None:
            raise ValueError(f"No properties model for {group_type}")

        return parameters_cls.model_validate(v)
