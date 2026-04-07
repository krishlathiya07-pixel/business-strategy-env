"""
Business Strategy Simulation Environment
Core environment logic implementing OpenEnv spec.
"""

import random
from typing import Any, Dict, Optional

try:
    from openenv.core import Environment as Env
except ImportError:
    from openenv_fallback import Env

class BusinessStrategyEnv(Env):
    """
    Simulates a company operating over multiple quarters.
    An AI agent must make strategic decisions to achieve business goals.
    """

    ACTIONS = [
        "increase_marketing",
        "decrease_marketing",
        "hire_employees",
        "layoff_employees",
        "cut_costs",
        "invest_in_rd",
        "launch_product",
        "expand_market",
        "raise_prices",
        "lower_prices",
    ]

    def __init__(self, task: str = "survive", seed: int = 42):
        self.task = task
        self.seed = seed
        self.rng = random.Random(seed)
        self.state_data: Dict[str, Any] = {}
        self.current_quarter = 0
        self.max_quarters = self._get_max_quarters()
        self.done = False
        self.history = []
        self.reset()

    def _get_max_quarters(self) -> int:
        return {"survive": 4, "grow_market_share": 8, "scale_profitably": 12}.get(self.task, 4)

    def reset(self) -> Dict[str, Any]:
        self.rng = random.Random(self.seed)
        self.current_quarter = 0
        self.done = False
        self.history = []

        self.state_data = {
            "revenue": 50000.0,
            "costs": 35000.0,
            "profit": 15000.0,
            "market_share": 0.10,
            "employees": 20,
            "customer_satisfaction": 0.70,
            "marketing_budget": 5000.0,
            "rd_investment": 2000.0,
            "product_quality": 0.65,
            "quarter": 0,
            "max_quarters": self.max_quarters,
            "task": self.task,
            "done": False,
            "message": "Company initialized. Make your first strategic decision.",
        }
        return self.state_data.copy()

    def state(self) -> Dict[str, Any]:
        return self.state_data.copy()

    def step(self, action: str, amount: float = 5000.0) -> Dict[str, Any]:
        if self.done:
            return {**self.state_data, "message": "Episode is over. Call reset() to start again."}

        if action not in self.ACTIONS:
            return {**self.state_data, "message": f"Invalid action '{action}'. Valid: {self.ACTIONS}"}

        # Apply action effects
        self._apply_action(action, amount)

        # Simulate market dynamics for the quarter
        self._simulate_quarter()

        # Advance quarter
        self.current_quarter += 1
        self.state_data["quarter"] = self.current_quarter

        # Compute reward
        reward = self._compute_reward()

        # Check termination
        self.done = self._check_done()
        self.state_data["done"] = self.done
        self.state_data["reward"] = reward

        # Log history
        self.history.append({
            "quarter": self.current_quarter,
            "action": action,
            "amount": amount,
            "reward": reward,
            "profit": self.state_data["profit"],
            "market_share": self.state_data["market_share"],
        })

        return self.state_data.copy()

    def _apply_action(self, action: str, amount: float):
        s = self.state_data

        if action == "increase_marketing":
            spend = min(amount, s["revenue"] * 0.2)
            s["marketing_budget"] += spend
            s["costs"] += spend
            s["market_share"] = min(s["market_share"] + 0.02, 1.0)
            s["customer_satisfaction"] = min(s["customer_satisfaction"] + 0.03, 1.0)

        elif action == "decrease_marketing":
            reduction = min(amount, s["marketing_budget"])
            s["marketing_budget"] -= reduction
            s["costs"] -= reduction
            s["market_share"] = max(s["market_share"] - 0.01, 0.01)

        elif action == "hire_employees":
            new_hires = max(1, int(amount / 3000))
            s["employees"] += new_hires
            s["costs"] += new_hires * 3000
            s["revenue"] = s["revenue"] * (1 + new_hires * 0.02)
            s["customer_satisfaction"] = min(s["customer_satisfaction"] + 0.02, 1.0)

        elif action == "layoff_employees":
            layoffs = min(max(1, int(amount / 3000)), s["employees"] - 5)
            s["employees"] -= layoffs
            s["costs"] -= layoffs * 3000
            s["customer_satisfaction"] = max(s["customer_satisfaction"] - 0.05, 0.0)

        elif action == "cut_costs":
            cut = min(amount, s["costs"] * 0.15)
            s["costs"] -= cut
            s["product_quality"] = max(s["product_quality"] - 0.03, 0.1)

        elif action == "invest_in_rd":
            invest = min(amount, s["revenue"] * 0.2)
            s["rd_investment"] += invest
            s["costs"] += invest
            s["product_quality"] = min(s["product_quality"] + 0.05, 1.0)

        elif action == "launch_product":
            s["costs"] += amount * 0.5
            s["revenue"] += amount * 0.8 * s["product_quality"]
            s["market_share"] = min(s["market_share"] + 0.03, 1.0)

        elif action == "expand_market":
            s["costs"] += amount
            s["market_share"] = min(s["market_share"] + 0.04, 1.0)
            s["revenue"] += amount * 1.2

        elif action == "raise_prices":
            s["revenue"] = s["revenue"] * 1.08
            s["customer_satisfaction"] = max(s["customer_satisfaction"] - 0.04, 0.0)
            s["market_share"] = max(s["market_share"] - 0.01, 0.01)

        elif action == "lower_prices":
            s["revenue"] = s["revenue"] * 0.94
            s["customer_satisfaction"] = min(s["customer_satisfaction"] + 0.04, 1.0)
            s["market_share"] = min(s["market_share"] + 0.02, 1.0)

    def _simulate_quarter(self):
        s = self.state_data
        noise = self.rng.uniform(-0.05, 0.05)

        # Market naturally evolves
        s["revenue"] = s["revenue"] * (1 + 0.02 + noise + s["market_share"] * 0.05)
        s["costs"] = s["costs"] * (1 + 0.01 + self.rng.uniform(0, 0.02))  # inflation

        # Profit derived
        s["profit"] = s["revenue"] - s["costs"]
        s["profit"] = round(s["profit"], 2)
        s["revenue"] = round(s["revenue"], 2)
        s["costs"] = round(s["costs"], 2)
        s["market_share"] = round(min(max(s["market_share"], 0.01), 1.0), 4)
        s["customer_satisfaction"] = round(min(max(s["customer_satisfaction"], 0.0), 1.0), 3)
        s["product_quality"] = round(min(max(s["product_quality"], 0.1), 1.0), 3)

        # Dynamic message
        if s["profit"] < 0:
            s["message"] = f"⚠️ Q{self.current_quarter + 1}: Company is losing money! Profit: ${s['profit']:,.0f}"
        else:
            s["message"] = f"✅ Q{self.current_quarter + 1}: Profit: ${s['profit']:,.0f} | Market Share: {s['market_share']*100:.1f}%"

    def _compute_reward(self) -> float:
        s = self.state_data
        if self.task == "survive":
            return 1.0 if s["profit"] > 0 else 0.0

        elif self.task == "grow_market_share":
            return round(min(s["market_share"] / 0.20, 1.0), 3)

        elif self.task == "scale_profitably":
            rev_score = min(s["revenue"] / 100000.0, 1.0)
            sat_score = s["customer_satisfaction"] if s["customer_satisfaction"] >= 0.8 else s["customer_satisfaction"] * 0.5
            return round((rev_score + sat_score) / 2, 3)

        return 0.0

    def _check_done(self) -> bool:
        s = self.state_data
        if self.current_quarter >= self.max_quarters:
            return True
        if s["profit"] < -50000:
            s["message"] = "💀 Bankruptcy! Company has collapsed."
            return True
        if s["employees"] < 5:
            s["message"] = "💀 Too few employees. Company shut down."
            return True
        return False