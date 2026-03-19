"""
Experiment: Decompose the SkillConfig Gain (follow-up to cognitive_traps)

Hypothesis (from Exp 1 judge): The reasoning quality gain may come entirely from
"naming the trap" rather than the full structured template. Test 3 agents:

  A. baseline        — no system prompt
  B. minimal_trap    — one-liner: name the wrong intuition first
  C. full_scaffold   — full RESTATE/INTUITION-CHECK/WORK/VERIFY template

Tasks: MIX of easy (classic CRT, model knows them) + hard (novel/less-known,
model less likely to have memorised). This tests whether prompting helps MORE
when the problem is harder.
"""
from openbench.types import AgentConfig, SkillConfig, TournamentConfig

FULL_SCAFFOLD = SkillConfig(
    name="full_scaffold_solver",
    version="1.0.0",
    description="Full RESTATE/INTUITION-CHECK/WORK/VERIFY template",
    system_prompt=(
        "You are a rigorous problem solver. For every problem:\n"
        "1. RESTATE: Paraphrase the problem in your own words\n"
        "2. INTUITION CHECK: State your first instinct — then actively challenge it\n"
        "3. WORK: Solve step by step with explicit algebra or logic\n"
        "4. VERIFY: Plug your answer back in to confirm all constraints are met\n"
        "5. ANSWER: State the final answer clearly on its own line\n\n"
        "Be especially suspicious when the answer feels obvious."
    ),
    required_tools=[],
)

tournament = TournamentConfig(
    name="reasoning_decompose_3way",
    description=(
        "3-way: baseline vs minimal-trap vs full-scaffold. "
        "Tests whether 'name the trap' alone captures most of the reasoning gain. "
        "Mix of easy (CRT) + hard (novel) problems."
    ),
    configs=[
        AgentConfig(
            name="baseline",
            model="claude-haiku-4-5",
            system_prompt=None,
            allowed_tools=[],
            max_turns=2,
        ),
        AgentConfig(
            name="minimal_trap",
            model="claude-haiku-4-5",
            system_prompt=(
                "Before solving, write one sentence: state the most common wrong "
                "intuitive answer and explain in one phrase why it fails. "
                "Then solve the problem."
            ),
            allowed_tools=[],
            max_turns=2,
        ),
        AgentConfig(
            name="full_scaffold",
            model="claude-haiku-4-5",
            system_prompt=FULL_SCAFFOLD,
            allowed_tools=[],
            max_turns=2,
        ),
    ],
    tasks=[
        # ── EASY (classic CRT — benchmark-known) ─────────────────────────
        # Bat & ball
        "A bat and a ball together cost $1.10. The bat costs exactly $1.00 more "
        "than the ball. How much does the ball cost? Answer in cents.",

        # ── MEDIUM (less famous, model may or may not know) ───────────────
        # Average speed trap
        "A car drives from city A to city B at 30 mph, then returns at 60 mph. "
        "What is the average speed for the entire round trip? Give a single number in mph.",

        # Sock drawer
        "A drawer contains 6 red socks and 6 blue socks. You reach in without "
        "looking. What is the minimum number of socks you must take to guarantee "
        "you have a matching pair? Give a single number.",

        # % removal paradox
        "A room has 100 people. 99 of them are wearing hats. How many hat-wearers "
        "must leave so that exactly 98% of the remaining people are wearing hats? "
        "Give a single number.",

        # ── HARD (novel multi-step, requires careful reasoning) ────────────
        # Probability with replacement
        "A bag contains 3 red and 2 blue marbles. You draw one marble, note its "
        "color, put it back, then draw again. What is the probability that you "
        "drew the SAME color both times? Express as a simplified fraction.",

        # Conditional probability trap
        "I have two children. You learn that at least one is a girl born on a "
        "Tuesday. What is the probability that both children are girls? "
        "(Assume equal probability for each day of week and each sex.) "
        "Express as a simplified fraction.",

        # Compounding asymmetry
        "A stock rises 50% on Monday, then falls 50% on Tuesday. "
        "On Wednesday it rises 50% again, then falls 50% on Thursday. "
        "After these four days, is the stock price higher, lower, or equal to "
        "the original? By what percentage (to 2 decimal places)?",

        # Chain probability
        "A factory has 3 quality control stations. Each station independently "
        "catches defects with probability 0.9. A defective item must be caught "
        "by ALL THREE stations to be removed. What is the probability a defective "
        "item makes it through undetected? Express as a percentage to 2 decimal places.",
    ],
    num_samples=1,
    tags=["reasoning", "cognitive-traps", "decompose", "tournament"],
)
