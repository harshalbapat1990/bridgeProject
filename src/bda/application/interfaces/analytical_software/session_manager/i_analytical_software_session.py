"""Interface for external analytical software runtime session_managers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class IAnalyticalSoftwareSession(ABC):
    """Represents an active (or activatable) connection to analysis software."""

    @property
    @abstractmethod
    def software_name(self) -> str:
        """Human-readable software name."""
        ...

    @abstractmethod
    def open_session(
        self,
        create_new_instance: bool,
        template_file_path: Optional[str],
    ) -> bool:
        """Open or attach to a software session."""
        ...

    @abstractmethod
    def close_session(self) -> None:
        """Close and release session resources owned by this object."""
        ...

    @abstractmethod
    def open_file(self, path: str) -> bool:
        """Open a model file in the active session."""
        ...

    @abstractmethod
    def save_model(self) -> bool:
        """Save the current model in the active session."""
        ...

    @abstractmethod
    def save_model_as(self, path: Path) -> bool:
        """Save the current model in the active session as new file."""
        ...

    @abstractmethod
    def has_analysis_results(self) -> bool:
        """Return True if the open model has at least one set of analysis results.

        Implementations should probe the software without raising — return
        False for any failure so the caller can treat it as "not yet analyzed".
        """
        ...