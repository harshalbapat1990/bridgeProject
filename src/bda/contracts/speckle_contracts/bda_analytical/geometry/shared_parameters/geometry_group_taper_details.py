from typing import Literal

from pydantic import BaseModel, Field

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup,
    UnitlessParameter
)
from bda.contracts.speckle_contracts.unit_parameters import LengthParameter

# =============================================================================
# TAPERED DETAIL PARAMETER GROUPS
# ============================================================================

class TaperedSectionIdParameter(UnitlessParameter[str]):
    name: Literal["Section ID"] = "Section ID"

    description: Literal[
        "Section identifier for tapered segment"
    ] = "Section identifier for tapered segment"

    symbol: None = None

    provided_value: str


class TaperDetailsXStartParameter(LengthParameter):
    name: Literal["Taper X Start"] = "Taper X Start"

    description: Literal[
        "Start x-coordinate of taper"
    ] = "Start x-coordinate of taper"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class TaperDetailsXEndParameter(LengthParameter):
    name: Literal[
        "Taper X End"
    ] = "Taper X End"

    description: Literal[
        "End x-coordinate of taper"
    ] = "End x-coordinate of taper"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class TaperedDetailsGroupParameters(BaseModel):
    x_start: TaperDetailsXStartParameter = Field(
        alias="Taper X Start"
    )

    x_end: TaperDetailsXEndParameter = Field(
        alias="Taper X End"
    )

    section_id: TaperedSectionIdParameter = Field(
        alias="Section ID"
    )


class TaperedDetailParameterGroup(ParameterGroup):
    name: Literal["Tapered Detail"] = "Tapered Detail"

    description: Literal[
        "Tapered segment details"
    ] = "Tapered segment details"

    symbol: None = None

    group_parameters: TaperedDetailsGroupParameters

    @classmethod
    def create(
        cls,
        x_start: float,
        x_end: float,
        section_id: str,
        x_start_unit: Literal["m", "ft"] = "m",
        x_end_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "TaperedDetailParameterGroup":

        return cls(
            isUser=isUser,
            group_parameters=TaperedDetailsGroupParameters(
                **{
                    "Taper X Start":
                        TaperDetailsXStartParameter(
                            isUser=isUser,
                            provided_value=x_start,
                            provided_unit=x_start_unit,
                            base_value=x_start,
                        ),

                    "Taper X End":
                        TaperDetailsXEndParameter(
                            isUser=isUser,
                            provided_value=x_end,
                            provided_unit=x_end_unit,
                            base_value=x_end,
                        ),

                    "Section ID":
                        TaperedSectionIdParameter(
                            isUser=isUser,
                            provided_value=section_id,
                        ),
                }
            ),
        )


class TaperedDetailsParameterGroup(ParameterGroup):
    name: Literal["Tapered Details"] = "Tapered Details"

    description: Literal[
        "Tapered details along the span"
    ] = "Tapered details along the span"

    symbol: None = None

    group_parameters: dict[
        str,
        TaperedDetailParameterGroup,
    ] = Field(
        ...,
        min_length=1,
    )

    @classmethod
    def create(
        cls,
        tapers: list[tuple[float, float, str]],
        taper_units: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "TaperedDetailsParameterGroup":

        return cls(
            isUser=isUser,
            group_parameters={
                f"Taper {i+1}":
                    TaperedDetailParameterGroup.create(
                        isUser=isUser,
                        x_start=x_start,
                        x_end=x_end,
                        section_id=section_id,
                        x_start_unit=taper_units,
                        x_end_unit=taper_units,
                    )
                for i, (x_start, x_end, section_id)
                in enumerate(tapers)
            }
        )

