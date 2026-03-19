"""
Experiment: Tool A/B — Bugs that REQUIRE execution to diagnose

Follow-up from tool_ab_code_debug: read_only won because all bugs were classic
patterns recognizable from source. This experiment uses bugs that are genuinely
hard to diagnose without running the code:

- Bugs that look correct but produce wrong output due to subtle runtime behavior
- Bugs that depend on execution order, state, or Python version specifics
- Bugs where multiple plausible explanations exist and only execution disambiguates

max_turns raised to 16 (from 8) to give bash_enabled enough budget.
"""
from openbench.types import AgentConfig, Experiment, DiffSpec

SETUP_FILES = {
    # Bug 1: Unicode normalization — two strings LOOK identical but aren't
    "bug1_unicode.py": '''\
"""Search function that fails on certain inputs."""

def search_users(users, query):
    """Find users whose name matches the query (case-insensitive)."""
    return [u for u in users if query.lower() in u["name"].lower()]

users = [
    {"name": "caf\\u00e9 owner", "id": 1},   # é as single codepoint U+00E9
    {"name": "cafe\\u0301 owner", "id": 2},   # e + combining acute U+0301
]

# Both display as "café owner" but...
result1 = search_users(users, "café")  # searches with U+00E9
result2 = search_users(users, "cafe\\u0301")  # searches with combining form

print(f"Search 'café' (NFC): found {len(result1)} users: {[u['id'] for u in result1]}")
print(f"Search 'café' (NFD): found {len(result2)} users: {[u['id'] for u in result2]}")
print(f"Are the two café strings equal? {'café' == 'cafe\\u0301'}")
''',

    # Bug 2: Dict ordering + mutation during iteration (subtle)
    "bug2_dict_order.py": '''\
"""Process config with defaults — subtle insertion order bug."""
import json

def merge_config(user_config, defaults):
    """Merge user config with defaults. User values take precedence."""
    result = {}
    # Add defaults first
    for k, v in defaults.items():
        result[k] = v
    # Override with user values
    for k, v in user_config.items():
        result[k] = v
    return result

defaults = {"host": "localhost", "port": 8080, "debug": False, "workers": 4}
user = {"port": 3000, "debug": True}

config = merge_config(user, defaults)
print(f"Config: {json.dumps(config, indent=2)}")

# Now the subtle bug: code elsewhere expects specific key order for positional unpacking
host, port, debug, workers = config.values()
print(f"Connecting to {host}:{port} (debug={debug}, workers={workers})")

# What if user provides keys in different order?
user2 = {"debug": True, "port": 3000, "workers": 8}
config2 = merge_config(user2, defaults)
host2, port2, debug2, workers2 = config2.values()
print(f"Config2: Connecting to {host2}:{port2} (debug={debug2}, workers={workers2})")
''',

    # Bug 3: Floating point accumulation that only shows with specific N
    "bug3_accumulation.py": '''\
"""Calculate statistics — accumulation error only visible at scale."""

def running_mean(values):
    """Calculate running mean incrementally."""
    mean = 0.0
    for i, v in enumerate(values):
        # Incremental mean formula: mean += (v - mean) / (i + 1)
        mean += (v - mean) / (i + 1)
    return mean

def simple_mean(values):
    return sum(values) / len(values)

# Test 1: Small input — looks fine
small = [1.0, 2.0, 3.0, 4.0, 5.0]
print(f"Small test: running={running_mean(small)}, simple={simple_mean(small)}")
print(f"Match: {running_mean(small) == simple_mean(small)}")

# Test 2: Larger input with varied magnitudes
import random
random.seed(42)
large = [random.uniform(-1e6, 1e6) for _ in range(10000)]
r = running_mean(large)
s = simple_mean(large)
print(f"Large test: running={r}, simple={s}")
print(f"Difference: {abs(r - s)}")
print(f"Match: {r == s}")

# Test 3: Pathological case — many small values then one large
pathological = [1e-10] * 10000 + [1e10]
r2 = running_mean(pathological)
s2 = simple_mean(pathological)
print(f"Pathological: running={r2}, simple={s2}")
print(f"Relative error: {abs(r2 - s2) / max(abs(s2), 1e-15)}")
''',

    # Bug 4: Regex that passes simple tests but has catastrophic backtracking
    "bug4_regex.py": '''\
"""Email validator — works on normal input, freezes on crafted input."""
import re
import time

# "Robust" email regex (actually has catastrophic backtracking)
EMAIL_PATTERN = re.compile(r'^([a-zA-Z0-9]+[._-])*[a-zA-Z0-9]+@[a-zA-Z0-9]+([.-][a-zA-Z0-9]+)*\\.[a-zA-Z]{2,}$')

def validate_email(email):
    """Return True if email is valid."""
    return bool(EMAIL_PATTERN.match(email))

# Normal inputs — works fine
tests_normal = [
    ("user@example.com", True),
    ("first.last@company.co.uk", True),
    ("bad@", False),
    ("@missing.com", False),
    ("user_name-test@domain.com", True),
]

print("Normal tests:")
for email, expected in tests_normal:
    start = time.time()
    result = validate_email(email)
    elapsed = time.time() - start
    status = "PASS" if result == expected else "FAIL"
    print(f"  {status}: {email!r} -> {result} ({elapsed:.4f}s)")

# Adversarial input — triggers catastrophic backtracking
print("\\nAdversarial test (may be slow):")
adversarial = "a" * 25 + "@"  # No valid TLD -> forces full backtrack
start = time.time()
result = validate_email(adversarial)
elapsed = time.time() - start
print(f"  {adversarial!r} -> {result} ({elapsed:.4f}s)")

# Even worse
adversarial2 = "a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a@"
start = time.time()
result2 = validate_email(adversarial2)
elapsed2 = time.time() - start
print(f"  {adversarial2!r} -> {result2} ({elapsed2:.4f}s)")
''',

    # Bug 5: Subtle asyncio / threading issue — result depends on execution timing
    "bug5_race.py": '''\
"""Concurrent counter — race condition only visible when actually run."""
import threading
import time

class Counter:
    def __init__(self):
        self.value = 0

    def increment(self):
        current = self.value
        # Simulate some work (makes race condition more likely)
        time.sleep(0.0001)
        self.value = current + 1

def run_increments(counter, n):
    for _ in range(n):
        counter.increment()

# Sequential — always correct
counter_seq = Counter()
run_increments(counter_seq, 100)
print(f"Sequential (100 increments): {counter_seq.value}")

# Concurrent — race condition
counter_par = Counter()
threads = [threading.Thread(target=run_increments, args=(counter_par, 50)) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"Concurrent (2x50 increments): {counter_par.value}")
print(f"Expected: 100, Lost updates: {100 - counter_par.value}")
''',
}

