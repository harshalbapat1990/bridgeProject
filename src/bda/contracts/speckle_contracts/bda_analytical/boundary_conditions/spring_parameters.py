from __future__ import annotations

from bda.contracts.paramodel.foundations.enums import DofTypeEnumParaModel
from bda.contracts.speckle_contracts.unit_parameters import ForcePerLengthParameter
from bda.contracts.speckle_contracts.unit_parameters import MomentParameter
from bda.contracts.speckle_contracts.base_objects import UnitlessParameter, ParameterGroup
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


def _dof_parameter(
    dof_type_value: DofTypeEnumParaModel,
    stiffness_value: float | None,
    isUser: bool,
    translational: bool,
    stiffness_unit: str,
):
    if dof_type_value == DofTypeEnumParaModel.FREE:
        if stiffness_value not in (None, 0.0):
            raise ValueError("Free spring stiffness must be 0.0.")
        dof_type = DofTypeParameter_Free(isUser=isUser)
        stiffness_type = (
            TranslationalSpringStiffnessParameter_Free
            if translational
            else RotationalSpringStiffnessParameter_Free
        )
        stiffness = stiffness_type(
            name="Stiffness",
            isUser=isUser,
            provided_unit=stiffness_unit,
        )
    elif dof_type_value == DofTypeEnumParaModel.FIXED:
        if stiffness_value not in (None, 10e10):
            raise ValueError("Fixed spring stiffness must be 10e10.")
        dof_type = DofTypeParameter_Fixed(isUser=isUser)
        stiffness_type = (
            TranslationalSpringStiffnessParameter_Fixed
            if translational
            else RotationalSpringStiffnessParameter_Fixed
        )
        stiffness = stiffness_type(
            name="Stiffness",
            isUser=isUser,
            provided_unit=stiffness_unit,
        )
    elif dof_type_value == DofTypeEnumParaModel.CUSTOM:
        if stiffness_value is None or stiffness_value <= 0:
            raise ValueError(
                "Custom spring stiffness must be greater than 0."
            )
        dof_type = DofTypeParameter_UserDefined(isUser=isUser)
        stiffness_type = (
            TranslationalSpringStiffnessParameter_UserDefined
            if translational
            else RotationalSpringStiffnessParameter_UserDefined
        )
        stiffness = stiffness_type(
            name="Stiffness",
            isUser=isUser,
            provided_unit=stiffness_unit,
            provided_value=stiffness_value,
        )
    else:
        raise ValueError(
            "Spring DOF type must be FREE, FIXED, or CUSTOM."
        )

    dof_payload = {
        "DOF Type": dof_type,
        "Stiffness": stiffness,
    }

    if translational:
        dof_model = {
            DofTypeEnumParaModel.FREE: TranslationalSpringDOFParameters_Free,
            DofTypeEnumParaModel.FIXED: TranslationalSpringDOFParameters_Fixed,
            DofTypeEnumParaModel.CUSTOM: TranslationalSpringDOFParameters_UserDefined,
        }[dof_type_value]
    else:
        dof_model = {
            DofTypeEnumParaModel.FREE: RotationalSpringDOFParameters_Free,
            DofTypeEnumParaModel.FIXED: RotationalSpringDOFParameters_Fixed,
            DofTypeEnumParaModel.CUSTOM: RotationalSpringDOFParameters_UserDefined,
        }[dof_type_value]

    return dof_model.model_validate(dof_payload)


class TranslationalSpringStiffnessParameter(
    ForcePerLengthParameter[float]
):
    pass

class TranslationalSpringStiffnessParameter_Fixed(TranslationalSpringStiffnessParameter):
    provided_value: float = 10e10

class TranslationalSpringStiffnessParameter_Free(TranslationalSpringStiffnessParameter):
    provided_value: float = 0.0

class TranslationalSpringStiffnessParameter_UserDefined(TranslationalSpringStiffnessParameter):
    provided_value:float = Field(ge=0.0)



class RotationalSpringStiffnessParameter(
    MomentParameter[float]
):
    pass

class RotationalSpringStiffnessParameter_Fixed(
    RotationalSpringStiffnessParameter
):
    provided_value: float = 10e10

