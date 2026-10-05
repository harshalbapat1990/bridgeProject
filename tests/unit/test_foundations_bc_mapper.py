"""Unit tests for FoundationMapper (foundation para models -> domain models).

The mapper is exercised in isolation: para models are built in-memory instead of
being read through a data provider, so a failure here always points at the
mapping logic and never at fixture parsing. Raw-dict cases go through
``model_validate`` on purpose, to cover the discriminated unions the mapper
relies on for dispatch.
"""

from __future__ import annotations

import pytest

from bda.application.mapping.foundation_conditions import foundation_mapper
from bda.application.mapping.foundation_conditions.foundation_mapper import FoundationMapper
from bda.contracts.paramodel.foundations.enums import (
    DofTypeEnumParaModel,
    FoundationApplicationTypeEnumParaModel,
    FoundationModelTypeParaModel,
    SoilProfileTypeEnumParaModel,
)
from bda.contracts.paramodel.foundations.foundation_bc_para_model import (
    BearingBasedFoundationApplicationParaModel,
    FoundationApplicationBaseParaModel,
    LumpedFoundationBCsParaModel,
    NodeSpringStiffnessParaModel,
    PileInteractionFoundationBCsParaModel,
    PileNodeSpringStiffnessParaModel,
    PileStiffnessUniformDatasetParaModel,
    SubstructureElementBasedFoundationApplicationParaModel, TranslationalStiffnessParaModel,
)
from bda.contracts.paramodel.groups import ElementOrientationParaModel
from bda.contracts.shared import QuantityParaModel
from bda.domain.models.submodels.boundary_conditions.enums import (
    DofTypeEnum,
    FoundationApplicationType,
    FoundationModelType,
    SoilProfileType,
)
from bda.domain.models.submodels.boundary_conditions.foundations import (
    BearingBasedFoundationApplication,
    LumpedFoundationBCs,
    NodeSpringStiffness,
    PileInteractionFoundationBCs,
    PileNodeSpringStiffness,
    PileStiffnessUniformDataset,
    SubstructureElementBasedFoundationApplication,
)
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import SpringStiffnessBase, TranslationalStiffness
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation
from bda.domain.units.registry import ureg

# Default injected by BearingBasedFoundationApplicationParaModel.
DEFAULT_VERTICAL_OFFSET = (0.1, "m")


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def assert_quantity(actual, value: float, unit: str) -> None:
    """Assert a mapped pint Quantity carries the expected magnitude and unit."""
    assert actual is not None
    assert actual.magnitude == pytest.approx(value)
    assert actual.units == ureg.Unit(unit)


def assert_dof(actual: SpringStiffnessBase, dof_type: DofTypeEnum, quantity: tuple[float, str] | None) -> None:
    assert isinstance(actual, SpringStiffnessBase)
    assert actual.dof_type == dof_type
    if quantity is None:
        assert actual.stiffness is None
    else:
        assert_quantity(actual.stiffness, *quantity)


# ---------------------------------------------------------------------------
# Para model factories
# ---------------------------------------------------------------------------


def quantity(value: float, unit: str) -> QuantityParaModel:
    return QuantityParaModel(value=value, unit=unit)


def dof(dof_type: str, value: float | None = None, unit: str = "N/m") -> dict:
    """DOF payload; omitting the value leaves the optional stiffness unset."""
    if value is None:
        return {"dof_type": dof_type}
    return {"dof_type": dof_type, "stiffness": {"value": value, "unit": unit}}


def make_node_spring(**overrides) -> NodeSpringStiffnessParaModel:
    """Full 6-DOF spring covering every DOF type once per direction group."""
    payload = {
        "sdx": dof("custom", 1_000_000),
        "sdy": dof("fixed", 2_000_000),
        "sdz": dof("free"),
        "srx": dof("custom", 4_000_000, "N*m/rad"),
        "sry": dof("fixed", 5_000_000, "N*m/rad"),
        "srz": dof("free"),
    }
    payload.update(overrides)
    return NodeSpringStiffnessParaModel(**payload)


