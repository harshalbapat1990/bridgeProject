from bda.application.interfaces.module.i_profile import IProfile
from bda.domain.enums import BridgeType
from bda.modules_pre.m1_materials.module_materials import MaterialsModule
from bda.modules_pre.m2_sections.module_sections import SectionsModule
from bda.modules_pre.m3_geometry.module_geometry_steel_composite import GeometrySteelCompositeModule


class SteelCompositeProfile(IProfile):
    """Pre-processing pipeline for steel composite bridges."""

    bridge_type = BridgeType.STEEL_COMPOSITE
    module_types = (MaterialsModule, SectionsModule)
