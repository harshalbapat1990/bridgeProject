from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Union

from pint.registry import Quantity

from bda.domain.models.submodels.element import Element1D


class StiffnessType(str, Enum):
    """Enumeration for stiffness representation used by an entire beam-end release."""

    RELATIVE_VALUE = "relative value"
    ABSOLUTE_VALUE = "absolute value"


@dataclass
class DirectionalRelease:
    """Represents release state and optional stiffness value for a single DOF.

    Attributes:
        enabled: Whether this DOF is released (True) or fixed (False, default).
        value: Stiffness value when enabled. Type depends on StiffnessType:
               - RELATIVE_VALUE: float >= 0
               - ABSOLUTE_VALUE: Quantity >= 0
               When enabled=False, value is ignored.
    """

    enabled: bool = False
    value: Union[float, Quantity, None] = None

    def __post_init__(self) -> None:
        if self.enabled and self.value is None:
            raise ValueError(f"DirectionalRelease: value is required when enabled=True")
        if self.enabled and isinstance(self.value, (int, float)):
            if self.value < 0:
                raise ValueError(f"DirectionalRelease: relative value must be >= 0, got {self.value}")
        if self.enabled and isinstance(self.value, Quantity):
            if self.value.magnitude < 0:
                raise ValueError(f"DirectionalRelease: absolute value must be >= 0, got {self.value}")


@dataclass
class NodeRelease:
    """Represents the release conditions at a node for all DOFs.

    All DOFs default to disabled (fixed). Set enabled=True and provide value
    to release a specific direction.
    """

    F_x: DirectionalRelease = field(default_factory=lambda: DirectionalRelease())
    F_y: DirectionalRelease = field(default_factory=lambda: DirectionalRelease())
    F_z: DirectionalRelease = field(default_factory=lambda: DirectionalRelease())
    M_x: DirectionalRelease = field(default_factory=lambda: DirectionalRelease())
    M_y: DirectionalRelease = field(default_factory=lambda: DirectionalRelease())
    M_z: DirectionalRelease = field(default_factory=lambda: DirectionalRelease())
    M_b: DirectionalRelease = field(default_factory=lambda: DirectionalRelease())


@dataclass
class BeamEndRelease:
    """Represents a beam end release in a structural model.

    Attributes:
        element_reference (Element1D): The beam element this release is applied to.
        stiffness_type (StiffnessType): Type of stiffness values (RELATIVE_VALUE or ABSOLUTE_VALUE).
        start_node_release (NodeRelease): The release conditions at the start node of the beam.
        end_node_release (NodeRelease): The release conditions at the end node of the beam.
    """

    element_reference: Element1D
    stiffness_type: StiffnessType = StiffnessType.RELATIVE_VALUE
    start_node_release: NodeRelease = field(default_factory=NodeRelease)
    end_node_release: NodeRelease = field(default_factory=NodeRelease)

    def __post_init__(self) -> None:
        """Validate that all enabled DOF values match stiffness_type."""
        expected_value_type = float if self.stiffness_type == StiffnessType.RELATIVE_VALUE else Quantity

        for node_release, node_name in (
            (self.start_node_release, "start_node_release"),
            (self.end_node_release, "end_node_release"),
        ):
            for dof_name in ("F_x", "F_y", "F_z", "M_x", "M_y", "M_z", "M_b"):
                dof = getattr(node_release, dof_name)
                if dof.enabled:
                    if not isinstance(dof.value, expected_value_type):
                        raise ValueError(
                            f"{node_name}.{dof_name}: value type must be {expected_value_type.__name__} "
                            f"for stiffness_type={self.stiffness_type.value}, got {type(dof.value).__name__}"
                        )