class RotationalSpringStiffnessParameter_Free(
    RotationalSpringStiffnessParameter
):
    provided_value: float = 0.0

class RotationalSpringStiffnessParameter_UserDefined(
    RotationalSpringStiffnessParameter
):
    provided_value: float = Field(ge=0.0)


class DofTypeParameter(
    UnitlessParameter[
        DofTypeEnumParaModel
    ]
):
    name: Literal["DOF Type"] = "DOF Type"


class DofTypeParameter_Free(
    DofTypeParameter
    ):
    provided_value: DofTypeEnumParaModel = (
        DofTypeEnumParaModel.FREE
    )

class DofTypeParameter_Fixed(
    DofTypeParameter
):
    provided_value: DofTypeEnumParaModel = (
        DofTypeEnumParaModel.FIXED
    )

class DofTypeParameter_UserDefined(
    DofTypeParameter
):
    provided_value: DofTypeEnumParaModel = (
        DofTypeEnumParaModel.CUSTOM
    )


# class SDXParameter(
#     TranslationalSpringStiffnessParameter
# ):
#     name: Literal["SDX"] = "SDX"
#     description: Literal[
#         "Translational spring stiffness in the X direction"
#     ] = (
#         "Translational spring stiffness in the X direction"
#     )


# class SDYParameter(
#     TranslationalSpringStiffnessParameter
# ):
#     name: Literal["SDY"] = "SDY"
#     description: Literal[
#         "Translational spring stiffness in the Y direction"
#     ] = (
#         "Translational spring stiffness in the Y direction"
#     )


# class SDZParameter(
#     TranslationalSpringStiffnessParameter
# ):
#     name: Literal["SDZ"] = "SDZ"
#     description: Literal[
#         "Translational spring stiffness in the Z direction"
#     ] = (
#         "Translational spring stiffness in the Z direction"
#     )




class TranslationalSpringDOFParameters_Free(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )

    dof_type: DofTypeParameter_Free = Field(
        alias="DOF Type"
    )

    stiffness: (
        TranslationalSpringStiffnessParameter_Free
        | None
    ) = Field(
        default=None,
        alias="Stiffness"
    )
    @classmethod
    def create(
        cls,
        isUser:bool = True,
    ) -> "TranslationalSpringDOFParameters_Free":
        return cls.model_validate(
            {
                "DOF Type": DofTypeParameter_Free(isUser=isUser),
                "Stiffness": TranslationalSpringStiffnessParameter_Free(
                    name="Stiffness",
                    isUser=isUser,
                    provided_unit="kN/m",
                    base_unit="kN/m",
                )
            }
        )

class TranslationalSpringDOFParameters_Fixed(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )

    dof_type: DofTypeParameter_Fixed = Field(
        alias="DOF Type"
    )

    stiffness: (
        TranslationalSpringStiffnessParameter_Fixed
        | None
    ) = Field(
        default=None,
        alias="Stiffness"
    )
    @classmethod
    def create(
        cls,
        isUser:bool = True,
    ) -> "TranslationalSpringDOFParameters_Fixed":
        return cls.model_validate(
            {
                "DOF Type": DofTypeParameter_Fixed(isUser=isUser),
                "Stiffness": TranslationalSpringStiffnessParameter_Fixed(
                    name="Stiffness",
                    isUser=isUser,
                    provided_unit="kN/m",
                    base_unit="kN/m",
                )
            }
        )

class TranslationalSpringDOFParameters_UserDefined(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )

    dof_type: DofTypeParameter_UserDefined = Field(
        alias="DOF Type"
    )

    stiffness: (
        TranslationalSpringStiffnessParameter_UserDefined
        | None
    ) = Field(
        default=None,
        alias="Stiffness"
    )
    @classmethod
    def create(
        cls,
        stiffness:float,
        isUser:bool = True,
        stiffness_unit: str = "kN/m",
    ) -> "TranslationalSpringDOFParameters_UserDefined":
        return cls.model_validate(
            {
                "DOF Type": DofTypeParameter_UserDefined(isUser=isUser),
                "Stiffness": TranslationalSpringStiffnessParameter_UserDefined(
                    name="Stiffness",
                    isUser=isUser,
                    provided_unit=stiffness_unit,
                    provided_value=stiffness
                )
            }
        )

