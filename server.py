"""
FastAPI server for Business Strategy Simulation Environment.
Implements full OpenEnv spec: step(), reset(), state() + /baseline, /grader, /tasks
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import uvicorn

from environment import BusinessStrategyEnv
from graders import run_grader, GRADERS

app = FastAPI(
    title="Business Strategy Simulation Environment",
    description="An OpenEnv-compliant environment where an AI agent makes strategic business decisions.",
    version="1.0.0",
)

# In-memory session store (one env per task)
_envs: Dict[str, BusinessStrategyEnv] = {}


def get_env(task: str) -> BusinessStrategyEnv:
    if task not in _envs:
        _envs[task] = BusinessStrategyEnv(task=task)
    return _envs[task]


# ─── Request / Response Models ───────────────────────────────────────────────

class ResetRequest(BaseModel):
    task: str = Field(default="survive", description="Task name: survive | grow_market_share | scale_profitably")
    seed: int = Field(default=42, description="Random seed for reproducibility")

class StepRequest(BaseModel):
    task: str = Field(default="survive")
    action: str = Field(..., description="Action to take. See /tasks for valid actions.")
    amount: float = Field(default=5000.0, description="Dollar amount for the action (where applicable)")

class GraderRequest(BaseModel):
    task: str = Field(..., description="Task to grade")


# ─── Core OpenEnv Endpoints ───────────────────────────────────────────────────

@app.get("/", summary="Health check")
def root():
    return {"status": "ok", "environment": "BusinessStrategyEnv", "version": "1.0.0"}

@app.post("/reset", summary="Reset the environment")
def reset(req: ResetRequest):
    """Reset the environment for a given task and return the initial state."""
    valid_tasks = list(GRADERS.keys())
    if req.task not in valid_tasks:
        raise HTTPException(status_code=400, detail=f"Invalid task '{req.task}'. Valid: {valid_tasks}")
    env = BusinessStrategyEnv(task=req.task, seed=req.seed)
    _envs[req.task] = env
    return env.reset()

@app.post("/step", summary="Take an action in the environment")
def step(req: StepRequest):
    """Submit an action and advance the environment by one quarter."""
    env = get_env(req.task)
    result = env.step(action=req.action, amount=req.amount)
    return result

@app.get("/state", summary="Get current environment state")
def state(task: str = "survive"):
    """Return the current state without advancing the environment."""
    env = get_env(task)
    return env.state()


# ─── Additional Required Endpoints ───────────────────────────────────────────

@app.get("/tasks", summary="List all tasks and action schemas")
def tasks():
    """Returns all available tasks, their descriptions, and the action schema."""
    return {
        "tasks": [
            {
                "id": "survive",
                "name": "Survive 4 Quarters",
                "difficulty": "easy",
                "description": "Keep the company profitable (profit > 0) for all 4 quarters.",
                "max_quarters": 4,
                "success_metric": "Profit > 0 each quarter",
            },
            {
                "id": "grow_market_share",
                "name": "Grow Market Share",
                "difficulty": "medium",
                "description": "Reach 20% market share within 8 quarters.",
                "max_quarters": 8,
                "success_metric": "market_share >= 0.20",
            },
            {
                "id": "scale_profitably",
                "name": "Scale Profitably",
                "difficulty": "hard",
                "description": "Double revenue AND maintain customer satisfaction >= 0.8 within 12 quarters.",
                "max_quarters": 12,
                "success_metric": "revenue >= 100000 AND customer_satisfaction >= 0.8",
            },
        ],
        "action_schema": {
            "action": {
                "type": "string",
                "required": True,
                "valid_values": BusinessStrategyEnv.ACTIONS,
                "description": "The strategic action to take this quarter.",
            },
            "amount": {
                "type": "float",
                "required": False,
                "default": 5000.0,
                "description": "Dollar amount associated with the action (e.g., marketing spend, investment).",
            },
        },
        "observation_space": {
            "revenue": "float — quarterly revenue in USD",
            "costs": "float — total quarterly costs in USD",
            "profit": "float — revenue minus costs",
            "market_share": "float [0.0–1.0] — fraction of total market",
            "employees": "int — number of employees",
            "customer_satisfaction": "float [0.0–1.0]",
            "marketing_budget": "float — current marketing spend",
            "rd_investment": "float — current R&D spend",
            "product_quality": "float [0.0–1.0]",
            "quarter": "int — current quarter number",
            "max_quarters": "int — max quarters for this task",
            "done": "bool — whether episode has ended",
            "reward": "float [0.0–1.0] — reward for this step",
            "message": "str — human-readable summary of the quarter",
        },
    }


@app.post("/grader", summary="Grade a completed episode")
def grader(req: GraderRequest):
    """Run the grader on the current episode state and return a score [0.0–1.0]."""
    env = get_env(req.task)
    final_state = env.state()
    result = run_grader(task=req.task, history=env.history, final_state=final_state)
    return result


@app.get("/baseline", summary="Run baseline agent and return scores for all tasks")
def baseline():
    """
    Runs a simple rule-based baseline agent on all 3 tasks.
    Returns reproducible baseline scores.
    """
    from baseline import run_baseline_agent
    scores = {}
    for task in GRADERS.keys():
        scores[task] = run_baseline_agent(task=task, seed=42)
    return {"baseline_scores": scores, "agent": "rule_based_v1"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=7860, reload=False)
     
# ✅ Health Endpoint
@app.get("/health")
def health():
    return {"status": "healthy"}

# ✅ Metadata Endpoint
@app.get("/metadata")
def metadata():
    return {
        "name": "Business Strategy Env",
        "description": "AI-powered business strategy simulation environment"
    }

# ✅ Schema Endpoint
@app.get("/schema")
def schema():
    return {
        "action": {"type": "object"},
        "observation": {"type": "object"},
        "state": {"type": "object"}
    }

# ✅ MCP Endpoint
@app.post("/mcp")
def mcp():
    return {
        "jsonrpc": "2.0",
        "result": "ok"
    }