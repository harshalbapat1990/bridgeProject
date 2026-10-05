from dataclasses import dataclass, field

from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.loads.load_base import LoadBase


@dataclass(kw_only=True, frozen=True)
class SelfWeightFactors:
    """
    Directional self-weight multipliers applied in the
    global coordinate system.

    The components define the direction and magnitude
    of gravity load generation.

    Examples
    --------
    Standard gravity acting in global Z:

        SelfWeightFactor(z=-1.0)

    Reversed gravity:

        SelfWeightFactor(z=1.0)

    Gravity acting in global Y:

        SelfWeightFactor(y=-1.0)
    """
    x: float = field(default=0.0)
    y: float = field(default=0.0)
    z: float = field(default=-1.0)

@dataclass
class SelfWeightLoad(LoadBase):
    element: Element1D
    self_weight_factors: SelfWeightFactors = field(default_factory=SelfWeightFactors)

    @property
    def target(self) ->  Element1D:
        """Return the analytical object this load acts on."""
        return self.element