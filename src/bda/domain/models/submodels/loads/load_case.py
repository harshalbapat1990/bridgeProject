"""LoadCase - a named container that every FE-level load must belong to.

NOTE: do not add ``from __future__ import annotations`` to modules in this
package. Postponed annotations turn ``Annotated[...]`` field types into
strings and silently disable ``validate_pint_fields`` dimension checks.
"""
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(kw_only=True, eq=False)
class LoadCase:
    """Represents a load case to which FE-level loads are assigned.

    Attributes:
        guid (UUID): Unique identifier of the load case.
        model_id (int): Sequential id assigned by the ``Loads`` container
            when the load case is registered. ``0`` means "not registered".
        name (str): Unique (within a ``Loads`` container) human-readable name.
            This is the name that will appear in the analytical software.
        description (str | None): Optional free-text description.
        load_nature (str | None): Optional AASHTO nature of the load
            (DC, DW, LL, ...) used for later combination/factor resolution.
    """

    guid: UUID = field(default_factory=uuid4)
    _model_id: int = field(default=0, init=False)
    name: str
    description: str | None = None
    load_nature: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("LoadCase name must be a non-empty string.")

    @property
    def model_id(self) -> int:
        """Return the sequential id assigned by the ``Loads`` container."""
        return self._model_id

    def set_id(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("LoadCase model_id must be an integer.")
        if value < 0:
            raise ValueError("LoadCase model_id must be >= 0.")
        self._model_id = value

    def __repr__(self) -> str:
        nature = self.load_nature if self.load_nature is not None else None
        return f"LoadCase[id: {self.model_id}, name: '{self.name}', nature: {nature}]"

    def __hash__(self) -> int:
        return hash(self.guid)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return self.guid == other.guid
