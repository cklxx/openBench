"""
Experiment: Novel Math Problems with Objective Correctness Checking

Previous experiments showed haiku-4-5 aces well-known problems. This experiment
uses NOVEL multi-step problems with made-up constants that cannot be memorized
from training data. Each task has an objectively verifiable expected answer.

Tests whether the minimal_trap prompt helps when the model genuinely needs to
reason (not pattern-match from memory).

Key infrastructure improvements tested:
- TaskItem with expected answers → objective correctness scoring
- check_fn for programmatic verification
- Difficulty tagging for stratified analysis
"""
from openbench.types import AgentConfig, Experiment, DiffSpec, TaskItem

experiment = Experiment(
    name="novel_math_with_answers",
    description=(
        "Novel multi-step math with verifiable answers. "
        "Tests whether minimal_trap helps on genuinely unfamiliar problems."
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
            "Before solving, write one sentence: state the most common wrong "
            "intuitive answer and explain in one phrase why it fails. "
            "Then solve the problem."
        ),
        allowed_tools=[],
        max_turns=2,
    ),
    tasks=[
        # ── EASY: Direct calculation with unusual numbers ────────────────
        TaskItem(
            prompt=(
                "A store sells widgets at $7.30 each. If you buy 13 widgets and "
                "pay with a $100 bill, how much change do you receive? "
                "Give the exact dollar amount."
            ),
            expected="$5.10",
            check_fn='"5.10" in output',
            difficulty="easy",
            tags=["arithmetic"],
        ),

        # ── MEDIUM: Multi-step with unit conversion ──────────────────────
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
            tags=["multi-step", "rates"],
        ),

        # ── MEDIUM: Probability with non-standard dice ───────────────────
        TaskItem(
            prompt=(
                "A bag has 4 red, 3 blue, and 2 green marbles. You draw 2 marbles "
                "WITHOUT replacement. What is the probability that both marbles are "
                "the same color? Express as a simplified fraction."
            ),
            expected="5/18",
            check_fn='"5/18" in output',
            difficulty="medium",
            tags=["probability", "combinatorics"],
        ),

        # ── MEDIUM: Compound interest with unusual terms ─────────────────
        TaskItem(
            prompt=(
                "You invest $2,500 at 6% annual interest compounded quarterly. "
                "After exactly 3 years, what is the total amount? "
                "Round to the nearest cent."
            ),
            expected="$2,986.50",
            check_fn='"2986.5" in output or "2,986.5" in output',
            difficulty="medium",
            tags=["compound-interest"],
        ),

        # ── HARD: System of equations with a twist ───────────────────────
        TaskItem(
            prompt=(
                "Alice, Bob, and Charlie split a bill. Alice pays 3 times what "
                "Bob pays. Charlie pays $14 more than Bob. The total bill is $94. "
                "How much does each person pay? Give all three amounts."
            ),
            expected="Alice: $48, Bob: $16, Charlie: $30",
            check_fn='"48" in output and "16" in output and "30" in output',
            difficulty="hard",
            tags=["algebra", "system-of-equations"],
        ),

        # ── HARD: Geometric series with non-obvious sum ──────────────────
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
            tags=["geometric-series"],
        ),

        # ── HARD: Modular arithmetic ─────────────────────────────────────
        TaskItem(
            prompt=(
                "What is the remainder when 7^100 is divided by 13? "
                "Give a single number."
            ),
            expected="9",
            # 7^1=7, 7^2=49≡10, 7^3≡70≡5, 7^4≡35≡9, 7^5≡63≡11, 7^6≡77≡12,
            # 7^7≡84≡6, 7^8≡42≡3, 7^9≡21≡8, 7^10≡56≡4, 7^11≡28≡2, 7^12≡14≡1
            # period=12, 100 mod 12 = 4, 7^4 mod 13 = 9
            check_fn='output.strip().endswith("9") or "= 9" in output or "is 9" in output',
            difficulty="hard",
            tags=["number-theory", "modular-arithmetic"],
        ),

        # ── HARD: Combinatorics ──────────────────────────────────────────
        TaskItem(
            prompt=(
                "How many 4-digit numbers (1000-9999) have all digits strictly "
                "increasing (each digit is larger than the one before it)? "
                "Give a single number."
            ),
            # C(9,4) = 126 (choose 4 from {1,...,9}, order forced by increasing)
            expected="126",
            check_fn='"126" in output',
            difficulty="hard",
            tags=["combinatorics"],
        ),

        # ── VERY HARD: Multi-step logic + arithmetic ─────────────────────
        TaskItem(
            prompt=(
                "In a tournament, 7 teams play round-robin (each team plays every other "
                "team exactly once). A win is worth 3 points, a draw 1 point each, "
                "a loss 0 points. After all games, the total points across all teams "
                "is 84. How many games ended in a draw? Show your work."
            ),
            # Total games = C(7,2) = 21
            # Each decisive game awards 3 total pts; each draw awards 2 total pts
            # Let d = draws. 3*(21-d) + 2*d = 84 → 63 - 3d + 2d = 84 → -d = 21 → d = -21???
            # Wait, let me recalculate. 3(21-d) + 2d = 84 → 63 - d = 84 → d = -21
            # That can't be right. Max points = 63 (all decisive). 84 > 63, impossible.
            # Actually I made an error. Let me fix: 84 total points, 21 games.
            # Each game distributes either 3 pts (win/loss) or 2 pts (draw).
            # 3(21-d) + 2d = 84 → 63 - d = 84 → d = -21. That's impossible.
            # So 84 total points from 21 games is impossible. The correct answer
            # is that this is impossible / no solution exists.
            # Actually wait — max is 21*3 = 63. 84 > 63, so impossible.
            expected="impossible",
            check_fn='"impossible" in output.lower() or "not possible" in output.lower() or "cannot" in output.lower()',
            difficulty="very_hard",
            tags=["logic", "trap", "impossible"],
        ),

        # ── VERY HARD: Rate problem with a hidden constraint ─────────────
        TaskItem(
            prompt=(
                "Worker A can finish a job in 12 hours alone. Worker B can finish the "
                "same job in 18 hours alone. They start working together, but after 4 hours, "
                "Worker A leaves. How many more hours does Worker B need to finish the "
                "remaining work alone? Give an exact answer as a fraction or decimal."
            ),
            # Together rate: 1/12 + 1/18 = 3/36 + 2/36 = 5/36 per hour
            # In 4 hours: 4 * 5/36 = 20/36 = 5/9 done
            # Remaining: 1 - 5/9 = 4/9
            # B alone: (4/9) / (1/18) = 4/9 * 18 = 8 hours
            expected="8",
            check_fn='"8 hours" in output.lower() or "= 8" in output or output.strip().endswith("8")',
            difficulty="very_hard",
            tags=["rates", "multi-step"],
        ),
    ],
    num_samples=1,
    tags=["novel-math", "objective-correctness", "difficulty-stratified"],
)
