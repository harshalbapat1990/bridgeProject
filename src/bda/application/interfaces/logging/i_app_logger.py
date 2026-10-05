from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IAppLogger(ABC):
	@abstractmethod
	def debug(self, msg: str, *args: Any) -> None:
		...

	@abstractmethod
	def info(self, msg: str, *args: Any) -> None:
		...

	@abstractmethod
	def warning(self, msg: str, *args: Any) -> None:
		...

	@abstractmethod
	def error(self, msg: str, *args: Any) -> None:
		...


