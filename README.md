---
title: Business Strategy Env
emoji: 💼
colorFrom: blue
colorTo: purple
sdk: docker
app_file: server.py
pinned: false
---

# 🏢 Business Strategy Simulation Environment

> An **OpenEnv-compliant** real-world environment where an AI agent acts as CEO, making quarterly strategic decisions to grow a company. Features stochastic market dynamics and multi-objective reward optimization.

Built for the **OpenEnv Hackathon — Round 1** · [Live API Docs](https://ihere04u-business-strategy-env.hf.space/docs)

---

## 🌍 Why This Environment?

Business strategy is a genuine real-world task — companies live and die by quarterly decisions on hiring, marketing, pricing, and R&D. This environment models those decisions with:

- **Stochastic market dynamics** — random noise simulates real market unpredictability
- **Interdependent state variables** — actions have cascading effects (e.g. cutting costs reduces quality, reducing satisfaction, reducing market share)
- **Multi-objective trade-offs** — agents must balance short-term profit vs long-term growth
- **Partial progress rewards** — dense reward signal every quarter, not just at episode end

---

## 🎯 Tasks

| Task | Difficulty | Goal | Max Quarters | Reward Formula |
|------|-----------|------|-------------|----------------|
| `survive` | Easy | Keep profit > 0 every quarter | 4 | `profitable_quarters / total_quarters` |
| `grow_market_share` | Medium | Reach 20% market share | 8 | `min(market_share / 0.20, 1.0)` + early bonus |
| `scale_profitably` | Hard | 2x revenue AND satisfaction ≥ 0.8 | 12 | `0.6 × revenue_score + 0.4 × satisfaction_score` |

---

## 🔧 Action Space

10 strategic actions, each with an optional `amount` parameter (default: $5,000):

| Action | Primary Effect |
|--------|----------------|
| `increase_marketing` | ↑ Market share, ↑ Satisfaction, ↑ Costs |
| `decrease_marketing` | ↓ Costs, ↓ Market share |
| `hire_employees` | ↑ Revenue capacity, ↑ Costs |
| `layoff_employees` | ↓ Costs, ↓ Satisfaction |
| `cut_costs` | ↓ Costs, ↓ Product quality |
| `invest_in_rd` | ↑ Product quality, ↑ Costs |
| `launch_product` | ↑ Revenue, ↑ Market share |
| `expand_market` | ↑ Market share, ↑ Revenue |
| `raise_prices` | ↑ Revenue, ↓ Satisfaction, ↓ Market share |
| `lower_prices` | ↓ Revenue, ↑ Satisfaction, ↑ Market share |

---

## 👁️ Observation Space

This environment returns both raw business metrics and higher-level strategy signals.

```json
{
  "revenue": 50000.0,
  "costs": 35000.0,
  "profit": 15000.0,
  "market_share": 0.10,
  "employees": 20,
  "customer_satisfaction": 0.70,
  "marketing_budget": 5000.0,
  "rd_investment": 2000.0,
  "product_quality": 0.65,
  "profit_margin": 0.30,
  "cost_efficiency": 0.30,
  "growth_signal": 0.40,
  "profit_trend": 0.0,
  "last_reward": 0.0,
  "risk_level": 0.70,
  "strategic_health": 0.37,
  "growth_momentum": 0.07,
  "decision_quality": "neutral",
  "quarter": 1,
  "max_quarters": 4,
  "done": false,
  "reward": 0.0,
  "message": "Q1: Profit=$15,000 | Market=10.0%"
}
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — returns `{"status": "healthy"}` |
| `GET` | `/metadata` | Environment metadata |
| `GET` | `/schema` | Typed action/observation/state schemas |
| `POST` | `/reset` | Reset environment for a task |
| `POST` | `/step` | Take an action, advance one quarter |
| `GET` | `/state` | Get current state |
| `GET` | `/tasks` | List all tasks + action schema |
| `POST` | `/grader` | Grade a completed episode |
| `GET` | `/baseline` | Run rule-based baseline on all 3 tasks |
| `POST` | `/mcp` | MCP JSON-RPC endpoint |

---

## 🏆 Reward Design

All rewards are **partial progress signals** — no sparse binary end-of-episode rewards:

- **survive**: `profitable_quarters / total_quarters` — scores every quarter
- **grow_market_share**: `min(final_share / 0.20, 1.0)` + early completion bonus
- **scale_profitably**: `0.6 × revenue_score + 0.4 × satisfaction_score` — weighted multi-objective

Undesirable behaviors are penalized:
- Bankruptcy (profit < -$50,000) → early termination
- Over-hiring with no revenue → costs spiral punishes poor decisions
- Cutting costs repeatedly → product quality degrades, reducing future revenue

---

## 🧠 Advanced Learning Dynamics

This environment is intentionally designed to challenge decision-making agents through:

### 1. Multi-Objective Optimization
Agents must balance:
- Profitability
- Market share growth
- Customer satisfaction
- Cost efficiency

### 2. Delayed Rewards
Investments in R&D improve future revenue rather than immediate outcomes.

### 3. Strategic Trade-offs
Each action has both positive and negative consequences:
- Expanding markets increases growth but reduces satisfaction
- Cost cutting improves margins but degrades product quality

### 4. Stochastic Environment
- Economic cycles affect revenue unpredictably
- Competitor pressure reduces market share dynamically

### 5. Non-Linear Reward Shaping
Rewards include:
- Trend-based bonuses
- Strategic diversity incentives
- Penalties for repetitive or short-sighted decisions

### 6. Failure Cascades
Poor decisions (e.g., low satisfaction) trigger compounding negative effects.

### 7. Decision Feedback
The environment exposes decision quality signals such as `decision_quality` and a `final_summary` at episode end.

This creates a realistic environment requiring **long-term planning, adaptation, and strategic reasoning**.

---

## 📊 Baseline Scores

Scores from the included rule-based baseline agent (`baseline.py`):

| Task | Score | Notes |
|------|-------|-------|
| `survive` | 0.999 | Profitable all 4 quarters |
| `grow_market_share` | 0.685 | Explores aggressively, but market share remains a challenge |
| `scale_profitably` | 0.999 | Revenue target reached with tight satisfaction |

> Note: Baseline performance is intentionally stochastic and may vary across seeds.

---

## 🤖 Agent Strategy

The included **rule-based inference agent** (`inference.py`) uses adaptive task-specific logic:

- **Survive**: Maintains profitability by cutting costs when needed, then rotates between growth actions
- **Grow Market Share**: Progressively increases market reach—expands when low, invests in marketing, then launches products
- **Scale Profitably**: Balances quality, satisfaction, and growth—invests heavily in R&D, then scales with pricing and expansion

The agent includes **anti-repetition safety** to avoid over-using the same action, ensuring diverse strategy execution.
The agent is fully rule-based and does not depend on external LLM calls, ensuring stable and deterministic performance.
---

## 🚀 Setup & Run

### Local

```bash
pip install -r requirements.txt
python baseline.py      # verify logic
python server.py        # start API server
```

Visit: http://localhost:7860/docs

### Local app entrypoint

```bash
python main.py
```

### Docker

```bash
docker build -t business-strategy-env .
docker run -p 7860:7860 business-strategy-env
```

### Inference (Rule-Based Agent)

```bash
python inference.py
```

---

## 📋 Quick Example

```python
import requests

BASE = "https://ihere04u-business-strategy-env.hf.space"

# Reset
state = requests.post(f"{BASE}/reset", json={"task": "survive", "seed": 42}).json()

# Play 4 quarters
for _ in range(4):
    state = requests.post(f"{BASE}/step", json={
        "task": "survive",
        "action": "increase_marketing",
        "amount": 5000
    }).json()
    print(state["message"], "| Reward:", state["reward"])

# Grade
score = requests.post(f"{BASE}/grader", json={"task": "survive"}).json()
print("Final score:", score["score"])
```

---

## 📁 Project Structure

```
business-strategy-env/
├── environment.py     # Core simulation logic + stochastic market dynamics
├── graders.py         # Task-specific graders returning scores in [0.0, 1.0]
├── server.py          # FastAPI server — all OpenEnv + additional endpoints
├── baseline.py        # Rule-based baseline agent
├── inference.py       # LLM agent using OpenAI-compatible client
├── openenv.yaml       # OpenEnv spec
├── Dockerfile         # Container — deploys on HF Spaces (port 7860)
├── requirements.txt
└── README.md
```