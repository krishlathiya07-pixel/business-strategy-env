import os
import json
import requests

# ─── Config ─────────────────────────────────────────

ENV_URL      = os.environ.get("ENV_URL", "https://ihere04u-business-strategy-env.hf.space")
MAX_STEPS   = 12

FALLBACK_ACTION = {"action": "increase_marketing", "amount": 5000}
TASKS = ["survive", "grow_market_share", "scale_profitably"]

# ─── Rule-Based Action ──────────────────────────────────────────────────────

def choose_action(obs, task, last_action=None):
    profit       = obs.get("profit", 0)
    costs        = obs.get("costs", 0)
    market_share = obs.get("market_share", 0)
    satisfaction = obs.get("customer_satisfaction", 0)
    quality      = obs.get("product_quality", 0)
    revenue      = obs.get("revenue", 0)
    quarter      = obs.get("quarter", 0)

    # ── Critical fixes ──
    if profit < 0:
        act = {"action": "cut_costs", "amount": 6000}
    elif task != "grow_market_share" and costs > revenue * 0.85:
        act = {"action": "cut_costs", "amount": 4000}
        
    # ── Task logic ──
    elif task == "survive":
        if profit < 3000:
            act = {"action": "cut_costs", "amount": 3000}
        elif satisfaction < 0.65:
            act = {"action": "invest_in_rd", "amount": 4000}
        elif market_share < 0.15:
            act = {"action": "increase_marketing", "amount": 5000}
        else:
            rotation = ["launch_product", "raise_prices", "invest_in_rd"]
            act = {"action": rotation[quarter % len(rotation)], "amount": 4000}

    elif task == "grow_market_share":
        if market_share < 0.10:
            act = {"action": "expand_market", "amount": 9000}
        elif market_share < 0.20:
            act = {"action": "increase_marketing", "amount": 7000}
        elif market_share < 0.30:
            if last_action == "increase_marketing":
                act = {"action": "expand_market", "amount": 8000}
            elif last_action == "expand_market":
                act = {"action": "increase_marketing", "amount": 7000}
            else:
                act = {"action": "expand_market", "amount": 7000}
        elif satisfaction < 0.7:
            act = {"action": "invest_in_rd", "amount": 5000}
        else:
            act = {"action": "launch_product", "amount": 5000}

    elif task == "scale_profitably":
        if satisfaction < 0.65:
            act = {"action": "invest_in_rd", "amount": 7000}
        elif quality < 0.6:
            act = {"action": "invest_in_rd", "amount": 6000}
        elif market_share < 0.15:
            act = {"action": "expand_market", "amount": 7000}
        elif satisfaction >= 0.8 and profit > 0:
            # 🔥 SAFE pricing logic (fixed)
            if profit < 10000:
                act = {"action": "expand_market", "amount": 6000}
            elif profit > 15000 and satisfaction > 0.85:
                act = {"action": "raise_prices", "amount": 4000}
            else:
                act = {"action": "launch_product", "amount": 6000}
        else:
            act = {"action": "increase_marketing", "amount": 5000}

    else:
        if market_share < 0.3:
            act = {"action": "increase_marketing", "amount": 5000}
        else:
            act = {"action": "expand_market", "amount": 5000}

    # ── Anti-repetition safety ──
    if last_action == act.get("action"):
        alternatives = [
            "increase_marketing",
            "cut_costs",
            "expand_market",
            "invest_in_rd"
        ]
        for alt in alternatives:
            if alt != last_action:
                return {"action": alt, "amount": 5000}

    return act


# ─── Prompt (LLM fallback only) ─────────────────────────────────────────────

# ─── API Calls ──────────────────────────────────────

def env_reset(task):
    return requests.post(f"{ENV_URL}/reset", json={"task": task, "seed": 42}).json()

def env_step(task, action, amount):
    return requests.post(f"{ENV_URL}/step", json={"task": task, "action": action, "amount": amount}).json()

def env_grader(task):
    return requests.post(f"{ENV_URL}/grader", json={"task": task}).json()


# ─── Core Loop ──────────────────────────────────────

def run_task(task):
    print(f"[START] task={task} env=business-strategy-env", flush=True)

    rewards     = []
    obs         = env_reset(task)
    last_action = None

    for step in range(1, MAX_STEPS + 1):
        if obs.get("done"):
            break

        act = choose_action(obs, task, last_action)
        action = act.get("action", "increase_marketing")
        amount = float(act.get("amount", 5000))

        # 🔥 Safe env_step
        try:
            obs = env_step(task, action, amount)
        except Exception:
            obs = {"reward": 0.0, "done": True}

        reward = float(obs.get("reward", 0.0))
        rewards.append(reward)
        done = str(obs.get("done", False)).lower()
        last_action = action

        print(
            f"[STEP] step={step} action={action} reward={reward:.2f} done={done} error=null",
            flush=True
        )

        if obs.get("done"):
            break

    # 🔥 Safe grader
    try:
        grade = env_grader(task)
        score = float(grade.get("score", 0.0))
    except Exception:
        score = 0.0

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success     = str(score >= 0.1).lower()

    print(
        f"[END] success={success} steps={len(rewards)} score={score:.3f} rewards={rewards_str}",
        flush=True
    )


# ─── Main ───────────────────────────────────────────

def main():
    for task in TASKS:
        try:
            run_task(task)
        except Exception:
            print("[END] success=false steps=0 score=0.000 rewards=", flush=True)


if __name__ == "__main__":
    main()