def make_pile_node(sdx: float = 1_000_000) -> PileNodeSpringStiffnessParaModel:
    return PileNodeSpringStiffnessParaModel(
        sdx=TranslationalStiffnessParaModel(** dof("custom", sdx)),
        sdy=TranslationalStiffnessParaModel(** dof("fixed", 2_000_000)),
        sdz=TranslationalStiffnessParaModel(** dof("free")),
    )


def make_lumped(
    support_index: int = 0,
    orientation: ElementOrientationParaModel = ElementOrientationParaModel.ORTHOGONAL,
    application: FoundationApplicationBaseParaModel | None = None,
    stiffness_definition: NodeSpringStiffnessParaModel | None = None,
) -> LumpedFoundationBCsParaModel:
    return LumpedFoundationBCsParaModel(
        foundation_model_type=FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL,
        support_index=support_index,
        stiffness_definition=stiffness_definition if stiffness_definition is not None else make_node_spring(),
        orientation=orientation,
        application=application if application is not None else BearingBasedFoundationApplicationParaModel(
            application_type=FoundationApplicationTypeEnumParaModel.BEARING_BASED,
            vertical_offset=quantity(0.5, "m"),
        ),
    )


def make_pile_dataset(
    pile_index: int = 0,
    intermediate_nodes: PileNodeSpringStiffnessParaModel | None = None,
) -> PileStiffnessUniformDatasetParaModel:
    return PileStiffnessUniformDatasetParaModel(
        soil_profile_type=SoilProfileTypeEnumParaModel.UNIFORM,
        pile_index=pile_index,
        top_node=make_pile_node(1_000_000),
        bottom_node=make_pile_node(2_000_000),
        intermediate_nodes=intermediate_nodes or make_pile_node(3_000_000),
    )


def make_pile_interaction(
    support_index: int = 2,
    pile_springs: list[PileStiffnessUniformDatasetParaModel] | None = None,
) -> PileInteractionFoundationBCsParaModel:
    return PileInteractionFoundationBCsParaModel(
        foundation_model_type=FoundationModelTypeParaModel.PILE_INTERACTION_MODEL,
        support_index=support_index,
        pile_springs=pile_springs if pile_springs is not None else [make_pile_dataset()],
    )


