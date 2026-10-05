"""
UUID helpers shared across all mappers.
"""
from __future__ import annotations

import uuid
from typing import Union


def to_uuid(raw: Union[str, int, uuid.UUID]) -> uuid.UUID:
    """Normalise guid from any accepted source type to ``uuid.UUID``.

    * ``str``        → ``uuid.UUID(raw)`` or uuid5(raw) if failed to parse
    * ``int``        → ``uuid.UUID(int=raw)``
    * ``uuid.UUID``  → returned as-is
    """
    if isinstance(raw, str):
        try:
            return uuid.UUID(raw)
        except:
            return uuid.uuid5(uuid.NAMESPACE_DNS, raw)
    if isinstance(raw, int):
        return uuid.UUID(int=raw)
    return raw

