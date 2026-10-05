"""BridgeModuleFactory — auto-discovers IProfile subclasses from stage profiles.

Depending on the selected processing stage (``pre`` or ``post``), discovery
imports every ``*.py`` module inside either:

- ``modules_pre/a_bridge_profiles/``
- ``modules_post/a_profiles/``

Any class that inherits from ``IProfile`` and declares ``bridge_type`` +
``module_types`` is registered automatically.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Sequence

from bda.application.interfaces.module.i_profile import IProfile, ModuleType
from bda.domain.enums import BridgeType, ProcessingStage

_PROFILE_SOURCES: dict[ProcessingStage, tuple[str, Path]] = {
    ProcessingStage.PRE: (
        "bda.modules_pre.a_bridge_profiles",
        Path(__file__).resolve().parents[1] / "modules_pre" / "a_bridge_profiles",
    ),
    ProcessingStage.POST: (
        "bda.modules_post.a_profiles",
        Path(__file__).resolve().parents[1] / "modules_post" / "a_profiles",
    ),
}


@dataclass(frozen=True)
class BridgeModuleConfig:
    """Configuration for a single bridge type processing pipeline."""

    module_types: tuple[ModuleType, ...]
    profile_class: type[IProfile]


class BridgeModuleFactory:
    """Central registry for bridge-type-specific module configurations.

    Populated automatically by :meth:`initialize` which scans the selected
    stage package for :class:`~bda.application.interfaces.module.i_profile.IProfile`
    subclasses.
    """

    _configs: ClassVar[dict[ProcessingStage, dict[BridgeType, BridgeModuleConfig]]] = {
        ProcessingStage.PRE: {},
        ProcessingStage.POST: {},
    }

    @staticmethod
    def _coerce_stage(stage: ProcessingStage | str) -> ProcessingStage:
        if isinstance(stage, ProcessingStage):
            return stage

        try:
            return ProcessingStage(stage.lower())
        except ValueError as exc:
            supported = ", ".join(member.value for member in ProcessingStage)
            raise ValueError(
                f"Unsupported processing stage: '{stage}'. Supported: {supported}"
            ) from exc

    @classmethod
    def initialize(cls, stage: ProcessingStage | str = ProcessingStage.PRE) -> None:
        """Discover and register all profiles for the selected stage."""
        stage = cls._coerce_stage(stage)
        if cls._configs[stage]:
            return

        cls._discover_profiles(stage)

    @classmethod
    def _discover_profiles(cls, stage: ProcessingStage) -> None:
        """Import every module in the selected stage package and register profiles."""
        profiles_package, profiles_path = _PROFILE_SOURCES[stage]
        if not profiles_path.exists():
            return

        for module_info in pkgutil.iter_modules([str(profiles_path)]):
            full_name = f"{profiles_package}.{module_info.name}"
            imported = importlib.import_module(full_name)

            for attr_name in dir(imported):
                obj = getattr(imported, attr_name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, IProfile)
                    and obj is not IProfile
                    and hasattr(obj, "bridge_type")
                    and hasattr(obj, "module_types")
                ):
                    cls._register_profile(stage, obj)

    @classmethod
    def _register_profile(
        cls,
        stage: ProcessingStage,
        profile_cls: type[IProfile],
    ) -> None:
        bridge_type: BridgeType = profile_cls.bridge_type
        cls._configs[stage][bridge_type] = BridgeModuleConfig(
            module_types=tuple(profile_cls.module_types),
            profile_class=profile_cls,
        )

    @classmethod
    def register_config(
        cls,
        bridge_type: BridgeType,
        config: BridgeModuleConfig,
        stage: ProcessingStage | str = ProcessingStage.PRE,
    ) -> None:
        """Manually register or override a config (useful in tests)."""
        stage = cls._coerce_stage(stage)
        cls.initialize(stage)
        cls._configs[stage][bridge_type] = config

    @classmethod
    def get_config(
        cls,
        bridge_type: BridgeType,
        stage: ProcessingStage | str = ProcessingStage.PRE,
    ) -> BridgeModuleConfig:
        stage = cls._coerce_stage(stage)
        cls.initialize(stage)
        try:
            return cls._configs[stage][bridge_type]
        except KeyError as exc:
            supported = ", ".join(sorted(bt.value for bt in cls._configs[stage]))
            raise ValueError(
                f"Unsupported bridge type: '{bridge_type}' for stage '{stage.value}'. "
                f"Supported: {supported}"
            ) from exc

    @classmethod
    def get_module_types(
        cls,
        bridge_type: BridgeType,
        stage: ProcessingStage | str = ProcessingStage.PRE,
    ) -> Sequence[ModuleType]:
        return cls.get_config(bridge_type, stage).module_types

    @classmethod
    def registered_bridge_types(
        cls,
        stage: ProcessingStage | str = ProcessingStage.PRE,
    ) -> Sequence[BridgeType]:
        """Return all currently registered bridge types for the selected stage."""
        stage = cls._coerce_stage(stage)
        cls.initialize(stage)
        return list(cls._configs[stage].keys())

    @classmethod
    def _reset(cls, stage: ProcessingStage | str | None = None) -> None:
        """Clear the registry for one stage or for all stages (for tests only)."""
        if stage is None:
            cls._configs = {
                ProcessingStage.PRE: {},
                ProcessingStage.POST: {},
            }
            return

        stage = cls._coerce_stage(stage)
        cls._configs[stage] = {}

