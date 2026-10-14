"""
Risk score calculator — pure functions, no side effects.

Formula:
    Risk Score = 100 × (w1·SD + w2·WD + w3·DP + w4·SI)

Where:
    SD = Normalized Sleep Deficit        ∈ [0, 1]
    WD = Normalized Workload Density     ∈ [0, 1]
    DP = Normalized Deadline Proximity   ∈ (0, 1]
    SI = Normalized Study Inconsistency  ∈ [0, 1]

Weights (from educational psychology literature):
    w1 = 0.35  (Sleep deficit — highest impact on cognitive function)
    w2 = 0.30  (Workload density — direct indicator of stress)
    w3 = 0.20  (Deadline proximity — contributes but decreases after deadline)
    w4 = 0.15  (Study inconsistency — indirect via study quality)

IMPORTANT DISCLAIMER:
    This indicator reflects workload stress level based on self-reported
    behavioral data. It is NOT a medical or psychological diagnosis.
    It is NOT a substitute for professional consultation.
"""
from dataclasses import dataclass


# ============================================================
# WEIGHTS (chosen from educational psychology literature)
# ============================================================
W_SLEEP_DEFICIT = 0.35
W_WORKLOAD_DENSITY = 0.30
W_DEADLINE_PROXIMITY = 0.20
W_STUDY_INCONSISTENCY = 0.15


# ============================================================
# NORMALIZATION CONSTANTS
# ============================================================
# Recommended sleep for adults: 7-8h/day
SLEEP_RECOMMENDED_HOURS = 7.0
# A 4h deficit is considered maximum (based on sleep literature)
SLEEP_DEFICIT_MAX_HOURS = 4.0
# A std of 3h in daily study hours is considered maximum inconsistency
STUDY_STD_MAX_HOURS = 3.0


DISCLAIMER = (
    "Chỉ báo này phản ánh mức độ căng thẳng do khối lượng công việc dựa trên "
    "dữ liệu hành vi tự báo cáo. Đây KHÔNG phải là chẩn đoán y tế hoặc tâm lý. "
    "Kết quả chỉ mang tính tham khảo để hỗ trợ quản lý thời gian và không thay "
    "thế tư vấn chuyên nghiệp. Nếu bạn cảm thấy kiệt sức kéo dài, mất động lực "
    "học tập, hoặc lo lắng quá mức, hãy liên hệ với chuyên gia tư vấn tâm lý "
    "hoặc bác sĩ."
)


# ============================================================
# NORMALIZATION FUNCTIONS (each maps to [0, 1])
# ============================================================

def normalize_sleep_deficit(sleep_hours: float) -> float:
    """
    Normalize sleep deficit to [0, 1].

    deficit = max(0, 7 - sleep_hours)    # hours below recommendation
    normalized = min(1, deficit / 4)     # 4h deficit = maximum

    Examples:
        sleep_hours=8  → 0.0  (no deficit)
        sleep_hours=7  → 0.0  (at recommendation)
        sleep_hours=5  → 0.5  (2h deficit / 4)
        sleep_hours=3  → 1.0  (4h+ deficit = max)
    """
    if sleep_hours < 0:
        raise ValueError("sleep_hours must be >= 0")

    deficit = max(0.0, SLEEP_RECOMMENDED_HOURS - sleep_hours)
    return min(1.0, deficit / SLEEP_DEFICIT_MAX_HOURS)


def normalize_workload_density(
    required_hours: float,
    available_hours: float,
) -> float:
    """
    Normalize workload density to [0, 1].

    density = required_hours / available_hours
    normalized = min(1, density)

    Examples:
        required=10, available=40  → 0.25  (low density)
        required=20, available=40  → 0.50
        required=40, available=40  → 1.00  (fully packed)
        required=50, available=40  → 1.00  (capped)
    """
    if required_hours < 0:
        raise ValueError("required_hours must be >= 0")
    if available_hours <= 0:
        # Edge case: no available time → maximum density
        return 1.0

    density = required_hours / available_hours
    return min(1.0, density)