class TestLumpedFoundationMapping:
    """LumpedFoundationBCsParaModel -> LumpedFoundationBCs."""

    @pytest.fixture
    def para(self) -> LumpedFoundationBCsParaModel:
        return make_lumped(support_index=3)

    @pytest.fixture
    def domain(self, para) -> LumpedFoundationBCs:
        return FoundationMapper.to_domain([para])[0]

    def test_maps_to_lumped_domain_type(self, domain):
        assert isinstance(domain, LumpedFoundationBCs)

    def test_support_index_is_copied(self, domain):
        assert domain.support_index == 3

    def test_foundation_model_type_is_lumped(self, domain):
        assert domain.foundation_model_type == FoundationModelType.LUMPED_FOUNDATION_MODEL

    @pytest.mark.parametrize(
        ("para_orientation", "expected"),
        [
            (ElementOrientationParaModel.ORTHOGONAL, ElementOrientation.ORTHOGONAL),
            (ElementOrientationParaModel.SKEWED, ElementOrientation.SKEWED),
        ],
    )
    def test_orientation_is_mapped(self, para_orientation, expected):
        domain = FoundationMapper.to_domain([make_lumped(orientation=para_orientation)])[0]

        assert isinstance(domain.orientation, ElementOrientation)
        assert domain.orientation == expected

    def test_stiffness_definition_is_full_node_spring(self, domain):
        assert isinstance(domain.stiffness_definition, NodeSpringStiffness)

    def test_custom_translational_dof_keeps_value_and_unit(self, domain):
        assert_dof(domain.stiffness_definition.sdx, DofTypeEnum.CUSTOM, (1_000_000, "N/m"))

    def test_custom_rotational_dof_keeps_value_and_unit(self, domain):
        assert_dof(domain.stiffness_definition.srx, DofTypeEnum.CUSTOM, (4_000_000, "N*m/rad"))

    def test_fixed_translational_dof_keeps_value_and_unit(self, domain):
        assert_dof(domain.stiffness_definition.sdy, DofTypeEnum.FIXED, (2_000_000, "N/m"))

    def test_fixed_rotational_dof_keeps_value_and_unit(self, domain):
        assert_dof(domain.stiffness_definition.sry, DofTypeEnum.FIXED, (5_000_000, "N*m/rad"))

    def test_translational_dof_without_stiffness_maps_to_none(self, domain):
        assert_dof(domain.stiffness_definition.sdz, DofTypeEnum.FREE, None)

    def test_rotational_dof_without_stiffness_maps_to_none(self, domain):
        assert_dof(domain.stiffness_definition.srz, DofTypeEnum.FREE, None)

    def test_stiffness_is_copied_verbatim_even_for_free_dof(self):
        """The mapper is a pure translation layer: it does not sanitise inputs."""
        stiffness = make_node_spring(sdz=dof("free", 9_000_000))

        domain = FoundationMapper.to_domain([make_lumped(stiffness_definition=stiffness)])[0]

        assert_dof(domain.stiffness_definition.sdz, DofTypeEnum.FREE, (9_000_000, "N/m"))

    @pytest.mark.parametrize(
        ("para_dof", "expected"),
        [
            (DofTypeEnumParaModel.FREE, DofTypeEnum.FREE),
            (DofTypeEnumParaModel.FIXED, DofTypeEnum.FIXED),
            (DofTypeEnumParaModel.CUSTOM, DofTypeEnum.CUSTOM),
        ],
    )
    def test_every_para_dof_type_has_a_domain_counterpart(self, para_dof, expected):
        stiffness = make_node_spring(sdx=dof(para_dof.value, 1_000))

        domain = FoundationMapper.to_domain([make_lumped(stiffness_definition=stiffness)])[0]

        assert domain.stiffness_definition.sdx.dof_type == expected

    def test_dof_type_is_case_insensitive_on_the_contract(self):
        stiffness = make_node_spring(sdx=dof("CUSTOM", 1_000))

        domain = FoundationMapper.to_domain([make_lumped(stiffness_definition=stiffness)])[0]

        assert domain.stiffness_definition.sdx.dof_type == DofTypeEnum.CUSTOM

    def test_bearing_based_application_is_mapped(self, domain):
        application = domain.application

        assert isinstance(application, BearingBasedFoundationApplication)
        assert application.application_type == FoundationApplicationType.BEARING_BASED
        assert_quantity(application.vertical_offset, 0.5, "m")

    def test_bearing_based_application_falls_back_to_default_offset(self):
        para = make_lumped(
            application=BearingBasedFoundationApplicationParaModel(
                application_type=FoundationApplicationTypeEnumParaModel.BEARING_BASED,
            )
        )

        application = FoundationMapper.to_domain([para])[0].application

        assert_quantity(application.vertical_offset, *DEFAULT_VERTICAL_OFFSET)

    def test_substructure_element_based_application_is_mapped(self):
        para = make_lumped(
            application=SubstructureElementBasedFoundationApplicationParaModel(
                application_type=FoundationApplicationTypeEnumParaModel.SUBSTRUCTURE_ELEMENT_BASED,
            )
        )

        application = FoundationMapper.to_domain([para])[0].application

        assert isinstance(application, SubstructureElementBasedFoundationApplication)
        assert application.application_type == FoundationApplicationType.SUBSTRUCTURE_ELEMENT_BASED


