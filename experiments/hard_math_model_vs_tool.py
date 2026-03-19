"""
Experiment: Model Capability vs Tool Access on Hard Math

Previous experiment (novel_math_with_answers) found haiku fails 4/10 tasks.
This 3-way tournament tests two remediation strategies:

  A. haiku (baseline) — no tools, pure reasoning
  B. haiku + Bash — can write and run Python to verify calculations
  C. sonnet (no tools) — stronger model, pure reasoning

Hypothesis: Sonnet will outperform both haiku variants. Haiku+Bash should
beat haiku-only because it can verify calculations programmatically.

Uses the SAME 4 tasks haiku failed + 2 it passed (as control).
All tasks have objective expected answers.
"""
from openbench.types import AgentConfig, TournamentConfig, TaskItem

tournament = TournamentConfig(
    name="hard_math_model_vs_tool",
    description=(
        "3-way: haiku vs haiku+Bash vs sonnet on hard math. "
        "Tests whether tool access or model capability better compensates for reasoning failures."
    ),
    configs=[
        AgentConfig(
            name="haiku_baseline",
            model="claude-haiku-4-5",
            system_prompt=None,
            allowed_tools=[],
            max_turns=2,
        ),
        AgentConfig(
            name="haiku_with_bash",
            model="claude-haiku-4-5",
            system_prompt=(
                "You have access to Bash. For math problems, write a short Python "
                "script to compute the answer, run it, and report the result. "
                "Always verify your reasoning with code."
            ),
            allowed_tools=["Bash"],
            max_turns=6,
        ),
        AgentConfig(
            name="sonnet_baseline",
            model="claude-sonnet-4-6",
            system_prompt=None,
            allowed_tools=[],
            max_turns=2,
        ),
    ],
    tasks=[
        # ── Tasks haiku FAILED (from novel_math_with_answers) ────────────

        # T1: Water tank — haiku got wrong (both agents)
        TaskItem(
            prompt=(
                "A tank fills at 3.7 liters per minute. After 23 minutes of filling, "
                "a drain opens that removes water at 1.2 liters per minute (while filling "
                "continues). How many total liters are in the tank after 40 minutes from "
                "the start? Give a number to one decimal place."
            ),
            expected="105.8",
            check_fn='"105.8" in output',
            difficulty="medium",
        ),

        # T2: Compound interest — haiku got wrong
        TaskItem(
            prompt=(
                "You invest $2,500 at 6% annual interest compounded quarterly. "
                "After exactly 3 years, what is the total amount? "
                "Round to the nearest cent."
            ),
            expected="$2,986.50",
            check_fn='"2986.5" in output or "2,986.5" in output',
            difficulty="medium",
        ),

        # T3: Bouncing ball — haiku got wrong
        TaskItem(
            prompt=(
                "A bouncing ball is dropped from 243 cm. Each bounce reaches exactly "
                "2/3 of the previous height. What is the TOTAL distance the ball "
                "travels (both up and down) from the moment it's dropped until it "
                "reaches the ground after the 5th bounce? Give exact answer in cm."
            ),
            expected="1033",
            check_fn='"1033" in output',
            difficulty="hard",
        ),

        # T4: Modular arithmetic — haiku got wrong
        TaskItem(
            prompt=(
                "What is the remainder when 7^100 is divided by 13? "
                "Give a single number."
            ),
            expected="9",
            check_fn='output.strip().endswith("9") or "= 9" in output or "is 9" in output or "remainder is 9" in output.lower()',
            difficulty="hard",
        ),

        # ── Control tasks haiku PASSED ───────────────────────────────────

        # T5: System of equations (haiku passed)
        TaskItem(
            prompt=(
                "Alice, Bob, and Charlie split a bill. Alice pays 3 times what "
                "Bob pays. Charlie pays $14 more than Bob. The total bill is $94. "
                "How much does each person pay? Give all three amounts."
            ),
            expected="Alice: $48, Bob: $16, Charlie: $30",
            check_fn='"48" in output and "16" in output and "30" in output',
            difficulty="medium",
        ),

        # T6: Combinatorics (haiku passed)
        TaskItem(
            prompt=(
                "How many 4-digit numbers (1000-9999) have all digits strictly "
                "increasing (each digit is larger than the one before it)? "
                "Give a single number."
            ),
            expected="126",
            check_fn='"126" in output',
            difficulty="hard",
        ),
    ],
    num_samples=1,
    tags=["model-vs-tool", "hard-math", "objective-correctness", "tournament"],
)
