"""
Graders for the Business Strategy Simulation Environment.
Each grader evaluates an episode and returns a score in (0.0, 1.0) exclusive.
"""

from typing import Any, Dict, List


def _clamp(score: float) -> float:
    """Clamp score to strictly (0, 1) — never 0.0 or 1.0."""
    return max(0.001, min(score, 0.999))


def grade_survive(history: List[Dict], final_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Task: Survive — Keep profit > 0 for all 4 quarters.
    Score = (profitable quarters) / (total quarters played)
    """
    if not history:
        return {"score": _clamp(0.0), "reason": "No history recorded."}

    profitable = sum(1 for h in history if h["profit"] > 0)
    total = len(history)
    score = _clamp(round(profitable / total, 3))

    return {
        "score": score,
        "profitable_quarters": profitable,
        "total_quarters": total,
        "final_profit": final_state.get("profit", 0),
        "reason": f"Profitable in {profitable}/{total} quarters.",
    }


def grade_grow_market_share(history: List[Dict], final_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Task: Grow Market Share — Reach 20% market share within 8 quarters.
    Score = min(final_market_share / 0.20, 1.0)
    Bonus: +0.1 if achieved before quarter 8.
    """
    if not history:
        return {"score": _clamp(0.0), "reason": "No history recorded."}

    final_share = final_state.get("market_share", 0.0)
    base_score = min(final_share / 0.20, 1.0)

    # Bonus for early achievement
    bonus = 0.0
    for h in history:
        if h["market_share"] >= 0.20:
            bonus = round(0.1 * (1 - h["quarter"] / 8), 3)
            break

    score = _clamp(round(min(base_score + bonus, 1.0), 3))

    return {
        "score": score,
        "final_market_share": round(final_share * 100, 2),
        "target_market_share": 20.0,
        "early_bonus": bonus,
        "reason": f"Reached {final_share*100:.1f}% market share (target: 20%).",
    }


def grade_scale_profitably(history: List[Dict], final_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Task: Scale Profitably — 2x revenue AND customer satisfaction >= 0.8 in 12 quarters.
    Score = weighted average of revenue_score (60%) + satisfaction_score (40%).
    """
    if not history:
        return {"score": _clamp(0.0), "reason": "No history recorded."}

    initial_revenue = 50000.0  # baseline at start
    final_revenue = final_state.get("revenue", initial_revenue)
    final_satisfaction = final_state.get("customer_satisfaction", 0.0)

    # Revenue score: 2x = full score
    revenue_score = min(final_revenue / (initial_revenue * 2), 1.0)

    # Satisfaction score
    if final_satisfaction >= 0.8:
        sat_score = 1.0
    elif final_satisfaction >= 0.6:
        sat_score = 0.5 + (final_satisfaction - 0.6) * 2.5
    else:
        sat_score = final_satisfaction / 0.6 * 0.5

    score = _clamp(round(0.6 * revenue_score + 0.4 * sat_score, 3))

    return {
        "score": score,
        "final_revenue": round(final_revenue, 2),
        "target_revenue": initial_revenue * 2,
        "revenue_score": round(revenue_score, 3),
        "final_customer_satisfaction": final_satisfaction,
        "satisfaction_score": round(sat_score, 3),
        "reason": (
            f"Revenue: ${final_revenue:,.0f} (target: ${initial_revenue*2:,.0f}), "
            f"Satisfaction: {final_satisfaction:.2f} (target: 0.80)."
        ),
    }


GRADERS = {
    "survive": grade_survive,
    "grow_market_share": grade_grow_market_share,
    "scale_profitably": grade_scale_profitably,
}


def run_grader(task: str, history: list, final_state: dict) -> dict:
    """Run the appropriate grader for a given task."""
    if task not in GRADERS:
        return {"score": _clamp(0.0), "reason": f"Unknown task '{task}'. Valid: {list(GRADERS.keys())}"}
    return GRADERS[task](history, final_state)