class TestPileInteractionFoundationMapping:
    """PileInteractionFoundationBCsParaModel -> PileInteractionFoundationBCs."""

    @pytest.fixture
    def para(self) -> PileInteractionFoundationBCsParaModel:
        return make_pile_interaction(
            support_index=5,
            pile_springs=[make_pile_dataset(pile_index=0), make_pile_dataset(pile_index=1)],
        )

    @pytest.fixture
    def domain(self, para) -> PileInteractionFoundationBCs:
        return FoundationMapper.to_domain([para])[0]

    def test_maps_to_pile_interaction_domain_type(self, domain):
        assert isinstance(domain, PileInteractionFoundationBCs)

    def test_support_index_is_copied(self, domain):
        assert domain.support_index == 5

    def test_foundation_model_type_is_pile_interaction(self, domain):
        assert domain.foundation_model_type == FoundationModelType.PILE_INTERACTION_MODEL

    def test_all_pile_datasets_are_mapped_in_order(self, domain):
        assert all(isinstance(dataset, PileStiffnessUniformDataset) for dataset in domain.pile_springs)
        assert [dataset.pile_index for dataset in domain.pile_springs] == [0, 1]

    def test_soil_profile_type_is_uniform(self, domain):
        assert all(
            dataset.soil_profile_type == SoilProfileType.UNIFORM for dataset in domain.pile_springs
        )

    def test_top_node_is_mapped(self, domain):
        top_node = domain.pile_springs[0].top_node

        assert isinstance(top_node, PileNodeSpringStiffness)
        assert_dof(top_node.sdx, DofTypeEnum.CUSTOM, (1_000_000, "N/m"))
        assert_dof(top_node.sdy, DofTypeEnum.FIXED, (2_000_000, "N/m"))
        assert_dof(top_node.sdz, DofTypeEnum.FREE, None)

    def test_bottom_node_is_mapped(self, domain):
        bottom_node = domain.pile_springs[0].bottom_node

        assert isinstance(bottom_node, PileNodeSpringStiffness)
        assert_dof(bottom_node.sdx, DofTypeEnum.CUSTOM, (2_000_000, "N/m"))

    def test_pile_nodes_carry_translational_dofs_only(self, domain):
        assert not hasattr(domain.pile_springs[0].top_node, "srx")

    def test_single_intermediate_definition_becomes_a_one_element_list(self, domain):
        """The contract holds one definition shared by all intermediate nodes."""
        intermediate_nodes = domain.pile_springs[0].intermediate_nodes

        assert isinstance(intermediate_nodes, PileNodeSpringStiffness)
        assert_dof(intermediate_nodes.sdx, DofTypeEnum.CUSTOM, (3_000_000, "N/m"))

    def test_intermediate_definition_is_mapped_per_dataset(self):
        para = make_pile_interaction(
            pile_springs=[
                make_pile_dataset(pile_index=0, intermediate_nodes=make_pile_node(1_000)),
                make_pile_dataset(pile_index=1, intermediate_nodes=make_pile_node(2_000)),
            ]
        )

        domain = FoundationMapper.to_domain([para])[0]

        magnitudes = [
            dataset.intermediate_nodes.sdx.stiffness.magnitude
            for dataset in domain.pile_springs
        ]
        assert magnitudes == pytest.approx([1_000, 2_000])

    def test_empty_pile_springs_are_allowed(self):
        domain = FoundationMapper.to_domain([make_pile_interaction(pile_springs=[])])[0]

        assert domain.pile_springs == []


class TestRawPayloadMapping:
    """Discriminated unions must resolve concrete types the mapper can dispatch on."""

    LUMPED_PAYLOAD = {
        "foundation_model_type": "lumped_foundation_model",
        "support_index": 7,
        "stiffness_definition": {
            "sdx": dof("custom", 1_000_000),
            "sdy": dof("fixed", 2_000_000),
            "sdz": dof("free"),
            "srx": dof("custom", 4_000_000, "N*m/rad"),
            "sry": dof("fixed", 5_000_000, "N*m/rad"),
            "srz": dof("free"),
        },
        "orientation": "orthogonal",
        "application": {"application_type": "bearing_based", "vertical_offset": {"value": 0.5, "unit": "m"}},
    }

    PILE_PAYLOAD = {
        "foundation_model_type": "pile_interaction_model",
        "support_index": 8,
        "pile_springs": [
            {
                "soil_profile_type": "uniform",
                "pile_index": 0,
                "top_node": {"sdx": dof("custom", 1_000_000), "sdy": dof("fixed", 2_000_000), "sdz": dof("free")},
                "bottom_node": {"sdx": dof("custom", 2_000_000), "sdy": dof("fixed", 2_000_000), "sdz": dof("free")},
                "intermediate_nodes": {
                    "sdx": dof("custom", 3_000_000),
                    "sdy": dof("fixed", 2_000_000),
                    "sdz": dof("free"),
                },
            }
        ],
    }

    def test_lumped_payload_maps_to_bearing_based_application(self):
        para = LumpedFoundationBCsParaModel.model_validate(self.LUMPED_PAYLOAD)

        domain = FoundationMapper.to_domain([para])[0]

        assert isinstance(domain, LumpedFoundationBCs)
        assert domain.support_index == 7
        assert isinstance(domain.application, BearingBasedFoundationApplication)
        assert_quantity(domain.application.vertical_offset, 0.5, "m")

    def test_lumped_payload_maps_to_substructure_application(self):
        payload = {
            **self.LUMPED_PAYLOAD,
            "application": {"application_type": "substructure_element_based"},
        }
        para = LumpedFoundationBCsParaModel.model_validate(payload)

        domain = FoundationMapper.to_domain([para])[0]

        assert isinstance(domain.application, SubstructureElementBasedFoundationApplication)

    def test_pile_payload_maps_to_uniform_dataset(self):
        para = PileInteractionFoundationBCsParaModel.model_validate(self.PILE_PAYLOAD)

        domain = FoundationMapper.to_domain([para])[0]

        assert isinstance(domain, PileInteractionFoundationBCs)
        assert domain.support_index == 8
        assert domain.pile_springs[0].soil_profile_type == SoilProfileType.UNIFORM
        assert_dof(
            domain.pile_springs[0].intermediate_nodes.sdx, DofTypeEnum.CUSTOM, (3_000_000, "N/m")
        )


