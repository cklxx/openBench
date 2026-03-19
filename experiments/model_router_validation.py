"""
Experiment: Validate ModelRouter — auto-select haiku/sonnet by task complexity.

Based on benchmark results:
- haiku matches sonnet on simple tasks (< 500 estimated tokens)
- sonnet is more efficient on complex tasks (saves tokens/turns)
- haiku is 5× cheaper per token

ModelRouter should:
- Pick haiku for simple tasks → save cost, no quality loss
- Pick sonnet for complex tasks → better efficiency, worth the premium
- Overall: cost between haiku-only and sonnet-only, quality ≥ both

3-way tournament: fixed haiku vs fixed sonnet vs auto-router.
Mix of simple and complex tasks with verifiable answers.
"""
from openbench.types import AgentConfig, ModelRouter, TaskItem, TournamentConfig

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer questions concisely and accurately. "
    "For coding tasks, write clean, working code."
)

tournament = TournamentConfig(
    name="model_router_validation",
    description=(
        "3-way: fixed haiku vs fixed sonnet vs auto-router. "
        "Validates that ModelRouter picks the right model per task complexity."
    ),
    configs=[
        AgentConfig(
            name="haiku_fixed",
            model="claude-haiku-4-5",
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=["Bash"],
            max_turns=10,
        ),
        AgentConfig(
            name="sonnet_fixed",
            model="claude-sonnet-4-6",
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=["Bash"],
            max_turns=10,
        ),
        AgentConfig(
            name="auto_router",
            model=ModelRouter(
                default="claude-haiku-4-5",
                upgrade="claude-sonnet-4-6",
                threshold_tokens=500,
            ),
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=["Bash"],
            max_turns=10,
        ),
    ],
    tasks=[
        # ── SIMPLE tasks (< 500 tokens input → should route to haiku) ────
        TaskItem(
            prompt="What is 17 × 23? Give just the number.",
            expected="391",
            check_fn='"391" in output',
            difficulty="easy",
            tags=["simple", "arithmetic"],
        ),
        TaskItem(
            prompt="What is the capital of France? One word answer.",
            expected="Paris",
            check_fn='"Paris" in output or "paris" in output',
            difficulty="easy",
            tags=["simple", "factual"],
        ),
        TaskItem(
            prompt="Convert 72°F to Celsius. Round to 1 decimal. Just the number.",
            expected="22.2",
            check_fn='"22.2" in output',
            difficulty="easy",
            tags=["simple", "conversion"],
        ),
        TaskItem(
            prompt="What is the GCD of 48 and 36? Give just the number.",
            expected="12",
            check_fn='"12" in output',
            difficulty="easy",
            tags=["simple", "math"],
        ),

        # ── COMPLEX tasks (> 500 tokens input → should route to sonnet) ──
        TaskItem(
            prompt=(
                "Write a Python function called `is_balanced(s)` that checks if a string "
                "of brackets is balanced. It should handle '()', '[]', and '{}'. "
                "The function should return True if balanced, False otherwise.\n\n"
                "Examples:\n"
                "  is_balanced('()[]{}') → True\n"
                "  is_balanced('([{}])') → True\n"
                "  is_balanced('([)]') → False\n"
                "  is_balanced('{[}') → False\n"
                "  is_balanced('') → True\n\n"
                "Write the function and verify it works by running the examples above "
                "using Bash with python3 -c. Show the test output."
            ),
            expected="True",
            check_fn='"True" in output and "False" in output',
            difficulty="medium",
            tags=["complex", "coding"],
        ),
        TaskItem(
            prompt=(
                "Analyze the following data and answer the questions:\n\n"
                "Monthly sales data (units):\n"
                "Jan: 120, Feb: 135, Mar: 148, Apr: 162, May: 175, Jun: 190,\n"
                "Jul: 180, Aug: 195, Sep: 210, Oct: 225, Nov: 245, Dec: 260\n\n"
                "1. What is the total annual sales?\n"
                "2. What is the average monthly sales (rounded to 1 decimal)?\n"
                "3. Which month had the highest growth rate compared to previous month?\n"
                "4. What is the median monthly sales?\n\n"
                "Use Python with Bash to compute exact answers. Show calculations."
            ),
            expected="2245",
            check_fn='"2245" in output',
            difficulty="medium",
            tags=["complex", "data-analysis"],
        ),
        TaskItem(
            prompt=(
                "A database has three tables:\n\n"
                "employees(id, name, department_id, salary, hire_date)\n"
                "departments(id, name, budget)\n"
                "projects(id, name, department_id, deadline, status)\n\n"
                "Write SQL queries for:\n"
                "1. Find all departments where average salary exceeds $75,000\n"
                "2. List employees hired in the last year who work in departments "
                "with budget > $1M\n"
                "3. Find departments that have no active projects\n"
                "4. Calculate the total salary expenditure per department as a "
                "percentage of that department's budget\n\n"
                "Write clean, correct SQL. Explain each query briefly."
            ),
            expected="SELECT",
            check_fn='"SELECT" in output and "department" in output.lower()',
            difficulty="hard",
            tags=["complex", "sql"],
        ),
        TaskItem(
            prompt=(
                "Implement a function `longest_palindrome_substring(s)` that finds "
                "the longest palindromic substring in a given string. Use the expand-around-center "
                "approach for O(n²) time complexity.\n\n"
                "Test with these cases using Bash:\n"
                "  'babad' → 'bab' or 'aba' (either is correct)\n"
                "  'cbbd' → 'bb'\n"
                "  'a' → 'a'\n"
                "  'racecar' → 'racecar'\n"
                "  'abcde' → 'a' (any single char)\n\n"
                "Write the implementation in Python and verify all test cases pass."
            ),
            expected="palindrome",
            check_fn='"racecar" in output.lower() or "palindrom" in output.lower()',
            difficulty="hard",
            tags=["complex", "algorithm"],
        ),
    ],
    num_samples=5,
    tags=["model-router", "validation", "cost-optimization", "n5"],
)