_TranslationalSpringDOFParameters = (
    TranslationalSpringDOFParameters_Free
    | TranslationalSpringDOFParameters_Fixed
    | TranslationalSpringDOFParameters_UserDefined
)


class SDXParameterGroup(
    ParameterGroup
):
    name: Literal["SDX"] = "SDX"
    description: Literal[
        "Translational spring stiffness in the X direction"
    ] = (
        "Translational spring stiffness in the X direction"
    )
    group_parameters: (
        _TranslationalSpringDOFParameters
    )

class SDYParameterGroup(
    ParameterGroup
):
    name: Literal["SDY"] = "SDY"
    description: Literal[
        "Translational spring stiffness in the Y direction"
    ] = (
        "Translational spring stiffness in the Y direction"
    )
    group_parameters: (
        _TranslationalSpringDOFParameters
    )

class SDZParameterGroup(
    ParameterGroup
):
    name: Literal["SDZ"] = "SDZ"
    description: Literal[
        "Translational spring stiffness in the Z direction"
    ] = (
        "Translational spring stiffness in the Z direction"
    )
    group_parameters: (
        _TranslationalSpringDOFParameters
    )

class RotationalSpringDOFParameters_Free(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )

    dof_type: DofTypeParameter_Free = Field(
        alias="DOF Type"
    )

    stiffness: (
        RotationalSpringStiffnessParameter_Free
        | None
    ) = Field(
        default=None,
        alias="Stiffness"
    )
    @classmethod
    def create(
        cls,
        isUser:bool = True,
    ) -> "RotationalSpringDOFParameters_Free":
        return cls.model_validate(
            {
                "DOF Type": DofTypeParameter_Free(isUser=isUser),
                "Stiffness": RotationalSpringStiffnessParameter_Free(
                    name="Stiffness",
                    isUser=isUser,
                    provided_unit="kN*m",
                )
            }
        )

class RotationalSpringDOFParameters_Fixed(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )

    dof_type: DofTypeParameter_Fixed = Field(
        alias="DOF Type"
    )

    stiffness: (
        RotationalSpringStiffnessParameter_Fixed
        | None
    ) = Field(
        default=None,
        alias="Stiffness"
    )
    @classmethod
    def create(
        cls,
        isUser:bool = True,
    ) -> "RotationalSpringDOFParameters_Fixed":
        return cls.model_validate(
            {
                "DOF Type": DofTypeParameter_Fixed(isUser=isUser),
                "Stiffness": RotationalSpringStiffnessParameter_Fixed(
                    name="Stiffness",
                    isUser=isUser,
                    provided_unit="kN*m",
                )
            }
        )

class RotationalSpringDOFParameters_UserDefined(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )

    dof_type: DofTypeParameter_UserDefined = Field(
        alias="DOF Type"
    )

    stiffness: (
        RotationalSpringStiffnessParameter_UserDefined
        | None
    ) = Field(
        default=None,
        alias="Stiffness"
    )
    @classmethod
    def create(
        cls,
        stiffness:float,
        isUser:bool = True,
        stiffness_unit: str = "kN*m",
    ) -> "RotationalSpringDOFParameters_UserDefined":
        return cls.model_validate(
            {
                "DOF Type": DofTypeParameter_UserDefined(isUser=isUser),
                "Stiffness": RotationalSpringStiffnessParameter_UserDefined(
                    name="Stiffness",
                    isUser=isUser,
                    provided_unit=stiffness_unit,
                    provided_value=stiffness
                )
            }
        )

_RotationalSpringDOFParameters = (
    RotationalSpringDOFParameters_Free
    | RotationalSpringDOFParameters_Fixed
    | RotationalSpringDOFParameters_UserDefined
)

class SRXParameter(
    ParameterGroup
):
    name: Literal["SRX"] = "SRX"
    description: Literal[
        "Rotational spring stiffness about the X axis"
    ] = (
        "Rotational spring stiffness about the X axis"
    )
    group_parameters: (
            _RotationalSpringDOFParameters
        )


class SRYParameter(
    ParameterGroup
):
    name: Literal["SRY"] = "SRY"
    description: Literal[
        "Rotational spring stiffness about the Y axis"
    ] = (
        "Rotational spring stiffness about the Y axis"
    )
    group_parameters: (
                _RotationalSpringDOFParameters
            )


