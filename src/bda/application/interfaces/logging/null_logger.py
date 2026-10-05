from __future__ import annotations

from typing import Any

from bda.application.interfaces.logging.i_app_logger import IAppLogger


class NullLogger(IAppLogger):
	def debug(self, msg: str, *args: Any) -> None:
		return None

	def info(self, msg: str, *args: Any) -> None:
		return None

	def warning(self, msg: str, *args: Any) -> None:
		return None

	def error(self, msg: str, *args: Any) -> None:
		return None


