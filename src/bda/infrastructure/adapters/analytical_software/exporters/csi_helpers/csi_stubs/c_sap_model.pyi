from typing import TypeAlias

from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.csi_stubs.definitions.group.c_group_def import \
    cGroupDef
from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.csi_stubs.object.frame.c_frame_obj import \
    cFrameObj
from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.csi_stubs.object.link.c_link_obj import \
    cLinkObj
from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.csi_stubs.object.point.c_point_obj import \
    cPointObj
from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.csi_stubs.definitions.properties.c_prop_link import \
    cPropLink

# ============================================================================
# COMMON TYPES
# ============================================================================

DofVector: TypeAlias = tuple[
    bool, bool, bool, bool, bool, bool
]
"""
Degrees of freedom vector.

Order:
(U1, U2, U3, R1, R2, R3)

Where:
- U1, U2, U3 are translational degrees of freedom
- R1, R2, R3 are rotational degrees of freedom
"""

FixityVector: TypeAlias = tuple[
    bool, bool, bool, bool, bool, bool
]
"""
Fixity or release state for each degree of freedom.

Order:
(U1, U2, U3, R1, R2, R3)

Meaning:
- True  = restrained/fixed
- False = free
"""

LinearLinkStiffnessVector: TypeAlias = tuple[
    float, float, float, float, float, float
]
"""
Linear link stiffness values.

Order:
(U1, U2, U3, R1, R2, R3)

Units:
- U1, U2, U3 : force / length
- R1, R2, R3 : force * length / radian
"""

LinearLinkDampingVector: TypeAlias = tuple[
    float, float, float, float, float, float
]
"""
Linear link damping coefficients.

Order:
(U1, U2, U3, R1, R2, R3)

Units depend on the active CSI model units.
"""

# ============================================================================
# SAP MODEL
# ============================================================================

class cSapModel:
    """
    Root CSI SAP2000/CSiBridge model object.

    Provides access to object collections, property definitions
    and model management functions exposed by the CSI API.
    """
    PropLink: cPropLink
    LinkObj: cLinkObj
    PointObj: cPointObj
    FrameObj: cFrameObj
    GroupDef: cGroupDef