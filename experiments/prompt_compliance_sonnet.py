"""
Prompt Compliance Threshold: Sonnet vs Haiku

Core finding from compute_allocation: moderate prompts have ZERO effect on Haiku.
Only EXTREME FORBIDDEN prompts change behavior.

Question: Does Sonnet have a LOWER compliance threshold?
If Sonnet responds to moderate prompts, the threshold is model-dependent.

Design: test-first vs read-first with MODERATE prompts on both models.
Measure: first tool called (Bash = test-first compliant, Read/Glob = read-first compliant).
Use the same SC tasks for consistent comparison.

Tournament: 4 agents × 4 tasks × 3 samples.
"""
import importlib.util, os
_spec = importlib.util.spec_from_file_location(
    "sc_v1", os.path.join(os.path.dirname(__file__), "self_correction_strategy.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

from openbench.types import AgentConfig, TournamentConfig, TaskItem

# MODERATE prompts — suggestions, not prohibitions
TEST_FIRST_MODERATE = """\
You are debugging Python code. Follow this workflow:

Before reading any code, run the test to see what fails.
Start with running the test file — the error output tells you exactly what's wrong.
Then read the relevant source code to understand the error.
Fix the bug and run the test again.

Test-driven debugging is the most efficient approach — let the errors guide you.
Print the final test output.
"""

READ_FIRST_MODERATE = """\
You are debugging Python code. Follow this workflow:

Before running any test, read all source files carefully.
Start with reading every .py file to understand the full codebase.
Then read the test file to understand expected behavior.
Fix the bugs based on your understanding, then run the test to verify.

Understanding-first debugging is the most efficient approach — comprehend before acting.
Print the final test output.
"""

TASKS = [
    TaskItem(
        prompt="Fix all bugs in tasks/t1/inventory.py. Run: cd tasks/t1 && python test_inventory.py\nPrint the test output.",
        expected="PASSED",
        check_fn='"PASSED" in output or "pass" in output.lower()',
        difficulty="medium",
    ),
    TaskItem(
        prompt="Fix all bugs in tasks/t2/textstats.py. Run: cd tasks/t2 && python test_textstats.py\nPrint the test output.",
        expected="PASSED",
        check_fn='"PASSED" in output or "pass" in output.lower()',
        difficulty="medium",
    ),
    TaskItem(
        prompt="Fix all bugs in tasks/t3/pqueue.py. Run: cd tasks/t3 && python test_pqueue.py\nPrint the test output.",
        expected="PASSED",
        check_fn='"PASSED" in output or "pass" in output.lower()',
        difficulty="medium",
    ),
    TaskItem(
        prompt="Fix all bugs in tasks/t4/grades.py. Run: cd tasks/t4 && python test_grades.py\nPrint the test output.",
        expected="PASSED",
        check_fn='"PASSED" in output or "pass" in output.lower()',
        difficulty="medium",
    ),
]

tournament = TournamentConfig(
    name="prompt_compliance_sonnet",
    description=(
        "Prompt compliance threshold: do Sonnet and Haiku respond differently "
        "to MODERATE behavioral prompts? Measure first-tool divergence."
    ),
    configs=[
        AgentConfig(
            name="haiku_test_first",
            model="claude-haiku-4-5",
            system_prompt=TEST_FIRST_MODERATE,
            allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
            max_turns=10,
        ),
        AgentConfig(
            name="haiku_read_first",
            model="claude-haiku-4-5",
            system_prompt=READ_FIRST_MODERATE,
            allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
            max_turns=10,
        ),
        AgentConfig(
            name="sonnet_test_first",
            model="claude-sonnet-4-6",
            system_prompt=TEST_FIRST_MODERATE,
            allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
            max_turns=10,
        ),
        AgentConfig(
            name="sonnet_read_first",
            model="claude-sonnet-4-6",
            system_prompt=READ_FIRST_MODERATE,
            allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
            max_turns=10,
        ),
    ],
    tasks=TASKS,
    setup_files=_mod.SETUP_FILES,
    setup_script="cd tasks/t1 && git init -q && git add -A && git commit -q -m init && cd ../t2 && git init -q && git add -A && git commit -q -m init && cd ../t3 && git init -q && git add -A && git commit -q -m init && cd ../t4 && git init -q && git add -A && git commit -q -m init",
    num_samples=3,
    tags=["prompt-compliance", "moderate-prompts", "cross-model"],
)