class SRZParameter(
    ParameterGroup
):
    name: Literal["SRZ"] = "SRZ"
    description: Literal[
        "Rotational spring stiffness about the Z axis"
    ] = (
        "Rotational spring stiffness about the Z axis"
    )
    group_parameters: (
                _RotationalSpringDOFParameters
            )


class BoundaryConditionSpringParameters_Translational(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )

    sdx: SDXParameterGroup = Field(
        alias="SDX"
    )

    sdy: SDYParameterGroup = Field(
        alias="SDY"
    )

    sdz: SDZParameterGroup = Field(
        alias="SDZ"
    )

class BoundaryConditionSpringParameters_Rotational(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )

    sdx: SDXParameterGroup = Field(
        alias="SDX"
    )

    sdy: SDYParameterGroup = Field(
        alias="SDY"
    )

    sdz: SDZParameterGroup = Field(
        alias="SDZ"
    )

    srx: SRXParameter = Field(
        alias="SRX"
    )

    sry: SRYParameter = Field(
        alias="SRY"
    )

    srz: SRZParameter = Field(
        alias="SRZ"
    )

class BoundaryConditionTranslationalSpringParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Boundary Condition Translational Spring Definition"
    ] = "Boundary Condition Translational Spring Definition"

    description: Literal[
        "Parameters defining the translational spring stiffnesses for a boundary condition with no rotational spring stiffnesses."
    ] = (
        "Parameters defining the translational spring stiffnesses for a boundary condition with no rotational spring stiffnesses."
    )

    group_parameters: (
        BoundaryConditionSpringParameters_Translational
    )

    @classmethod
    def create(
        cls,
        sdx_dof_type: DofTypeEnumParaModel = DofTypeEnumParaModel.FREE,
        sdx_stiffness: float | None = None,
        sdy_dof_type: DofTypeEnumParaModel = DofTypeEnumParaModel.FREE,
        sdy_stiffness: float | None = None,
        sdz_dof_type: DofTypeEnumParaModel = DofTypeEnumParaModel.FREE,
        sdz_stiffness: float | None = None,
        isUser: bool = True,
        stiffness_unit: str = "kN/m",
    ) -> "BoundaryConditionTranslationalSpringParameterGroup":
        return cls(
            name=cls.model_fields["name"].default,
            isUser=isUser,
            group_parameters=BoundaryConditionSpringParameters_Translational(
                SDX=SDXParameterGroup(
                    name="SDX",
                    isUser=isUser,
                    group_parameters=_dof_parameter(
                        sdx_dof_type, sdx_stiffness, isUser, True, stiffness_unit
                    ),
                ),
                SDY=SDYParameterGroup(
                    name="SDY",
                    isUser=isUser,
                    group_parameters=_dof_parameter(
                        sdy_dof_type, sdy_stiffness, isUser, True, stiffness_unit
                    ),
                ),
                SDZ=SDZParameterGroup(
                    name="SDZ",
                    isUser=isUser,
                    group_parameters=_dof_parameter(
                        sdz_dof_type, sdz_stiffness, isUser, True, stiffness_unit
                    ),
                ),
            ),
        )

class BoundaryConditionSpringParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Boundary Condition Spring Definition"
    ] = "Boundary Condition Spring Definition"

    description: Literal[
            "Parameters defining the translational and rotational spring stiffnesses for a boundary condition with no rotational spring stiffnesses."
        ] = (
            "Parameters defining the translational and rotational spring stiffnesses for a boundary condition with no rotational spring stiffnesses."
        )

    group_parameters: (
        BoundaryConditionSpringParameters_Rotational
    )

    @classmethod
    def create(
        cls,
        sdx_dof_type: DofTypeEnumParaModel = DofTypeEnumParaModel.FREE,
        sdx_stiffness: float | None = None,
        sdy_dof_type: DofTypeEnumParaModel = DofTypeEnumParaModel.FREE,
        sdy_stiffness: float | None = None,
        sdz_dof_type: DofTypeEnumParaModel = DofTypeEnumParaModel.FREE,
        sdz_stiffness: float | None = None,
        srx_dof_type: DofTypeEnumParaModel = DofTypeEnumParaModel.FREE,
        srx_stiffness: float | None = None,
        sry_dof_type: DofTypeEnumParaModel = DofTypeEnumParaModel.FREE,
        sry_stiffness: float | None = None,
        srz_dof_type: DofTypeEnumParaModel = DofTypeEnumParaModel.FREE,
        srz_stiffness: float | None = None,
        isUser: bool = True,
        translational_unit: str = "kN/m",
        rotational_unit: str = "kN*m",
    ) -> "BoundaryConditionSpringParameterGroup":
        return cls(
            name=cls.model_fields["name"].default,
            isUser=isUser,
            group_parameters=BoundaryConditionSpringParameters_Rotational(
                SDX=SDXParameterGroup(
                    name="SDX",
                    isUser=isUser,
                    group_parameters=_dof_parameter(
                        sdx_dof_type, sdx_stiffness, isUser, True, translational_unit
                    ),
                ),
                SDY=SDYParameterGroup(
                    name="SDY",
                    isUser=isUser,
                    group_parameters=_dof_parameter(
                        sdy_dof_type, sdy_stiffness, isUser, True, translational_unit
                    ),
                ),
                SDZ=SDZParameterGroup(
                    name="SDZ",
                    isUser=isUser,
                    group_parameters=_dof_parameter(
                        sdz_dof_type, sdz_stiffness, isUser, True, translational_unit
                    ),
                ),
                SRX=SRXParameter(
                    name="SRX",
                    isUser=isUser,
                    group_parameters=_dof_parameter(
                        srx_dof_type, srx_stiffness, isUser, False, rotational_unit
                    ),
                ),
                SRY=SRYParameter(
                    name="SRY",
                    isUser=isUser,
                    group_parameters=_dof_parameter(
                        sry_dof_type, sry_stiffness, isUser, False, rotational_unit
                    ),
                ),
                SRZ=SRZParameter(
                    name="SRZ",
                    isUser=isUser,
                    group_parameters=_dof_parameter(
                        srz_dof_type, srz_stiffness, isUser, False, rotational_unit
                    ),
                ),
            ),
        )

if __name__ == "__main__":
    import json

    def show_example(title: str, value) -> None:
        print(f"\n{title}\n{'-' * len(title)}")
        print(
            json.dumps(
                value.model_dump(mode="json", by_alias=True),
                indent=2,
            )
        )

    show_example(
        "Individual translational DOF variants",
        TranslationalSpringDOFParameters_Free.create(),
    )
    show_example(
        "Individual translational fixed variant",
        TranslationalSpringDOFParameters_Fixed.create(),
    )
    show_example(
        "Individual translational custom variant",
        TranslationalSpringDOFParameters_UserDefined.create(
            stiffness=1000.0
        ),
    )

    show_example(
        "Individual rotational free variant",
        RotationalSpringDOFParameters_Free.create(),
    )
    show_example(
        "Individual rotational fixed variant",
        RotationalSpringDOFParameters_Fixed.create(),
    )
    show_example(
        "Individual rotational custom variant",
        RotationalSpringDOFParameters_UserDefined.create(
            stiffness=1000.0
        ),
    )

    show_example(
        "Translational spring group: free, fixed, and custom",
        BoundaryConditionTranslationalSpringParameterGroup.create(
            sdx_dof_type=DofTypeEnumParaModel.FREE,
            sdy_dof_type=DofTypeEnumParaModel.FIXED,
            sdz_dof_type=DofTypeEnumParaModel.CUSTOM,
            sdz_stiffness=1000.0,
        ),
    )

    show_example(
        "Full spring group: all six DOFs and all supported DOF types",
        BoundaryConditionSpringParameterGroup.create(
            sdx_dof_type=DofTypeEnumParaModel.FREE,
            sdy_dof_type=DofTypeEnumParaModel.FIXED,
            sdz_dof_type=DofTypeEnumParaModel.CUSTOM,
            sdz_stiffness=1000.0,
            srx_dof_type=DofTypeEnumParaModel.FIXED,
            sry_dof_type=DofTypeEnumParaModel.CUSTOM,
            sry_stiffness=250.0,
            srz_dof_type=DofTypeEnumParaModel.FREE,
        ),
    )