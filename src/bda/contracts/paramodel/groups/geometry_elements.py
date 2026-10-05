from __future__ import annotations

from typing import List

from pydantic import BaseModel

from bda.contracts.shared import QuantityParaModel

# -------------------------
# Geometry elements
# -------------------------

class ParaNode(BaseModel):
    node_id: str
    x: QuantityParaModel
    y: QuantityParaModel
    z: QuantityParaModel


class ParaElement(BaseModel):
    element_id: str
    nodes: List[ParaNode]
