"""
Experiment: Does minimal_trap generalize across domains?

Follow-up from reasoning_decompose_tournament: minimal_trap matched full_scaffold
on math/cognitive traps. But does the "name the wrong intuition first" pattern
transfer to non-math domains?

Domains tested:
  - Logical syllogisms (formal logic fallacies)
  - Causal inference (correlation ≠ causation traps)
  - Code debugging (reading buggy Python, identifying the real bug)
  - Probability/statistics (base rate neglect, survivorship bias)

Hypothesis: minimal_trap will generalize — naming the wrong intuition is a
domain-general metacognitive strategy, not math-specific.
"""
from openbench.types import AgentConfig, Experiment, DiffSpec

experiment = Experiment(
    name="minimal_trap_cross_domain",
    description=(
        "Does the 'name the wrong intuition first' prompt generalize beyond math? "
        "Testing on logic, causal inference, code debugging, and statistics."
    ),
    diff=DiffSpec(
        field="system_prompt",
        description="minimal_trap (name wrong intuition) vs baseline (no prompt)",
    ),
    agent_a=AgentConfig(
        name="baseline",
        model="claude-haiku-4-5",
        system_prompt=None,
        allowed_tools=[],
        max_turns=2,
    ),
    agent_b=AgentConfig(
        name="minimal_trap",
        model="claude-haiku-4-5",
        system_prompt=(
            "Before answering, write one sentence: state the most common wrong "
            "intuitive answer and explain in one phrase why it fails. "
            "Then answer the question."
        ),
        allowed_tools=[],
        max_turns=2,
    ),
    tasks=[
        # ── LOGICAL SYLLOGISMS ────────────────────────────────────────────
        # Affirming the consequent (common fallacy)
        "All dogs are mammals. All mammals are animals. Some animals are pets. "
        "Does it follow that all dogs are pets? Answer Yes or No and explain your reasoning.",

        # Denying the antecedent
        "If it rains, the ground gets wet. It didn't rain today. "
        "Can we conclude the ground is not wet? Answer Yes or No and explain.",

        # Illicit conversion
        "All roses are flowers. Does it follow that all flowers are roses? "
        "What about: some flowers are roses? Evaluate both statements.",

        # ── CAUSAL INFERENCE ──────────────────────────────────────────────
        # Survivorship bias
        "During WWII, the military studied bullet holes on returning bombers "
        "and found most damage on the fuselage and wings, with almost none on "
        "the engines. A naive analyst recommends reinforcing the fuselage and wings. "
        "What is wrong with this recommendation? What should they reinforce instead?",

        # Confounding variable
        "A study finds that children who eat breakfast every day score 15% higher "
        "on standardized tests than children who skip breakfast. A newspaper headline "
        "reads: 'Eating breakfast boosts test scores by 15%.' "
        "What is the key flaw in this causal claim? Name at least two confounding variables.",

        # Regression to the mean
        "A sports team performs extremely well one season (top 5%). The next season "
        "they hire a new coach, and their performance drops to average. "
        "The media blames the new coach. What statistical phenomenon better explains this?",

        # ── CODE DEBUGGING ────────────────────────────────────────────────
        # Off-by-one that looks correct
        "```python\ndef find_pairs_summing_to(nums, target):\n"
        "    seen = set()\n"
        "    pairs = []\n"
        "    for i in range(len(nums)):\n"
        "        complement = target - nums[i]\n"
        "        if complement in seen:\n"
        "            pairs.append((complement, nums[i]))\n"
        "        seen.add(nums[i])\n"
        "    return pairs\n\n"
        "# Bug report: find_pairs_summing_to([3, 3, 3], 6) returns [(3,3),(3,3)] but should return [(3,3)] once.\n```\n"
        "What is the real bug? Is the reporter's expectation correct? Explain.",

        # Boolean logic bug
        "```python\ndef is_valid_triangle(a, b, c):\n"
        "    return a + b > c or a + c > b or b + c > a\n```\n"
        "This function is supposed to check if three sides form a valid triangle. "
        "It returns True for (1, 2, 10). Is the function correct? What's the bug?",

        # ── BASE RATE / STATISTICS ────────────────────────────────────────
        # Base rate neglect (classic)
        "A disease affects 1 in 10,000 people. A test for this disease has a 99% "
        "true positive rate and a 1% false positive rate. You test positive. "
        "What is the approximate probability you actually have the disease? "
        "Show your calculation.",

        # Simpson's paradox variant (hiring)
        "Company X hired 40% of male applicants and 50% of female applicants overall. "
        "But in every single department, the male hiring rate was higher than the female rate. "
        "How is this possible? Give a concrete numerical example.",
    ],
    num_samples=1,
    tags=["cross-domain", "minimal-trap", "generalization", "logic", "causal", "code"],
)
