"""Unit tests for DataRequest — merge, difference, is_empty, all_load_cases.

Covers:
    - merge: union of two requests
    - merge_all: union of an iterable of requests
    - difference: subtraction of cached coverage
    - is_empty: vacancy check
    - all_load_cases: union of all load-case sets
    - frozen / immutable semantics
"""
from __future__ import annotations

import pytest

from bda.domain.results.data_request import DataRequest


# =====================================================================
# TestConstruction
# =====================================================================


class TestConstruction:
    """DataRequest defaults and basic construction."""

    def test_default_empty(self):
        dr = DataRequest()
        assert dr.element_ids == frozenset()
        assert dr.node_ids == frozenset()
        assert dr.force_loadcases == frozenset()
        assert dr.stress_loadcases == frozenset()
        assert dr.disp_loadcases == frozenset()

    def test_is_empty_default(self):
        assert DataRequest().is_empty()

    def test_is_empty_with_elements(self):
        dr = DataRequest(element_ids=frozenset({1}))
        assert not dr.is_empty()

    def test_is_empty_with_nodes(self):
        dr = DataRequest(node_ids=frozenset({1}))
        assert not dr.is_empty()

    def test_is_empty_with_force_lcs(self):
        dr = DataRequest(force_loadcases=frozenset({"Dead"}))
        assert not dr.is_empty()

    def test_is_empty_with_stress_lcs(self):
        dr = DataRequest(stress_loadcases=frozenset({"Dead"}))
        assert not dr.is_empty()

    def test_is_empty_with_disp_lcs(self):
        dr = DataRequest(disp_loadcases=frozenset({"Dead"}))
        assert not dr.is_empty()

    def test_frozen(self):
        dr = DataRequest()
        with pytest.raises(AttributeError):
            dr.element_ids = frozenset({1})


# =====================================================================
# TestMerge
# =====================================================================


class TestMerge:
    """Tests for DataRequest.merge — union of two requests."""

    def test_merge_disjoint(self):
        dr1 = DataRequest(
            element_ids=frozenset({1, 2}),
            node_ids=frozenset({10}),
            force_loadcases=frozenset({"Dead"}),
        )
        dr2 = DataRequest(
            element_ids=frozenset({3}),
            node_ids=frozenset({20}),
            force_loadcases=frozenset({"Live"}),
            disp_loadcases=frozenset({"Dead"}),
        )
        merged = dr1.merge(dr2)

        assert merged.element_ids == frozenset({1, 2, 3})
        assert merged.node_ids == frozenset({10, 20})
        assert merged.force_loadcases == frozenset({"Dead", "Live"})
        assert merged.disp_loadcases == frozenset({"Dead"})
        assert merged.stress_loadcases == frozenset()

    def test_merge_overlapping(self):
        dr1 = DataRequest(element_ids=frozenset({1, 2}))
        dr2 = DataRequest(element_ids=frozenset({2, 3}))
        merged = dr1.merge(dr2)

        assert merged.element_ids == frozenset({1, 2, 3})

    def test_merge_does_not_mutate(self):
        dr1 = DataRequest(element_ids=frozenset({1}))
        dr2 = DataRequest(element_ids=frozenset({2}))
        merged = dr1.merge(dr2)

        assert dr1.element_ids == frozenset({1})
        assert len(merged.element_ids) == 2

    def test_merge_with_empty(self):
        dr = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"Dead"}),
        )
        merged = dr.merge(DataRequest())

        assert merged.element_ids == frozenset({1})
        assert merged.force_loadcases == frozenset({"Dead"})


# =====================================================================
# TestMergeAll
# =====================================================================


class TestMergeAll:
    """Tests for DataRequest.merge_all — union of an iterable."""

    def test_merge_all_empty_iterable(self):
        merged = DataRequest.merge_all([])
        assert merged.is_empty()

    def test_merge_all_single(self):
        dr = DataRequest(element_ids=frozenset({1}))
        merged = DataRequest.merge_all([dr])
        assert merged.element_ids == frozenset({1})

    def test_merge_all_multiple(self):
        requests = [
            DataRequest(element_ids=frozenset({1}), force_loadcases=frozenset({"Dead"})),
            DataRequest(element_ids=frozenset({2}), force_loadcases=frozenset({"Live"})),
            DataRequest(node_ids=frozenset({10}), disp_loadcases=frozenset({"Dead"})),
        ]
        merged = DataRequest.merge_all(requests)

        assert merged.element_ids == frozenset({1, 2})
        assert merged.node_ids == frozenset({10})
        assert merged.force_loadcases == frozenset({"Dead", "Live"})
        assert merged.disp_loadcases == frozenset({"Dead"})

    def test_merge_all_generator(self):
        """merge_all should accept any iterable, not just lists."""
        def gen():
            yield DataRequest(element_ids=frozenset({1}))
            yield DataRequest(element_ids=frozenset({2}))

        merged = DataRequest.merge_all(gen())
        assert merged.element_ids == frozenset({1, 2})


