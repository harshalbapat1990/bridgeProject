from pathlib import Path
import pytest

from bda.application.mapping.base import to_uuid
from bda.application.mapping.sections.section_mapper import SectionMapper
from bda.contracts.paramodel.sections import SectionBaseParaModel
from bda.contracts.paramodel.sections.sections_para_models import SectionFamilyParaModel, SectionTypeParaModel, \
    SectionOffsetParaModel
from bda.domain.enums import OffsetReference, SectionType, TaperVariation
from bda.domain.models.submodels.sections import SectionStandardAngle, SectionPSCValue, Point2D, SectionStandardISection, \
    SectionStandardBox, SectionStandardChannel, SectionStandardSolidRectangle, SectionStandardSolidRound, SectionStandardPipe, \
    SectionCompositeSteelISymmetric, SectionCompositeSteelIAsymmetric, SectionPSC12Cell, SectionTapered
from bda.infrastructure.data_providers import DataFileProvider



class TestSectionMapper:
    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path):
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def sections(self, provider):
        return provider.get_sections_for_project()

    def test_map_all_sections_from_json(self, sections):
        result = SectionMapper.to_domain_list(sections)
        assert len(result) == len(sections)

    def test_mapper_standard(self, sections):
        result = SectionMapper.to_domain_list(sections)
        standard_angle = next(x for x in result if x.name == "standard_angle")

        assert standard_angle is not None

    def test_mapper_standard_values(self, sections):
        result = SectionMapper.to_domain_list(sections)
        standard_angle = next(x for x in result if x.name == "standard_angle")

        assert isinstance(standard_angle, SectionStandardAngle)
        assert standard_angle.name == "standard_angle"
        assert standard_angle.offset.offset_reference == OffsetReference.LEFT_TOP
        assert standard_angle.dimensions.height.magnitude == 0.203
        assert standard_angle.dimensions.width.magnitude == 0.203
        assert standard_angle.dimensions.thickness_web.magnitude == 0.022
        assert standard_angle.dimensions.thickness_flange.magnitude == 0.022
        assert standard_angle.dimensions.height.units == "meter"

    def test_mapper_PSCValue(self, sections):
        result = SectionMapper.to_domain_list(sections)
        psc_value = next(x for x in result if x.name == "psc_value_section")

        assert isinstance(psc_value, SectionPSCValue)
        assert psc_value.name == "psc_value_section"
        assert psc_value.offset.offset_reference == OffsetReference.CENTER_TOP

        #+------------------------------------
        #+  dimension.outer_outline
        #+------------------------------------

        assert isinstance(psc_value.dimensions.outer_outline, list)
        assert len(psc_value.dimensions.outer_outline) == 4
        assert all(isinstance(p, Point2D) for p in psc_value.dimensions.outer_outline)

        pts = psc_value.dimensions.outer_outline

        expected = [
            (0.0, 0.0),
            (1.2, 0.0),
            (1.2, 2.1),
            (0.0, 2.1),
        ]

        for p, (x,y) in zip(pts, expected):
            assert p.x.magnitude == pytest.approx(x)
            assert p.y.magnitude == pytest.approx(y)
            assert str(p.x.units) in ("meter", "m")

        # +------------------------------------
        # +  dimension.inner_outlines
        # +------------------------------------
        inner = psc_value.dimensions.inner_outlines

        assert len(inner) == 1

        expected_inner = [
            [
                (0.2, 0.4),
                (1.0, 0.4),
                (1.0, 1.7),
                (0.2, 1.7),
            ]
        ]

        for outline, exp_outline in zip(inner, expected_inner):
            assert len(outline) == len(exp_outline)

            for p, (x, y) in zip(outline, exp_outline):
                assert p.x.magnitude == pytest.approx(x)
                assert p.y.magnitude == pytest.approx(y)
                assert str(p.x.units) in ("meter", "m")
                assert str(p.y.units) in ("meter", "m")

    def test_mapper_standard_all_types(self, sections):
        result = SectionMapper.to_domain_list(sections)

        types = {
            "standard_angle": SectionStandardAngle,
            "standard_I_section": SectionStandardISection,
            "standard_box": SectionStandardBox,
            "standard_channel": SectionStandardChannel,
            "standard_solid_rectangle": SectionStandardSolidRectangle,
            "standard_solid_round": SectionStandardSolidRound,
            "standard_pipe": SectionStandardPipe,
        }

        for name, cls in types.items():
            obj = next(x for x in result if x.name == name)
            assert isinstance(obj, cls)
            assert obj.guid is not None

    def test_mapper_composite(self, sections):
        result = SectionMapper.to_domain_list(sections)

        sym = next(x for x in result if x.name == "composite_steel_i_type1")
        asym = next(x for x in result if x.name == "composite_steel_i_type2")

        assert isinstance(sym, SectionCompositeSteelISymmetric)
        assert isinstance(asym, SectionCompositeSteelIAsymmetric)

        assert sym.dimensions.slab_width_bc.magnitude == 3.0
        assert asym.dimensions.slab_width_bc.magnitude == 3.2

    def test_mapper_psc_cells(self, sections):
        result = SectionMapper.to_domain_list(sections)

        psc1 = next(x for x in result if x.name == "psc_1cell")
        psc2 = next(x for x in result if x.name == "psc_2cell")

        assert isinstance(psc1, SectionPSC12Cell)
        assert isinstance(psc2, SectionPSC12Cell)

        assert psc1.section_type == SectionType.PSC_1CELL
        assert psc2.section_type == SectionType.PSC_2CELL

        assert len(psc1.dimensions.outer_height_ho.to_list()) > 0

    def test_mapper_tapered_basic(self, sections):
        result = SectionMapper.to_domain_list(sections)

        tapered = next(x for x in result if x.name == "tapered_example_1")

        assert isinstance(tapered, SectionTapered)

        assert tapered.section_start_id == to_uuid("331ffcb4-4aa8-4d67-9b72-e7428ac99bdf")
        assert tapered.section_end_id == to_uuid("331ffcb4-4aa8-4d67-9b71-e7428ac99bdf")

        assert tapered.taper_y_variation == TaperVariation.LINEAR
        assert tapered.taper_z_variation == TaperVariation.LINEAR

    def test_mapper_tapered_fallback(self, sections):
        result = SectionMapper.to_domain_list(sections)

        tapered = next(x for x in result if x.name == "tapered_example_1")

        assert isinstance(tapered, SectionTapered)

    def test_offset_mapping(self, sections):
        result = SectionMapper.to_domain_list(sections)

        sec = next(x for x in result if x.name == "standard_box")

        assert sec.offset.offset_reference == OffsetReference.RIGHT_TOP

    def test_guid_mapping(self, sections):
        result = SectionMapper.to_domain_list(sections)

        sec = next(x for x in result if x.name == "standard_angle")

        assert sec.guid == to_uuid("331ffcb4-4aa8-4d67-9b72-e7428ac99bdf")

def test_mapper_missing_mapper():
    class FakeSection(SectionBaseParaModel):
        section_id: str = "fake-id"
        name: str = "fake"
        section_family: SectionFamilyParaModel = SectionFamilyParaModel.STANDARD_SHAPE
        section_type: SectionTypeParaModel = "non-existing-type"
        offset: SectionOffsetParaModel = SectionOffsetParaModel.CENTER_CENTER

    fake = FakeSection()

    with pytest.raises(NotImplementedError):
        SectionMapper.to_domain(fake)

