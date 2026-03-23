"""
Task Decomposition v3: Hint Accuracy Spectrum

v1-v2 showed accurate hints save 38% cost. But research shows:
- CodeCrash (NeurIPS 2025): misleading comments degrade reasoning by 23%
- Anchoring bias studies: LLMs retain ~37% of anchor difference

Key question: Does 1 WRONG hint among 3 correct ones help or hurt overall?
- If guided_partial > discovery: correct hints outweigh wrong one (net positive)
- If guided_partial < discovery: anchoring to wrong hint is toxic (net negative)
- If guided_partial ≈ discovery: effects cancel out

Design: A/B test guided_correct vs guided_partial on same 8-file codebase.
Then compare both to discovery baseline from v2.

max_turns=20, num_samples=5.
"""
import importlib.util, os
_spec = importlib.util.spec_from_file_location(
    "wm_scale", os.path.join(os.path.dirname(__file__), "working_memory_scale.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

from openbench.types import AgentConfig, Experiment, DiffSpec, TaskItem

# All 4 hints correct (same as v2)
GUIDED_CORRECT_PROMPT = """\
You are a senior developer debugging a Python web application.

The team has identified these 4 bugs. Fix each one:

1. **app/config.py line 3** — MAX_CACHE_SIZE is 5 but should be 50.
   The cache needs to hold 20+ items without eviction.

2. **app/validators.py line 9** — Email regex doesn't allow '+' in local part.
   Add '+' to the character class: [a-zA-Z0-9._+-]

3. **app/services.py line 21** — UserService.update_email() doesn't invalidate
   the cache after update. Add: self.cache.invalidate(f"user:{username}")

4. **app/auth.py lines 13,20** — register() and authenticate() both call
   password.lower() before hashing, making passwords case-insensitive.
   Remove both .lower() calls.

After fixing all 4, run the tests to verify.
Print the final test output.
"""

# 3 correct + 1 WRONG hint
# Wrong hint: says services.py uses wrong attribute name (it doesn't —
# the real bug is missing cache invalidation). This is "directionally correct"
# (right file, right function) but specifically wrong (wrong diagnosis).
GUIDED_PARTIAL_PROMPT = """\
You are a senior developer debugging a Python web application.

The team has identified these 4 bugs. Fix each one:

1. **app/config.py line 3** — MAX_CACHE_SIZE is 5 but should be 50.
   The cache needs to hold 20+ items without eviction.

2. **app/validators.py line 9** — Email regex doesn't allow '+' in local part.
   Add '+' to the character class: [a-zA-Z0-9._+-]

3. **app/services.py line 21** — UserService.update_email() assigns new_email
   to user.name instead of user.email. Change the attribute name.

4. **app/auth.py lines 13,20** — register() and authenticate() both call
   password.lower() before hashing, making passwords case-insensitive.
   Remove both .lower() calls.

After fixing all 4, run the tests to verify.
Print the final test output.
"""

TASK_PROMPT = (
    "Fix all bugs in this web application. The code is in app/. "
    "Run: python test_app.py\n"
    "There are multiple bugs across different files. "
    "Print the final test output."
)

experiment = Experiment(
    name="task_decomposition_v3",
    description=(
        "Hint accuracy test: 4/4 correct hints vs 3 correct + 1 wrong hint. "
        "The wrong hint points to the right file/function but gives wrong diagnosis. "
        "Tests whether 1 bad hint poisons the benefit of 3 good ones."
    ),
    diff=DiffSpec(
        field="system_prompt",
        description="All-correct hints vs partially-wrong hints (1 of 4 is wrong)",
    ),
    agent_a=AgentConfig(
        name="guided_correct",
        model="claude-haiku-4-5",
        system_prompt=GUIDED_CORRECT_PROMPT,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=20,
    ),
    agent_b=AgentConfig(
        name="guided_partial",
        model="claude-haiku-4-5",
        system_prompt=GUIDED_PARTIAL_PROMPT,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=20,
    ),
    tasks=[
        TaskItem(
            prompt=TASK_PROMPT,
            expected="PASSED",
            check_fn='"PASSED" in output or "pass" in output.lower()',
            difficulty="hard",
            tags=["multi-file", "4-bugs", "wrong-hint"],
        ),
    ],
    setup_files=_mod.SETUP_FILES,
    num_samples=5,
    tags=["task-decomposition", "hint-accuracy", "anchoring-bias"],
)
