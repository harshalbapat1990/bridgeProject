from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from itertools import count
from typing import Set
from uuid import UUID, uuid4

from bda.domain.enums import OffsetReference, SectionFamily, SectionType
from bda.domain.models.submodels.material import MaterialBase
from bda.domain.units.quantities import Length
from bda.domain.units.registry import m as meter


@dataclass
class Offset():
    offset_reference: OffsetReference = OffsetReference.CENTER_CENTER
    horizontal_value: Length = field(default=0.0 * meter)
    vertical_value: Length = field(default=0.0 * meter)


_section_id_counter = count(1)

def next_section_id() -> int:
    return next(_section_id_counter)


@dataclass(kw_only=True, eq=False)
class SectionBase(ABC):
    guid: UUID = field(default_factory=uuid4)
    source_id: str | None = None
    model_id: int = field(default_factory=next_section_id, init=False, doc="Identifier of the section, "
                                                        "used exclusively for export to analytical software.")
    name: str
    section_family: SectionFamily
    section_type: SectionType
    offset: Offset = field(default_factory=Offset)
    material_main: MaterialBase | None = field(
        default=None,
        init=False,
        doc="Primary material of the section. This material must be defined for all composite sections before exporting to analytical software."
    )
    dimensions: DimensionsBase = field(init=False)

    def set_id(self, section_id: int) -> None:
        """
        Set the section model identifier.

        The identifier is used exclusively when exporting data to analytical
        software.

        Parameters
        ----------
        section_id : int
            Model identifier to assign to the section.

        Returns
        -------
        None
        """
        self.model_id = section_id

    def set_material_main(self, material_main: MaterialBase | None = None) -> None:
        """
        Set the primary material of the section.

        The primary material is required for all composite sections before
        exporting data to analytical software.

        Parameters
        ----------
        material_main : MaterialBase | None, optional
            Material to assign as the primary material of the section.
            If None, the current primary material is cleared.

        Returns
        -------
        None
        """
        self.material_main = material_main

    def _shallow_copy_fields(self) -> Set[str]:
        """
        Fields copied by reference instead of deepcopy.
        Child classes may extend
        """
        return {
            "material_main",
        }

    def __deepcopy__(self, memo):
        from copy import deepcopy

        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        shallow_fields = self._shallow_copy_fields()

        for field_name, value in self.__dict__.items():
            if field_name == "guid":
                setattr(result, field_name, uuid4())
            elif field_name == "model_id":
                setattr(result, field_name, next_section_id())
            elif field_name in shallow_fields:
                setattr(result, field_name, value)
            else:
                setattr(result, field_name, deepcopy(value, memo))
        return result

Section = SectionBase


@dataclass
class DimensionsBase(ABC):

    @property
    @abstractmethod
    def total_height(self) -> Length:
        """Return total height of section"""
        raise NotImplementedError

    @property
    @abstractmethod
    def total_width(self) -> Length:
        """Return total width of section"""
        raise NotImplementedError