class TestCollectionSemantics:
    """Behaviour of FoundationMapper.to_domain across the whole input list."""

    def test_empty_input_returns_empty_list(self):
        assert FoundationMapper.to_domain([]) == []

    def test_returns_one_domain_model_per_para_model(self):
        para_models = [make_lumped(support_index=0), make_lumped(support_index=1)]

        result = FoundationMapper.to_domain(para_models)

        assert len(result) == len(para_models)

    def test_mixed_model_types_keep_input_order(self):
        para_models = [
            make_lumped(support_index=0),
            make_pile_interaction(support_index=1),
            make_lumped(support_index=2),
        ]

        result = FoundationMapper.to_domain(para_models)

        assert [type(item) for item in result] == [
            LumpedFoundationBCs,
            PileInteractionFoundationBCs,
            LumpedFoundationBCs,
        ]
        assert [item.support_index for item in result] == [0, 1, 2]

    def test_each_call_builds_independent_domain_objects(self):
        para = make_lumped()

        first = FoundationMapper.to_domain([para])[0]
        second = FoundationMapper.to_domain([para])[0]

        assert first is not second
        assert first.stiffness_definition is not second.stiffness_definition


class TestUnsupportedInput:
    """Error paths of the mapping dispatch."""

    def test_unsupported_para_model_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported foundation model type"):
            FoundationMapper.to_domain([quantity(1.0, "m")])

    def test_error_message_names_only_the_unsupported_types(self):
        with pytest.raises(ValueError) as excinfo:
            FoundationMapper.to_domain([make_lumped(), quantity(1.0, "m")])

        assert "QuantityParaModel" in str(excinfo.value)
        assert "LumpedFoundationBCsParaModel" not in str(excinfo.value)

    def test_input_is_validated_before_any_mapping_happens(self, monkeypatch):
        mapped: list[object] = []
        monkeypatch.setitem(
            foundation_mapper._MAPPING_FUNCS,
            LumpedFoundationBCsParaModel,
            mapped.append,
        )

        with pytest.raises(ValueError):
            FoundationMapper.to_domain([make_lumped(), quantity(1.0, "m")])

        assert mapped == []

    def test_para_model_subclass_is_rejected_by_exact_type_dispatch(self):
        class CustomLumpedParaModel(LumpedFoundationBCsParaModel):
            pass

        para = CustomLumpedParaModel.model_validate(TestRawPayloadMapping.LUMPED_PAYLOAD)

        with pytest.raises(ValueError, match="CustomLumpedParaModel"):
            FoundationMapper.to_domain([para])

    def test_unsupported_application_type_raises_value_error(self):
        """Defensive guard: the discriminated union already rejects the base type,
        so this branch is only reachable by calling the mapper directly."""
        application = FoundationApplicationBaseParaModel(
            application_type=FoundationApplicationTypeEnumParaModel.BEARING_BASED,
        )

        with pytest.raises(ValueError, match="Unsupported foundation application type"):
            foundation_mapper._map_application(application)

    def test_unknown_dof_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported DOF type"):
            foundation_mapper._map_dof_type("not_a_dof_type")