# =====================================================================
# TestDifference
# =====================================================================


class TestDifference:
    """Tests for DataRequest.difference — subtract cached coverage."""

    def test_difference_disjoint(self):
        """If no overlap, difference is the original."""
        dr = DataRequest(
            element_ids=frozenset({1, 2}),
            force_loadcases=frozenset({"Dead", "Live"}),
        )
        cached = DataRequest(
            element_ids=frozenset({3}),
            force_loadcases=frozenset({"Wind"}),
        )
        diff = dr.difference(cached)

        assert diff.element_ids == frozenset({1, 2})
        assert diff.force_loadcases == frozenset({"Dead", "Live"})

    def test_difference_full_coverage(self):
        """If everything is cached, difference is empty."""
        dr = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"Dead"}),
        )
        diff = dr.difference(dr)
        assert diff.element_ids == frozenset()
        assert diff.force_loadcases == frozenset()

    def test_difference_partial(self):
        dr = DataRequest(
            element_ids=frozenset({1, 2, 3}),
            force_loadcases=frozenset({"Dead", "Live", "Wind"}),
            node_ids=frozenset({10, 20}),
        )
        cached = DataRequest(
            element_ids=frozenset({1, 2}),
            force_loadcases=frozenset({"Dead"}),
            node_ids=frozenset({10}),
        )
        diff = dr.difference(cached)

        assert diff.element_ids == frozenset({3})
        assert diff.force_loadcases == frozenset({"Live", "Wind"})
        assert diff.node_ids == frozenset({20})

    def test_difference_does_not_mutate(self):
        dr = DataRequest(element_ids=frozenset({1, 2}))
        cached = DataRequest(element_ids=frozenset({1}))
        diff = dr.difference(cached)

        assert dr.element_ids == frozenset({1, 2})
        assert diff.element_ids == frozenset({2})

    def test_difference_all_five_fields(self):
        """All five id/loadcase sets are subtracted independently."""
        dr = DataRequest(
            element_ids=frozenset({1, 2}),
            node_ids=frozenset({10, 20}),
            force_loadcases=frozenset({"A", "B"}),
            stress_loadcases=frozenset({"C", "D"}),
            disp_loadcases=frozenset({"E", "F"}),
        )
        cached = DataRequest(
            element_ids=frozenset({1}),
            node_ids=frozenset({10}),
            force_loadcases=frozenset({"A"}),
            stress_loadcases=frozenset({"C"}),
            disp_loadcases=frozenset({"E"}),
        )
        diff = dr.difference(cached)

        assert diff.element_ids == frozenset({2})
        assert diff.node_ids == frozenset({20})
        assert diff.force_loadcases == frozenset({"B"})
        assert diff.stress_loadcases == frozenset({"D"})
        assert diff.disp_loadcases == frozenset({"F"})


# =====================================================================
# TestAllLoadCases
# =====================================================================


class TestAllLoadCases:
    """Tests for DataRequest.all_load_cases — union of all LC sets."""

    def test_empty(self):
        assert DataRequest().all_load_cases() == frozenset()

    def test_union(self):
        dr = DataRequest(
            force_loadcases=frozenset({"Dead", "Live"}),
            stress_loadcases=frozenset({"Live", "Wind"}),
            disp_loadcases=frozenset({"Dead", "Seismic"}),
        )
        assert dr.all_load_cases() == frozenset({"Dead", "Live", "Wind", "Seismic"})

    def test_no_duplicates(self):
        dr = DataRequest(
            force_loadcases=frozenset({"Dead"}),
            stress_loadcases=frozenset({"Dead"}),
            disp_loadcases=frozenset({"Dead"}),
        )
        assert dr.all_load_cases() == frozenset({"Dead"})
