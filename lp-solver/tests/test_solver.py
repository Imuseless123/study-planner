"""Integration tests for the solver."""
import pytest
from app.solver import solve_schedule


@pytest.mark.integration
class TestThesisExample:
    def test_thesis_example_optimal(self, thesis_example_payload):
        """
        From thesis §4.5.6:
        - 2 subjects, 3 days, W_max = 4
        - Expected Z ≈ 52.0
        """
        result = solve_schedule(thesis_example_payload)
        assert result["status"] == "optimal"
        assert result["feasible"] is True
        assert abs(result["objective_value"] - 52.0) < 2.0  # tolerance

    def test_no_deadline_shortfall(self, thesis_example_payload):
        result = solve_schedule(thesis_example_payload)
        for subj in result["explanation"]["per_subject"]:
            assert subj["deadline_shortfall"] < 0.01

    def test_no_daily_overload(self, thesis_example_payload):
        result = solve_schedule(thesis_example_payload)
        for day in result["explanation"]["per_day"]:
            assert day["overload"] < 0.01


@pytest.mark.integration
class TestFeasibility:
    def test_simple_feasible(self, simple_payload):
        result = solve_schedule(simple_payload)
        assert result["status"] == "optimal"
        assert result["feasible"] is True
        assert len(result["schedule"]) > 0

    def test_respects_daily_cap(self, simple_payload):
        result = solve_schedule(simple_payload)
        for day in result["explanation"]["per_day"]:
            assert day["total_hours"] <= 4.0 + 0.01  # W_max + tolerance

    def test_empty_slots_trivial(self):
        """Zero available hours → infeasible-ish? No, soft constraint says trivial."""
        result = solve_schedule({
            "subjects": [{"id": "s1", "required_hours": 2, "deadline_day": 1,
                          "difficulty": 3, "priority": 3, "urgency": 0.5}],
            "time_slots": [{"day": 0, "slot": 0, "tod_factor": 1.0, "available_hours": 0}],
            "max_daily_hours": 4.0,
        })
        # With soft deadline, this is feasible but with shortfall
        assert result["status"] == "optimal"
        assert result["warnings"]


@pytest.mark.integration
class TestWarnings:
    def test_tight_deadline_produces_warning(self):
        """Deadline too tight → shortfall warning."""
        result = solve_schedule({
            "subjects": [{
                "id": "urgent",
                "required_hours": 20,  # needs 20h
                "deadline_day": 0,     # today only
                "difficulty": 4,
                "priority": 5,
                "urgency": 1.0,
            }],
            "time_slots": [
                {"day": 0, "slot": 0, "tod_factor": 1.2, "available_hours": 2},
                {"day": 0, "slot": 1, "tod_factor": 1.0, "available_hours": 2},
                {"day": 0, "slot": 2, "tod_factor": 0.8, "available_hours": 2},
            ],
            "max_daily_hours": 4.0,
        })
        assert result["status"] == "optimal"
        assert any(w["type"] == "deadline_shortfall" for w in result["warnings"])


@pytest.mark.integration
class TestBoundaryCases:
    def test_no_study_after_deadline(self):
        """Subject due day 1 should not be studied on day 2."""
        result = solve_schedule({
            "subjects": [{
                "id": "s1", "required_hours": 2, "deadline_day": 1,
                "difficulty": 3, "priority": 5, "urgency": 0.5,
            }],
            "time_slots": [
                {"day": 0, "slot": 0, "tod_factor": 1.0, "available_hours": 2},
                {"day": 1, "slot": 0, "tod_factor": 1.0, "available_hours": 2},
                {"day": 2, "slot": 0, "tod_factor": 1.0, "available_hours": 2},
            ],
            "max_daily_hours": 4.0,
        })
        for entry in result["schedule"]:
            assert entry["day"] <= 1

    def test_subject_buffer_respected(self):
        """Cannot study more than R[i] × (1 + buffer)."""
        result = solve_schedule({
            "subjects": [{
                "id": "s1", "required_hours": 2, "deadline_day": 10,
                "difficulty": 5, "priority": 5, "urgency": 1 / 11,
            }],
            "time_slots": [
                {"day": d, "slot": t, "tod_factor": tod, "available_hours": 2}
                for d in range(5) for t, tod in enumerate([1.2, 1.0, 0.8])
            ],
            "max_daily_hours": 4.0,
            "buffer_ratio": 0.25,
        })
        # Max allowed = 2 × 1.25 = 2.5h
        total_hours = sum(e["hours"] for e in result["schedule"])
        assert total_hours <= 2.5 + 0.01


@pytest.mark.integration
class TestNonUniqueness:
    def test_thesis_example_many_optima(self, thesis_example_payload):
        """Multiple runs may give different schedules but same objective."""
        r1 = solve_schedule(thesis_example_payload)
        r2 = solve_schedule(thesis_example_payload)
        # Both optimal, similar objective
        assert r1["status"] == "optimal"
        assert r2["status"] == "optimal"
        assert abs(r1["objective_value"] - r2["objective_value"]) < 0.01


@pytest.mark.integration
class TestDefaultConsistency:
    """
    Regression test: fallback defaults in solve_schedule must match
    DEFAULT_* constants in model.py.

    Previous bug: solve_schedule hardcoded lambda_daily=5.0 while
    model.py had DEFAULT_LAMBDA_DAILY=100.0 → HTTP path used 100.0
    (Pydantic default) but direct dict call used 5.0 → inconsistent
    results, silent bug.
    """

    def test_defaults_match_constants(self):
        """solve_schedule with no lambdas must match build_model defaults."""
        from app.model import DEFAULT_LAMBDA_DAILY, DEFAULT_LAMBDA_DEADLINE
        from app.solver import solve_schedule

        input_data = {
            "subjects": [{
                "id": "s1", "required_hours": 2, "deadline_day": 0,
                "difficulty": 4, "priority": 5, "urgency": 1.0,
            }],
            "time_slots": [
                {"day": 0, "slot": t, "tod_factor": tod, "available_hours": 2}
                for t, tod in enumerate([1.2, 1.0, 0.8])
            ],
            "max_daily_hours": 4.0,
        }
        # Should NOT overflow despite having extra capacity in slots
        result = solve_schedule(input_data)
        for day in result["explanation"]["per_day"]:
            assert day["overload"] < 0.01, (
                f"Day {day['day']} overflowed — check that solve_schedule "
                f"uses DEFAULT_LAMBDA_DAILY ({DEFAULT_LAMBDA_DAILY}), not a "
                f"hardcoded value."
            )
