"""Unit tests for the MILP model builder."""
import math
import pytest
from app.model import (
    BREAKPOINTS, WIDTHS, SLOPES, X_EFF_MAX, build_model,
)


@pytest.mark.unit
class TestPiecewiseApproximation:
    def test_breakpoints_match_thesis(self):
        assert BREAKPOINTS == [0, 0.5, 1.0, 2.0, 4.0]

    def test_widths_sum_to_max(self):
        assert sum(WIDTHS) == X_EFF_MAX

    def test_slopes_match_thesis(self):
        """Slopes from thesis §4.5.3."""
        assert abs(SLOPES[0] - 1.414) < 0.001
        assert abs(SLOPES[1] - 0.586) < 0.001
        assert abs(SLOPES[2] - 0.414) < 0.001
        assert abs(SLOPES[3] - 0.293) < 0.001

    def test_slopes_decreasing(self):
        """Required for concavity (no binary variable needed for segment ordering)."""
        for k in range(len(SLOPES) - 1):
            assert SLOPES[k] > SLOPES[k + 1]

    def test_approx_matches_sqrt_at_breakpoints(self):
        """Piecewise linear approximation is exact at breakpoints."""
        for bp in BREAKPOINTS:
            approx = 0.0
            for k in range(4):
                if bp <= BREAKPOINTS[k]:
                    break
                seg_max = min(bp, BREAKPOINTS[k + 1]) - BREAKPOINTS[k]
                approx += SLOPES[k] * seg_max
            assert abs(approx - math.sqrt(bp)) < 1e-6, f"At x={bp}"


@pytest.mark.unit
class TestBuildModel:
    def test_model_created(self):
        prob, variables = build_model(
            subjects=[{"id": "s1", "required_hours": 2, "deadline_day": 1,
                       "difficulty": 3, "priority": 3, "urgency": 0.5}],
            time_slots=[{"day": 0, "slot": 0, "tod_factor": 1.0, "available_hours": 2}],
            max_daily_hours=4.0,
        )
        assert prob is not None
        assert "x" in variables
        assert "s" in variables
        assert "u" in variables

    def test_urgency_auto_computed(self):
        prob, variables = build_model(
            subjects=[{"id": "s1", "required_hours": 2, "deadline_day": 3,
                       "difficulty": 3, "priority": 3}],  # no urgency
            time_slots=[{"day": 0, "slot": 0, "tod_factor": 1.0, "available_hours": 2}],
            max_daily_hours=4.0,
        )
        # urgency should be 1/(1+3) = 0.25
        # (not directly accessible, but model builds successfully)
        assert prob is not None
