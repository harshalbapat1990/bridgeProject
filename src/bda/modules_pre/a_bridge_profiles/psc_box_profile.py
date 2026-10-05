from bda.application.interfaces.module.i_profile import IProfile
from bda.domain.enums import BridgeType
from bda.modules_pre.m1_materials.module_materials import MaterialsModule
from bda.modules_pre.m2_sections.module_sections import SectionsModule
from bda.modules_pre.m3_geometry.module_geometry_psc_box import GeometryPSCBoxModule
from bda.modules_pre.m4_foundations.module_foundations import FoundationsBCsModule
from bda.modules_pre.m5_bearings.module_bearings import BearingsBCsModule


class PTBoxProfile(IProfile):
    """Pre-processing pipeline for PT box girder bridges."""

    bridge_type = BridgeType.PSC_BOX
    module_types = (MaterialsModule,
                    SectionsModule,
                    GeometryPSCBoxModule,
                    FoundationsBCsModule,
                    BearingsBCsModule)
