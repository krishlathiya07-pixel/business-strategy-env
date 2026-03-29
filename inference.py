"""
inference.py — OpenEnv Hackathon Round 1
Business Strategy Simulation Environment

Uses OpenAI-compatible client to run an LLM agent against all 3 tasks.
Reads credentials from environment variables:
  - API_BASE_URL   : The API endpoint for the LLM
  - MODEL_NAME     : The model identifier to use
  - HF_TOKEN       : Your Hugging Face / API key
"""

import os
import json
import requests
from openai import OpenAI

# ─── Configuration ────────────────────────────────────────────────────────────

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api-inference.huggingface.co/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")
ENV_URL      = os.environ.get("ENV_URL", "https://ihere04u-business-strategy-env.hf.space")

MAX_STEPS    = 12
TEMPERATURE  = 0.2
MAX_TOKENS   = 512
FALLBACK_ACTION = '{"action": "increase_marketing", "amount": 5000}'

TASKS = ["survive", "grow_market_share", "scale_profitably"]

# ─── OpenAI Client ────────────────────────────────────────────────────────────

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
)

# ─── Prompts ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a strategic business advisor AI. 
You are controlling a company and must make quarterly decisions to achieve business goals.

Available actions:
- increase_marketing
- decrease_marketing
- hire_employees
- layoff_employees
- cut_costs
- invest_in_rd
- launch_product
- expand_market
- raise_prices
- lower_prices

You must respond with ONLY a valid JSON object like:
{"action": "increase_marketing", "amount": 5000}

The amount field is optional (default 5000). Choose the best action based on the current state."""


def build_user_prompt(step: int, state: dict, history: list, task: str) -> str:
    return f"""Task: {task}
Step: {step}

Current Company State:
- Revenue: ${state.get('revenue', 0):,.0f}
- Costs: ${state.get('costs', 0):,.0f}
- Profit: ${state.get('profit', 0):,.0f}
- Market Share: {state.get('market_share', 0)*100:.1f}%
- Employees: {state.get('employees', 0)}
- Customer Satisfaction: {state.get('customer_satisfaction', 0):.2f}
- Product Quality: {state.get('product_quality', 0):.2f}
- Quarter: {state.get('quarter', 0)} / {state.get('max_quarters', 0)}
- Last Message: {state.get('message', '')}

Recent History:
{chr(10).join(history[-3:]) if history else 'No history yet.'}

What action should the company take this quarter? Respond with JSON only."""


def parse_action(response_text: str) -> dict:
    """Extract JSON action from model response."""
    try:
        # Try direct parse
        return json.loads(response_text.strip())
    except Exception:
        pass
    try:
        # Try extracting JSON from text
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response_text[start:end])
    except Exception:
        pass
    # Fallback
    return json.loads(FALLBACK_ACTION)


# ─── Environment API Calls ────────────────────────────────────────────────────

def env_reset(task: str, seed: int = 42) -> dict:
    r = requests.post(f"{ENV_URL}/reset", json={"task": task, "seed": seed})
    r.raise_for_status()
    return r.json()

def env_step(task: str, action: str, amount: float = 5000.0) -> dict:
    r = requests.post(f"{ENV_URL}/step", json={"task": task, "action": action, "amount": amount})
    r.raise_for_status()
    return r.json()

def env_grader(task: str) -> dict:
    r = requests.post(f"{ENV_URL}/grader", json={"task": task})
    r.raise_for_status()
    return r.json()


# ─── Main Agent Loop ──────────────────────────────────────────────────────────

def run_task(task: str, seed: int = 42) -> dict:
    print(f"\n{'='*60}")
    print(f"Task: {task}")
    print(f"{'='*60}")

    observation = env_reset(task=task, seed=seed)
    history = []
    total_reward = 0.0

    for step in range(1, MAX_STEPS + 1):
        if observation.get("done", False):
            print("Environment signalled done. Stopping early.")
            break

        user_prompt = build_user_prompt(step, observation, history, task)

        messages = [
            {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
            {"role": "user",   "content": [{"type": "text", "text": user_prompt}]},
        ]

        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as exc:
            print(f"Model request failed ({exc}). Using fallback action.")
            response_text = FALLBACK_ACTION

        action_dict = parse_action(response_text)
        action_str  = action_dict.get("action", "increase_marketing")
        amount      = float(action_dict.get("amount", 5000.0))

        print(f"Step {step}: model suggested -> {action_str} (amount: {amount})")

        observation = env_step(task=task, action=action_str, amount=amount)
        reward = observation.get("reward", 0.0)
        total_reward += reward

        history_line = f"Step {step}: {action_str} -> reward {reward:+.2f} | profit ${observation.get('profit', 0):,.0f}"
        history.append(history_line)

        print(f"  Reward: {reward:+.2f} | Done: {observation.get('done')} | {observation.get('message','')}")

        if observation.get("done", False):
            print("Episode complete.")
            break
    else:
        print(f"Reached max steps ({MAX_STEPS}).")

    # Grade the episode
    grade = env_grader(task=task)

    result = {
        "task": task,
        "score": grade.get("score", 0.0),
        "reason": grade.get("reason", ""),
        "steps_taken": len(history),
        "total_reward": round(total_reward, 3),
        "final_state": {
            "profit": observation.get("profit", 0),
            "revenue": observation.get("revenue", 0),
            "market_share": observation.get("market_share", 0),
            "customer_satisfaction": observation.get("customer_satisfaction", 0),
        }
    }

    print(f"\nFinal Score: {result['score']:.3f}")
    print(f"Reason: {result['reason']}")
    return result


def main():
    print("Business Strategy Env — LLM Agent Inference")
    print(f"Model    : {MODEL_NAME}")
    print(f"Base URL : {API_BASE_URL}")
    print(f"Env URL  : {ENV_URL}")

    if not HF_TOKEN:
        print("WARNING: HF_TOKEN not set. Set it as an environment variable.")

    all_results = {}

    for task in TASKS:
        try:
            result = run_task(task=task, seed=42)
            all_results[task] = result
        except Exception as e:
            print(f"ERROR on task {task}: {e}")
            all_results[task] = {"task": task, "score": 0.0, "error": str(e)}

    # Summary
    print(f"\n{'='*60}")
    print("INFERENCE COMPLETE — Summary")
    print(f"{'='*60}")
    for task, result in all_results.items():
        print(f"{task:30s} → Score: {result.get('score', 0):.3f}")

    avg = sum(r.get("score", 0) for r in all_results.values()) / len(all_results)
    print(f"\nAverage Score: {avg:.3f}")
    print(f"{'='*60}")

    return all_results


if __name__ == "__main__":
    main()