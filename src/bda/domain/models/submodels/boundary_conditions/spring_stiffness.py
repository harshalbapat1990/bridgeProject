from __future__ import annotations

from dataclasses import dataclass, field

from pint.registry import Quantity

from bda.domain.base import MultiModelObjectBase
from bda.domain.models.submodels.boundary_conditions.enums import DofTypeEnum


@dataclass(kw_only=True)
class SpringStiffnessBase(MultiModelObjectBase):
    """
    Base class for spring stiffness properties, representing the stiffness characteristics of a spring support condition in a structural model.
    This class serves as a foundation for defining translational and rotational stiffness values for each degree of freedom (DOF) of the spring support.
    Default dof_type is set to FIXED, indicating that the spring is fully restrained in all directions.
    """
    dof_type: DofTypeEnum = DofTypeEnum.FIXED


@dataclass(kw_only=True)
class TranslationalStiffness(SpringStiffnessBase):
    """
    Represents the translational stiffness properties of a spring support condition in a structural model.
    This class encapsulates the translational stiffness values for each degree of freedom (DOF) of the spring support.
    Default dof_type is set to FIXED, indicating that the spring is fully restrained in all translational directions.
    Default stiffness values are set to None, indicating that the stiffness is not defined unless specified.
    Attributes
    ----------
    stiffness : Quantity | None
        Translational stiffness value for the corresponding degree of freedom (DOF) of the spring support.
    """
    stiffness: Quantity | None = None


@dataclass(kw_only=True)
class RotationalStiffness(SpringStiffnessBase):
    """
    Represents the rotational stiffness properties of a spring support condition in a structural model.
    This class encapsulates the rotational stiffness values for each degree of freedom (DOF) of the spring support.
    Default dof_type is set to FIXED, indicating that the spring is fully restrained in all rotational directions.
    Default stiffness values are set to None, indicating that the stiffness is not defined unless specified.
    Attributes
    ----------
    stiffness : Quantity | None
        Rotational stiffness value for the corresponding degree of freedom (DOF) of the spring support.
    """
    stiffness: Quantity | None = None


@dataclass(kw_only=True)
class SpringStiffness(MultiModelObjectBase):
    """
    Represents the stiffness properties of a spring support condition in a structural model.
    This class encapsulates the translational and rotational stiffness values for each degree of freedom (DOF) of the spring support.
    Default dof_type is set to FIXED for all stiffness components, indicating that the spring is fully restrained in all directions.
    Default stiffness values are set to None, indicating that the stiffness is not defined unless specified.
    Attributes
    ----------
    sdx : TranslationalStiffness
        Translational stiffness in the X direction.
    sdy : TranslationalStiffness
        Translational stiffness in the Y direction.
    sdz : TranslationalStiffness
        Translational stiffness in the Z direction.
    srx : RotationalStiffness
        Rotational stiffness about the X axis.
    sry : RotationalStiffness
        Rotational stiffness about the Y axis.
    srz : RotationalStiffness
        Rotational stiffness about the Z axis.
    """
    sdx: TranslationalStiffness = field(default_factory=TranslationalStiffness)
    sdy: TranslationalStiffness = field(default_factory=TranslationalStiffness)
    sdz: TranslationalStiffness = field(default_factory=TranslationalStiffness)
    srx: RotationalStiffness = field(default_factory=RotationalStiffness)
    sry: RotationalStiffness = field(default_factory=RotationalStiffness)
    srz: RotationalStiffness = field(default_factory=RotationalStiffness)

    def __repr__(self):
        """
        Returns a string representation of the SpringStiffness instance,
        Used by default for debug representation.
        """
        return f"SpringStiffness(sdx= {self.sdx}, sdy= {self.sdy}, sdz= {self.sdz}, srx= {self.srx}, sry= {self.sry}, srz= {self.srz})"

