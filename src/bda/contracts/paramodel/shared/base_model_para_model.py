from pydantic import BaseModel


class BaseModelParaModel(BaseModel):
    model_config = {
    "frozen": True,
    "extra": "allow",
    "populate_by_name": True,
    }