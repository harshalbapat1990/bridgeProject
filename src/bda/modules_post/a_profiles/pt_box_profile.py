from bda.application.interfaces.module.i_profile import IProfile
from bda.domain.enums import BridgeType
from bda.modules_post.coordination_modules.pt_box.pt_box_girder_coordination import PTBoxGirderCoordination


class PTBoxProfile(IProfile):
    """Pre-processing pipeline for PSC box girder bridges."""

    bridge_type = BridgeType.PSC_BOX
    

    module_types = (PTBoxGirderCoordination)
