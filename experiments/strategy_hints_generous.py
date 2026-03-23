"""
Strategy: Do Hints Help on Genuinely Hard Bugs? (Generous Turns)

Previous "hint paradox" was confounded by max_turns=8 — failures were
from running out of time, not from bad strategy.

This experiment removes the turn constraint entirely (max_turns=20).
Uses the same hard tasks (3 bugs per task, including tricky ones).
If guided still loses: hints are genuinely harmful on hard bugs.
If guided wins: the previous finding was just a turn budget artifact.

4 tasks × 5 samples, max_turns=20. Both agents should have 0 timeouts.
"""
from openbench.types import AgentConfig, Experiment, DiffSpec, TaskItem

# Import hard tasks
import importlib.util, os
_spec = importlib.util.spec_from_file_location(
    "dh", os.path.join(os.path.dirname(__file__), "task_decomposition_hard.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

DISCOVERY_PROMPT = """\
You are debugging Python code. Fix all bugs and make all tests pass.
Print the final test output.
"""

GUIDED_PROMPT = """\
You are debugging Python code. The team has identified these bugs:

**tasks/t1/bank.py:**
1. withdraw() doesn't check if balance is sufficient — add a balance check
2. transfer() deducts fee from recipient instead of charging sender — sender should pay amount + fee, recipient gets full amount
3. apply_interest() uses self.balance but should use self.opening_balance

**tasks/t2/limiter.py:**
1. is_allowed() always returns True — add check: if len >= max_requests return False
2. _cleanup() comparison is inverted — should keep requests where now - t < window
3. get_remaining() should call _cleanup first to purge expired requests

**tasks/t3/mdtable.py:**
1. Header cells aren't stripped of whitespace after split
2. Separator line detection assumes fixed position — detect --- dynamically
3. Type conversion edge cases — check carefully

**tasks/t4/emitter.py:**
1. emit() doesn't pass *args/**kwargs to handler function calls
2. once() registers with once=False instead of once=True
3. off(event, handler) clears ALL handlers instead of only the specified one

Fix the bugs for whichever task you're given. Print the final test output.
"""

experiment = Experiment(
    name="strategy_hints_generous",
    description=(
        "Do hints help on hard bugs when turns are NOT a constraint? "
        "Same hard tasks as D-Hard but max_turns=20 (generous). "
        "Tests whether hint paradox is a real strategy effect or turn artifact."
    ),
    diff=DiffSpec(
        field="system_prompt",
        description="Discovery (no hints) vs guided (bug list) with generous turn budget",
    ),
    agent_a=AgentConfig(
        name="discovery",
        model="claude-haiku-4-5",
        system_prompt=DISCOVERY_PROMPT,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=20,
    ),
    agent_b=AgentConfig(
        name="guided",
        model="claude-haiku-4-5",
        system_prompt=GUIDED_PROMPT,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=20,
    ),
    tasks=_mod.TASKS,
    setup_files=_mod.SETUP_FILES,
    num_samples=5,
    tags=["strategy", "hints", "generous-turns", "hard-bugs"],
)
