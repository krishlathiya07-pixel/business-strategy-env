from environment import BusinessStrategyEnv
from baseline import rule_based_agent
import random

random.seed(42)
env = BusinessStrategyEnv(task='survive', seed=42)
state = env.reset()
print('Initial state:', {k: v for k, v in state.items() if k not in ['message', 'done']})

for i in range(4):
    action = rule_based_agent(state, 'survive')
    print(f'Q{i+1} Action: {action}')
    state = env.step(**action)
    print(f'Q{i+1} Result: Profit={state["profit"]:.0f}, Revenue={state["revenue"]:.0f}, Costs={state["costs"]:.0f}')
    if state['done']:
        break

print('Final profit > 0:', state['profit'] > 0)