experiment = Experiment(
    name="tool_ab_execution_required",
    description=(
        "Bugs that REQUIRE execution to diagnose: unicode normalization, dict order, "
        "float accumulation, regex backtracking, race conditions. "
        "Bash+Read vs Read-only with max_turns=16."
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
            "and identify the bug in each one. Explain what the bug is, what output "
            "the code actually produces, and what the fix would be."
        ),
        allowed_tools=["Read", "Glob"],
        max_turns=16,
    ),
    agent_b=AgentConfig(
        name="bash_enabled",
        model="claude-haiku-4-5",
        system_prompt=(
            "You are a code debugger. Read and run the Python files in the current "
            "directory to identify the bug in each one. Execute the code to observe "
            "actual behavior, then explain the bug and the fix."
        ),
        allowed_tools=["Read", "Glob", "Bash"],
        max_turns=16,
    ),
    tasks=[
        "Analyze bug1_unicode.py. What happens when you search for 'café' and why do the two searches give different results?",
        "Analyze bug2_dict_order.py. Run it and explain what goes wrong with config2's positional unpacking.",
        "Analyze bug3_accumulation.py. Does the running mean match the simple mean? When does it diverge and by how much?",
        "Analyze bug4_regex.py. Run it and explain why some inputs are extremely slow. What is the root cause?",
        "Analyze bug5_race.py. Run it and explain why the concurrent counter gives wrong results. What is the exact value?",
    ],
    setup_files=SETUP_FILES,
    num_samples=1,
    tags=["tool-ab", "execution-required", "runtime-bugs"],
)
