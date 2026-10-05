"""LoadCase — identifier and metadata for a single load case or combination."""
from __future__ import annotations

from dataclasses import dataclass

from bda.domain.enums.load_case_enums import LoadCaseType


@dataclass(frozen=True)
class LoadCase:
    """Represents a load case reference used by calculators and the importer.

    Attributes:
        name: Exact name as it appears in the source program (e.g. CSI combo name).
              Naming conventions ensure this name matches between calculator
              and source program.
        load_case_type: Whether this case returns a single value or an envelope.
    """
    name: str
    load_case_type: LoadCaseType = LoadCaseType.SINGLE_VALUED

    def __str__(self) -> str:
        return self.name