def normalize_deadline_proximity(days_until_deadline: int) -> float:
    """
    Normalize deadline proximity to (0, 1].

    Formula: 1 / (1 + days_until_deadline)

    Examples:
        days=0   → 1.000  (deadline today — maximum urgency)
        days=1   → 0.500
        days=2   → 0.333
        days=7   → 0.125
        days=30  → 0.032  (far away)
    """
    if days_until_deadline < 0:
        # Deadline in the past — treat as maximum urgency
        return 1.0

    return 1.0 / (1.0 + days_until_deadline)


def normalize_study_inconsistency(study_std: float) -> float:
    """
    Normalize study inconsistency to [0, 1].

    std = standard deviation of daily study hours over past week
    normalized = min(1, std / 3)

    Examples:
        std=0.0  → 0.0  (perfectly consistent)
        std=0.5  → 0.17 (very consistent)
        std=1.5  → 0.50
        std=3.0  → 1.0  (maximum inconsistency)
        std=5.0  → 1.0  (capped)
    """
    if study_std < 0:
        raise ValueError("study_std must be >= 0")

    return min(1.0, study_std / STUDY_STD_MAX_HOURS)


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_risk(score: float) -> str:
    """
    Classify risk score into 3 levels.

    0-30:   "low"      (green)
    31-60:  "moderate" (yellow/orange)
    61-100: "high"     (red)
    """
    if score <= 30:
        return "low"
    elif score <= 60:
        return "moderate"
    else:
        return "high"


# ============================================================
# MAIN CALCULATOR
# ============================================================

@dataclass
class RiskResult:
    """Result of risk calculation with full breakdown."""
    risk_score: float
    level: str
    components: dict  # normalized inputs
    weights: dict


def calculate_risk_score(
    sd_norm: float,
    wd_norm: float,
    dp_norm: float,
    si_norm: float,
) -> float:
    """
    Compute weighted risk score in [0, 100].

    Args:
        sd_norm: normalized sleep deficit ∈ [0, 1]
        wd_norm: normalized workload density ∈ [0, 1]
        dp_norm: normalized deadline proximity ∈ (0, 1]
        si_norm: normalized study inconsistency ∈ [0, 1]

    Returns:
        Risk score in [0, 100], rounded to 2 decimal places.

    Note: This function expects ALREADY NORMALIZED inputs.
          Use `compute_risk()` for full pipeline with raw inputs.
    """
    score = 100.0 * (
        W_SLEEP_DEFICIT * sd_norm
        + W_WORKLOAD_DENSITY * wd_norm
        + W_DEADLINE_PROXIMITY * dp_norm
        + W_STUDY_INCONSISTENCY * si_norm
    )
    return round(score, 2)


def compute_risk(
    sleep_hours: float,
    required_hours: float,
    available_hours: float,
    days_until_deadline: int,
    study_std: float,
) -> RiskResult:
    """
    Full pipeline: raw inputs → normalized → weighted → classified.

    Args:
        sleep_hours: average sleep hours/day over past week
        required_hours: total hours needed to finish upcoming work
        available_hours: total hours available before deadline
        days_until_deadline: days remaining to the nearest deadline
        study_std: std deviation of daily study hours (past 7 days)

    Returns:
        RiskResult with score, level, breakdown of components
    """
    sd = normalize_sleep_deficit(sleep_hours)
    wd = normalize_workload_density(required_hours, available_hours)
    dp = normalize_deadline_proximity(days_until_deadline)
    si = normalize_study_inconsistency(study_std)

    score = calculate_risk_score(sd, wd, dp, si)
    level = classify_risk(score)

    return RiskResult(
        risk_score=score,
        level=level,
        components={
            "sleep_deficit": round(sd, 4),
            "workload_density": round(wd, 4),
            "deadline_proximity": round(dp, 4),
            "study_inconsistency": round(si, 4),
        },
        weights={
            "sleep_deficit": W_SLEEP_DEFICIT,
            "workload_density": W_WORKLOAD_DENSITY,
            "deadline_proximity": W_DEADLINE_PROXIMITY,
            "study_inconsistency": W_STUDY_INCONSISTENCY,
        },
    )
