"""
Experiment: Tool A/B — Does Bash execution improve code debugging?

Hypothesis: An agent with Bash (can execute code to verify) will outperform
a Read-only agent on code debugging tasks where the bug is subtle and
running the code reveals the issue.

This tests a fundamentally different axis than system prompt experiments:
tool access changes what's computable, not just reasoning quality.

Setup: Each task provides a buggy Python file via setup_files. Agent must
identify and explain the bug.
"""
from openbench.types import AgentConfig, Experiment, DiffSpec

# Buggy Python files provided to each trial's working directory
SETUP_FILES = {
    "bug1_float.py": '''\
"""Calculate the total price after applying discounts."""

def apply_discounts(prices, discounts):
    """Apply percentage discounts to prices and return total."""
    total = 0
    for price, discount in zip(prices, discounts):
        total += price * (1 - discount / 100)
    return round(total, 2)

# Expected: 10.00 + 8.50 + 7.20 = 25.70
# Actual: returns 25.70 ... but what about this case?
prices = [0.1 + 0.2, 0.3, 0.1]  # floating point
discounts = [0, 0, 0]
result = apply_discounts(prices, discounts)
print(f"Expected 0.60, got {result}")
# Bug: 0.1+0.2 != 0.3, so sum is 0.6000000000000001, round(_, 2) = 0.6 -- but
# the function LOOKS correct. The real subtle issue is that the function doesn't
# handle floating point input consistently.
''',

    "bug2_scope.py": '''\
"""Event handler registry with closures."""

def make_handlers(events):
    """Create a handler function for each event name."""
    handlers = []
    for event in events:
        def handler(data):
            return f"Handling {event}: {data}"
        handlers.append(handler)
    return handlers

h = make_handlers(["click", "hover", "scroll"])
# Expected: "Handling click: test", "Handling hover: test", "Handling scroll: test"
# Actual output:
for i, handler in enumerate(h):
    print(f"Handler {i}: {handler('test')}")
''',

    "bug3_mutation.py": '''\
"""Shopping cart with default argument mutation bug."""

def add_item(item, cart=[]):
    """Add an item to the cart and return it."""
    cart.append(item)
    return cart

# User A
cart_a = add_item("apple")
print(f"Cart A: {cart_a}")  # ['apple']

# User B (fresh cart expected)
cart_b = add_item("banana")
print(f"Cart B: {cart_b}")  # Expected: ['banana'], Actual: ???
''',

    "bug4_generator.py": '''\
"""Data pipeline with generator exhaustion bug."""

def read_data():
    """Simulate reading records."""
    yield {"name": "Alice", "score": 85}
    yield {"name": "Bob", "score": 92}
    yield {"name": "Charlie", "score": 78}

data = read_data()

# Step 1: Count records
count = sum(1 for _ in data)
print(f"Total records: {count}")

# Step 2: Calculate average
total = sum(record["score"] for record in data)
avg = total / count if count > 0 else 0
print(f"Average score: {avg}")
''',

    "bug5_comparison.py": '''\
"""Priority queue with custom comparison."""

class Task:
    def __init__(self, name, priority):
        self.name = name
        self.priority = priority

    def __lt__(self, other):
        return self.priority < other.priority

import heapq

tasks = [Task("email", 3), Task("urgent", 1), Task("meeting", 2)]
heapq.heapify(tasks)

# Pop all tasks -- should come out in priority order
results = []
while tasks:
    t = heapq.heappop(tasks)
    results.append(f"{t.name}(p={t.priority})")
print(" -> ".join(results))

# Now try with equal priorities
tasks2 = [Task("a", 1), Task("b", 1), Task("c", 1)]
heapq.heapify(tasks2)
while tasks2:
    t = heapq.heappop(tasks2)
    results.append(t.name)
# Bug: what happens when priorities are equal and Task has no __eq__?
''',
}

experiment = Experiment(
    name="tool_ab_code_debug",
    description=(
        "Does Bash execution access improve code debugging accuracy? "
        "Agent with Bash+Read vs Read-only on subtle Python bugs."
    ),
    diff=DiffSpec(
        field="allowed_tools",
        description="Bash+Read (can execute) vs Read-only (must reason from source)",
    ),
    agent_a=AgentConfig(
        name="read_only",
        model="claude-haiku-4-5",
        system_prompt=(
            "You are a code debugger. Read the Python files in the current directory "
            "and identify the bug in each one. Explain clearly what the bug is, why it "
            "happens, and what the fix would be."
        ),
        allowed_tools=["Read", "Glob"],
        max_turns=8,
    ),
    agent_b=AgentConfig(
        name="bash_enabled",
        model="claude-haiku-4-5",
        system_prompt=(
            "You are a code debugger. Read and run the Python files in the current directory "
            "to identify the bug in each one. Execute the code to observe the actual behavior. "
            "Explain clearly what the bug is, why it happens, and what the fix would be."
        ),
        allowed_tools=["Read", "Glob", "Bash"],
        max_turns=8,
    ),
    tasks=[
        "Find and explain the bug in bug1_float.py. What is the subtle issue with floating point?",
        "Find and explain the bug in bug2_scope.py. What do the handlers actually print and why?",
        "Find and explain the bug in bug3_mutation.py. What does Cart B contain and why?",
        "Find and explain the bug in bug4_generator.py. What happens in Step 2 and why?",
        "Find and explain the bug in bug5_comparison.py. What error occurs with equal priorities?",
    ],
    setup_files=SETUP_FILES,
    num_samples=1,
    tags=["tool-ab", "code-debug", "bash-vs-read"],
)
