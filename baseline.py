"""
Baseline inference script for Business Strategy Simulation Environment.
Uses a simple rule-based agent to produce reproducible scores across all 3 tasks.

Run directly:
    python baseline.py

Or called from server.py /baseline endpoint.
"""

from environment import BusinessStrategyEnv
from graders import run_grader, GRADERS


def rule_based_agent(state: dict, task: str) -> dict:
    """
    Simple rule-based agent that makes decisions based on the current state.
    No ML — purely heuristic. Serves as a reproducible baseline.
    """
    profit = state["profit"]
    market_share = state["market_share"]
    satisfaction = state["customer_satisfaction"]
    revenue = state["revenue"]
    costs = state["costs"]
    quarter = state["quarter"]

    # Task-specific strategy
    if task == "survive":
        # Priority: stay profitable
        if profit < 0:
            return {"action": "cut_costs", "amount": 5000}
        elif costs / revenue > 0.85:
            return {"action": "cut_costs", "amount": 3000}
        else:
            return {"action": "increase_marketing", "amount": 3000}

    elif task == "grow_market_share":
        # Priority: grow market share aggressively
        if market_share < 0.15:
            return {"action": "expand_market", "amount": 8000}
        elif satisfaction < 0.6:
            return {"action": "lower_prices", "amount": 0}
        else:
            return {"action": "increase_marketing", "amount": 6000}

    elif task == "scale_profitably":
        # Priority: grow revenue while maintaining satisfaction
        if satisfaction < 0.8:
            if quarter < 6:
                return {"action": "invest_in_rd", "amount": 5000}
            else:
                return {"action": "lower_prices", "amount": 0}
        elif revenue < 80000:
            return {"action": "launch_product", "amount": 10000}
        else:
            return {"action": "expand_market", "amount": 8000}

    # Fallback
    return {"action": "increase_marketing", "amount": 3000}


def run_baseline_agent(task: str, seed: int = 42) -> dict:
    """
    Run the rule-based baseline agent on a single task.
    Returns grader result with score.
    """
    env = BusinessStrategyEnv(task=task, seed=seed)
    state = env.reset()

    while not state.get("done", False):
        action_dict = rule_based_agent(state, task)
        state = env.step(**action_dict)

    result = run_grader(task=task, history=env.history, final_state=state)
    return {
        "task": task,
        "score": result["score"],
        "reason": result["reason"],
        "quarters_played": len(env.history),
        "final_state": {
            "profit": state["profit"],
            "revenue": state["revenue"],
            "market_share": state["market_share"],
            "customer_satisfaction": state["customer_satisfaction"],
        },
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Business Strategy Env — Baseline Agent Results")
    print("=" * 60)

    for task in GRADERS.keys():
        result = run_baseline_agent(task=task, seed=42)
        print(f"\nTask: {task}")
        print(f"  Score       : {result['score']:.3f}")
        print(f"  Quarters    : {result['quarters_played']}")
        print(f"  Reason      : {result['reason']}")
        print(f"  Final Profit: ${result['final_state']['profit']:,.0f}")
        print(f"  Market Share: {result['final_state']['market_share']*100:.1f}%")
        print(f"  Satisfaction: {result['final_state']['customer_satisfaction']:.2f}")

    print("\n" + "=" * 60)
    print("Baseline complete.")