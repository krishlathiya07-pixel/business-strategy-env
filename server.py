"""
FastAPI server for Business Strategy Simulation Environment.
Implements full OpenEnv spec with typed Pydantic models.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import uvicorn

from environment import BusinessStrategyEnv
from graders import run_grader, GRADERS

app = FastAPI(
    title="Business Strategy Simulation Environment",
    description="An OpenEnv-compliant environment where an AI agent makes strategic business decisions.",
    version="1.0.0",
)

_envs: Dict[str, BusinessStrategyEnv] = {}

def get_env(task: str) -> BusinessStrategyEnv:
    if task not in _envs:
        _envs[task] = BusinessStrategyEnv(task=task)
    return _envs[task]


# ─── Typed OpenEnv Models ─────────────────────────────────────────────────────

class Observation(BaseModel):
    """Typed observation returned after every step/reset."""
    revenue: float = Field(..., description="Quarterly revenue in USD")
    costs: float = Field(..., description="Total quarterly costs in USD")
    profit: float = Field(..., description="Revenue minus costs")
    market_share: float = Field(..., ge=0.0, le=1.0, description="Fraction of total market")
    employees: int = Field(..., description="Number of employees")
    customer_satisfaction: float = Field(..., ge=0.0, le=1.0)
    marketing_budget: float = Field(..., description="Current marketing spend")
    rd_investment: float = Field(..., description="Current R&D spend")
    product_quality: float = Field(..., ge=0.0, le=1.0)
    quarter: int = Field(..., description="Current quarter number")
    max_quarters: int = Field(..., description="Max quarters for this task")
    task: str = Field(..., description="Current task name")
    done: bool = Field(..., description="Whether the episode has ended")
    reward: float = Field(default=0.0, ge=0.0, le=1.0, description="Reward for this step")
    message: str = Field(default="", description="Human-readable summary")

class Action(BaseModel):
    """Typed action submitted by the agent each step."""
    action: str = Field(..., description="Strategic action to take", examples=["increase_marketing"])
    amount: float = Field(default=5000.0, ge=0.0, description="Dollar amount for the action")

class Reward(BaseModel):
    """Typed reward returned by the grader."""
    score: float = Field(..., ge=0.0, le=1.0, description="Episode score between 0.0 and 1.0")
    reason: str = Field(..., description="Human-readable explanation of the score")

class ResetRequest(BaseModel):
    task: str = Field(default="survive", description="Task: survive | grow_market_share | scale_profitably")
    seed: int = Field(default=42, description="Random seed for reproducibility")

class StepRequest(BaseModel):
    task: str = Field(default="survive")
    action: str = Field(..., description="Action to take")
    amount: float = Field(default=5000.0)

class GraderRequest(BaseModel):
    task: str = Field(..., description="Task to grade")

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: Optional[str] = None
    id: Optional[int] = 1
    params: Optional[Dict[str, Any]] = None


# ─── Health / Metadata / Schema / MCP ────────────────────────────────────────

@app.get("/", summary="Root")
def root():
    return {"status": "ok", "environment": "BusinessStrategyEnv", "version": "1.0.0"}

@app.get("/health", summary="Health check")
def health():
    return {"status": "healthy"}

@app.get("/metadata", summary="Environment metadata")
def metadata():
    return {
        "name": "business-strategy-env",
        "description": "A real-world business strategy simulation where an AI agent makes CEO-level quarterly decisions to grow a company across three tasks of increasing difficulty.",
        "version": "1.0.0",
        "author": "Krish Lathiya",
        "tasks": list(GRADERS.keys()),
    }

@app.get("/schema", summary="Action, observation and state schemas")
def schema():
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": Observation.model_json_schema(),
    }

@app.post("/mcp", summary="MCP JSON-RPC endpoint")
def mcp(req: MCPRequest = None):
    return {
        "jsonrpc": "2.0",
        "id": req.id if req else 1,
        "result": {
            "name": "business-strategy-env",
            "version": "1.0.0",
            "capabilities": ["reset", "step", "state", "tasks", "grader", "baseline"]
        }
    }


# ─── Core OpenEnv Endpoints ───────────────────────────────────────────────────

@app.post("/reset", response_model=Observation, summary="Reset the environment")
def reset(req: ResetRequest = None):
    if req is None:
        req = ResetRequest()
    if req.task not in GRADERS:
        raise HTTPException(status_code=400, detail=f"Invalid task '{req.task}'. Valid: {list(GRADERS.keys())}")
    env = BusinessStrategyEnv(task=req.task, seed=req.seed)
    _envs[req.task] = env
    state = env.reset()
    state.setdefault("reward", 0.0)
    return state

@app.post("/step", response_model=Observation, summary="Take an action in the environment")
def step(req: StepRequest):
    """Submit an action and advance the environment by one quarter."""
    if req.action not in BusinessStrategyEnv.ACTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid action '{req.action}'. Valid: {BusinessStrategyEnv.ACTIONS}")
    env = get_env(req.task)
    result = env.step(action=req.action, amount=req.amount)
    result.setdefault("reward", 0.0)
    return result

@app.get("/state", response_model=Observation, summary="Get current environment state")
def state(task: str = "survive"):
    """Return the current state without advancing the environment."""
    env = get_env(task)
    s = env.state()
    s.setdefault("reward", 0.0)
    return s


# ─── Additional Endpoints ─────────────────────────────────────────────────────

@app.get("/tasks", summary="List all tasks and action schemas")
def tasks():
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
            },
            "amount": {
                "type": "float",
                "required": False,
                "default": 5000.0,
            },
        },
    }

@app.post("/grader", response_model=Reward, summary="Grade a completed episode")
def grader(req: GraderRequest):
    """Run the grader on the current episode and return a score [0.0–1.0]."""
    env = get_env(req.task)
    return run_grader(task=req.task, history=env.history, final_state=env.state())

@app.get("/baseline", summary="Run baseline agent and return scores for all tasks")
def baseline():
    """Run rule-based baseline agent on all 3 tasks. Returns reproducible scores."""
    from baseline import run_baseline_agent
    scores = {}
    for task in GRADERS.keys():
        scores[task] = run_baseline_agent(task=task, seed=42)
    return {"baseline_scores": scores, "agent": "rule_based_v1"}


if __name__ == "__main__":
      uvicorn.run("server:app", host="0.0.0.0", port=7860, reload=False)    
