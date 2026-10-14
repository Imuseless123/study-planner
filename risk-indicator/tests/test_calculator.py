"""Unit tests for calculator.py — pure functions."""
import pytest
from app.calculator import (
    W_SLEEP_DEFICIT,
    W_WORKLOAD_DENSITY,
    W_DEADLINE_PROXIMITY,
    W_STUDY_INCONSISTENCY,
    normalize_sleep_deficit,
    normalize_workload_density,
    normalize_deadline_proximity,
    normalize_study_inconsistency,
    classify_risk,
    calculate_risk_score,
    compute_risk,
)


# ============================================================
# Weight invariants
# ============================================================

class TestWeights:
    def test_weights_sum_to_one(self):
        total = (
            W_SLEEP_DEFICIT
            + W_WORKLOAD_DENSITY
            + W_DEADLINE_PROXIMITY
            + W_STUDY_INCONSISTENCY
        )
        assert abs(total - 1.0) < 1e-9

    def test_weights_match_literature(self):
        """Weights should match the values declared in thesis §3.6.2."""
        assert W_SLEEP_DEFICIT == 0.35
        assert W_WORKLOAD_DENSITY == 0.30
        assert W_DEADLINE_PROXIMITY == 0.20
        assert W_STUDY_INCONSISTENCY == 0.15


# ============================================================
# normalize_sleep_deficit
# ============================================================

class TestNormalizeSleepDeficit:
    def test_no_deficit_at_8h(self):
        assert normalize_sleep_deficit(8) == 0.0

    def test_no_deficit_at_7h(self):
        assert normalize_sleep_deficit(7) == 0.0

    def test_half_deficit_at_5h(self):
        assert normalize_sleep_deficit(5) == 0.5

    def test_max_deficit_at_3h(self):
        assert normalize_sleep_deficit(3) == 1.0

    def test_capped_above_max(self):
        assert normalize_sleep_deficit(1) == 1.0
        assert normalize_sleep_deficit(0) == 1.0

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            normalize_sleep_deficit(-1)


# ============================================================
# normalize_workload_density
# ============================================================

class TestNormalizeWorkloadDensity:
    def test_low_density(self):
        assert normalize_workload_density(10, 40) == 0.25

    def test_half_density(self):
        assert normalize_workload_density(20, 40) == 0.5

    def test_full_density(self):
        assert normalize_workload_density(40, 40) == 1.0

    def test_capped_above_available(self):
        assert normalize_workload_density(50, 40) == 1.0

    def test_zero_available_returns_max(self):
        assert normalize_workload_density(10, 0) == 1.0

    def test_negative_required_raises(self):
        with pytest.raises(ValueError):
            normalize_workload_density(-1, 40)


# ============================================================
# normalize_deadline_proximity
# ============================================================

class TestNormalizeDeadlineProximity:
    def test_deadline_today(self):
        assert normalize_deadline_proximity(0) == 1.0

    def test_deadline_tomorrow(self):
        assert normalize_deadline_proximity(1) == 0.5

    def test_deadline_in_2_days(self):
        assert abs(normalize_deadline_proximity(2) - 1 / 3) < 1e-9

    def test_far_deadline(self):
        result = normalize_deadline_proximity(30)
        assert abs(result - 1 / 31) < 1e-9

    def test_past_deadline_returns_max(self):
        assert normalize_deadline_proximity(-1) == 1.0


# ============================================================
# normalize_study_inconsistency
# ============================================================

class TestNormalizeStudyInconsistency:
    def test_perfectly_consistent(self):
        assert normalize_study_inconsistency(0) == 0.0

    def test_half_inconsistent(self):
        assert normalize_study_inconsistency(1.5) == 0.5

    def test_max_inconsistent(self):
        assert normalize_study_inconsistency(3.0) == 1.0

    def test_capped_above_max(self):
        assert normalize_study_inconsistency(5) == 1.0

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            normalize_study_inconsistency(-1)


# ============================================================
# classify_risk
# ============================================================

class TestClassifyRisk:
    def test_low_boundary_0(self):
        assert classify_risk(0) == "low"

    def test_low_boundary_30(self):
        assert classify_risk(30) == "low"

    def test_moderate_31(self):
        assert classify_risk(31) == "moderate"

    def test_moderate_boundary_60(self):
        assert classify_risk(60) == "moderate"

    def test_high_61(self):
        assert classify_risk(61) == "high"

    def test_high_100(self):
        assert classify_risk(100) == "high"


# ============================================================
# calculate_risk_score
# ============================================================

class TestCalculateRiskScore:
    def test_all_zero_inputs(self):
        assert calculate_risk_score(0, 0, 0, 0) == 0.0

    def test_all_one_inputs(self):
        # 100 × (0.35 + 0.30 + 0.20 + 0.15) = 100
        assert calculate_risk_score(1, 1, 1, 1) == 100.0

    def test_only_sleep_deficit(self):
        # 100 × 0.35 × 1 = 35
        assert calculate_risk_score(1, 0, 0, 0) == 35.0

    def test_only_workload_density(self):
        # 100 × 0.30 × 1 = 30
        assert calculate_risk_score(0, 1, 0, 0) == 30.0

    def test_only_deadline_proximity(self):
        # 100 × 0.20 × 1 = 20
        assert calculate_risk_score(0, 0, 1, 0) == 20.0

    def test_only_study_inconsistency(self):
        # 100 × 0.15 × 1 = 15
        assert calculate_risk_score(0, 0, 0, 1) == 15.0


# ============================================================
# compute_risk — full pipeline
# ============================================================

class TestComputeRisk:
    def test_good_habits_scenario(self):
        """
        From thesis §3.6.2:
            sleep=8, required=10, available=40, days=14, std=0.49
            Expected: score ≈ 11.3
        """
        result = compute_risk(
            sleep_hours=8,
            required_hours=10,
            available_hours=40,
            days_until_deadline=14,
            study_std=0.49,
        )
        assert abs(result.risk_score - 11.3) < 0.1
        assert result.level == "low"

    def test_high_risk_scenario(self):
        """
        From thesis §3.6.2:
            sleep=5, required=30, available=40, days=2, std=3.06
            Expected: score ≈ 61.7
        """
        result = compute_risk(
            sleep_hours=5,
            required_hours=30,
            available_hours=40,
            days_until_deadline=2,
            study_std=3.06,
        )
        assert abs(result.risk_score - 61.7) < 0.1
        assert result.level == "high"

    def test_boundary_all_max(self):
        """All components at max → score = 100."""
        result = compute_risk(
            sleep_hours=3,
            required_hours=40,
            available_hours=40,
            days_until_deadline=0,
            study_std=3.0,
        )
        assert result.risk_score == 100.0
        assert result.level == "high"

    def test_components_sum_present(self):
        """Result should include component breakdown."""
        result = compute_risk(8, 10, 40, 14, 0.49)
        assert set(result.components.keys()) == {
            "sleep_deficit",
            "workload_density",
            "deadline_proximity",
            "study_inconsistency",
        }
        # All components in [0, 1]
        for v in result.components.values():
            assert 0 <= v <= 1

    def test_weights_in_result(self):
        result = compute_risk(8, 10, 40, 14, 0.49)
        assert result.weights["sleep_deficit"] == 0.35
        assert result.weights["workload_density"] == 0.30
