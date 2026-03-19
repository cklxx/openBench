"""
Experiment: Structured Reasoning vs Baseline on Cognitive Trap Tasks

Hypothesis: A SkillConfig that enforces explicit trap-checking and step-by-step
reasoning will significantly outperform no-prompt on tasks where human (and LLM)
intuition is systematically wrong.

Tasks chosen because:
- All have objectively verifiable correct answers
- All have a compelling but WRONG intuitive answer
- Models commonly fail these without deliberate reasoning
- Cheap: no tools, max_turns=2, haiku
"""
from openbench.types import SkillConfig, AgentConfig, Experiment, DiffSpec

REASONING_SKILL = SkillConfig(
    name="trap_aware_solver",
    version="1.0.0",
    description="Deliberate step-by-step solver that actively hunts for cognitive traps",
    system_prompt=(
        "You are a rigorous problem solver. For every problem:\n"
        "1. RESTATE: Paraphrase the problem in your own words\n"
        "2. INTUITION CHECK: State what your first instinct says — then actively challenge it\n"
        "3. WORK: Solve step by step with explicit algebra or logic\n"
        "4. VERIFY: Plug your answer back in to confirm it satisfies all constraints\n"
        "5. ANSWER: State the final answer clearly on its own line\n\n"
        "Be especially suspicious when the answer feels obvious — that's when traps appear."
    ),
    required_tools=[],
)

experiment = Experiment(
    name="cognitive_traps_skill_vs_baseline",
    description=(
        "Does structured trap-aware reasoning (SkillConfig) beat no-prompt "
        "on classic cognitive bias / counterintuitive math problems?"
    ),
    diff=DiffSpec(
        field="system_prompt",
        description="SkillConfig (trap-aware step-by-step) vs None (no system prompt)",
    ),
    agent_a=AgentConfig(
        name="baseline",
        model="claude-haiku-4-5",
        system_prompt=None,
        allowed_tools=[],
        max_turns=2,
    ),
    agent_b=AgentConfig(
        name="trap_aware",
        model="claude-haiku-4-5",
        system_prompt=REASONING_SKILL,
        allowed_tools=[],
        max_turns=2,
    ),
    tasks=[
        # CRT-1: Bat and ball (intuitive answer: 10¢, correct: 5¢)
        "A bat and a ball together cost $1.10. The bat costs exactly $1.00 more than the ball. "
        "How much does the ball cost? Give a numerical answer in cents.",

        # CRT-2: Lily pads (intuitive: 24 days, correct: 47 days)
        "A lily pad patch doubles in size every day. It takes 48 days for the patch to cover "
        "the entire lake. How many days does it take to cover HALF the lake? "
        "Give a single number.",

        # CRT-3: Widgets (intuitive: 100 minutes, correct: 5 minutes)
        "If 5 machines take 5 minutes to make 5 widgets, how long does it take "
        "100 machines to make 100 widgets? Give a single number in minutes.",

        # Monty Hall (intuitive: 50/50, correct: switch gives 2/3)
        "You're on a game show. There are 3 doors: one hides a car, two hide goats. "
        "You pick Door 1. The host (who always knows where the car is) opens Door 3, "
        "revealing a goat. He offers you a switch to Door 2. "
        "What is the probability of winning the car if you switch? Express as a fraction.",

        # Percentage trap (intuitive: same price, correct: 4% lower)
        "A jacket is discounted by 20%, then the new price is increased by 20%. "
        "Compared to the original price, is the final price higher, lower, or equal? "
        "By exactly what percentage?",

        # Rope around Earth (intuitive: huge amount, correct: ~6.28 meters ≈ 2π)
        "A rope is tied tightly around the Earth's equator (circumference ≈ 40,000 km). "
        "You want to raise the rope uniformly 1 metre above the surface all the way around. "
        "How many extra metres of rope do you need? Give a numerical answer to 2 decimal places.",

        # Simpson's paradox setup
        "Hospital A has a 90% survival rate for minor surgery and 30% for major surgery. "
        "Hospital B has a 93% survival rate for minor surgery and 40% for major surgery. "
        "Hospital A treats 1000 minor cases and 1000 major cases. "
        "Hospital B treats 100 minor cases and 1900 major cases. "
        "Which hospital has the higher OVERALL survival rate? Show your calculation.",
    ],
    num_samples=1,
    tags=["cognitive-bias", "reasoning", "skill-config"],
)
