"""Interface for bridge type profiles.

A profile declares:
- the ``BridgeType`` it handles (``bridge_type`` class attribute),
- the ordered tuple of module classes (``module_types`` class attribute).

Concrete profiles can live in either ``modules_pre/a_bridge_profiles/`` or
``modules_post/a_profiles/`` and are discovered automatically by
``BridgeModuleFactory``.

Example::

    from bda.application.interfaces.module.i_profile import IProfile
    from bda.domain.enums import BridgeType
    from bda.application.interfaces.m1_materials.module_materials import MaterialsModule

    class SteelCompositeProfile(IProfile):
        bridge_type = BridgeType.STEEL_COMPOSITE
        module_types = (MaterialsModule,)
"""

from __future__ import annotations

from bda.domain.enums import BridgeType
from bda.application.interfaces.module.i_module import IModule
from bda.application.interfaces.module.i_module_post import IModulePost

ModuleType = type[IModule] | type[IModulePost]


class IProfile:
    """Base class for bridge-type profiles.

    Subclasses **must** set both class-level attributes:

    Attributes:
        bridge_type:  The :class:`~bda.domain.enums.BridgeType` this profile handles.
        module_types: Ordered tuple of module classes to run for a selected stage.
    """

    bridge_type: BridgeType
    module_types: tuple[ModuleType, ...]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        missing = [
            attr
            for attr in ("bridge_type", "module_types")
            if not hasattr(cls, attr)
        ]
        if missing:
            raise TypeError(
                f"Profile '{cls.__name__}' must define class attributes: {missing}"
            )


