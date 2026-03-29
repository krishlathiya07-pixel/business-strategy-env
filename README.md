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

An **OpenEnv-compliant** environment where an AI agent plays the role of a CEO, making quarterly strategic decisions to grow a company.

Built for the **OpenEnv Hackathon — Round 1**.

---

## 🌍 Environment Description

The agent controls a company with the following state: revenue, costs, profit, market share, employees, customer satisfaction, marketing budget, R&D investment, and product quality.

Each step = one business quarter. The agent chooses a strategic action, the market responds, and a reward is computed based on the task objective.

---

## 🎯 Tasks

| Task | Difficulty | Goal | Max Quarters |
|------|-----------|------|-------------|
| `survive` | Easy | Keep profit > 0 every quarter | 4 |
| `grow_market_share` | Medium | Reach 20% market share | 8 |
| `scale_profitably` | Hard | 2x revenue + satisfaction ≥ 0.8 | 12 |

---

## 🔧 Action Space

| Action | Effect |
|--------|--------|
| `increase_marketing` | ↑ Market share, ↑ Satisfaction, ↑ Costs |
| `decrease_marketing` | ↓ Costs, ↓ Market share |
| `hire_employees` | ↑ Revenue capacity, ↑ Costs |
| `layoff_employees` | ↓ Costs, ↓ Satisfaction |
| `cut_costs` | ↓ Costs, ↓ Product quality |
| `invest_in_rd` | ↑ Product quality, ↑ Costs |
| `launch_product` | ↑ Revenue, ↑ Market share |
| `expand_market` | ↑ Market share, ↑ Revenue |
| `raise_prices` | ↑ Revenue, ↓ Satisfaction |
| `lower_prices` | ↓ Revenue, ↑ Satisfaction, ↑ Market share |

Each action also takes an `amount` (float, default: 5000.0) representing the dollar investment.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/reset` | Reset environment |
| `POST` | `/step` | Take an action |
| `GET` | `/state` | Get current state |
| `GET` | `/tasks` | List tasks + action schema |
| `POST` | `/grader` | Grade completed episode |
| `GET` | `/baseline` | Run baseline agent on all tasks |

---

## 🚀 Setup & Run

### Local

```bash
pip install -r requirements.txt
python server.py
```

Visit: http://localhost:7860/docs (Swagger UI)

### Docker

```bash
docker build -t business-strategy-env .
docker run -p 7860:7860 business-strategy-env
```

### Baseline

```bash
python baseline.py
```

---

## 📋 Example Usage

```python
import requests

BASE = "http://localhost:7860"

# Reset
state = requests.post(f"{BASE}/reset", json={"task": "survive", "seed": 42}).json()

# Play
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
business_strategy_env/
├── environment.py     # Core simulation logic
├── graders.py         # Task-specific graders (score 0.0–1.0)
├── server.py          # FastAPI server (all OpenEnv endpoints)
├── baseline.py        # Rule-based baseline agent
├── openenv.yaml       # OpenEnv spec
├── Dockerfile         # Container config
├── requirements.txt
└── README.md
```

---

## 🏆 Reward Design

- **survive**: `profitable_quarters / total_quarters`
- **grow_market_share**: `min(market_share / 0.20, 1.0)` + early bonus
- **scale_profitably**: `0.6 × revenue_score + 0.4 × satisfaction_score`

All rewards are partial progress signals in `[0.0, 1.0]` — no sparse end rewards.