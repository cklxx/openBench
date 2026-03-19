"""
Experiment: Domain-Specific Prompts vs Universal Prompt vs Baseline

Follow-up from minimal_trap_cross_domain: the universal "name the wrong intuition"
prompt didn't generalize. Hypothesis: domain-SPECIFIC prompts will outperform both
the universal prompt and no prompt, because they activate the right reasoning mode.

Test 3 agents on mixed tasks across 3 domains:
  A. baseline — no system prompt
  B. universal — one generic metacognitive prompt
  C. domain_specific — uses a tailored prompt per task domain (simulated by
     picking the right prompt for each task)

Since we can't change the system prompt per-task in a single experiment, we
test domain-specific prompts in their home domain vs the universal prompt.

Domain: code debugging (where "name the wrong intuition" failed hardest)
"""
from openbench.types import AgentConfig, Experiment, DiffSpec

experiment = Experiment(
    name="domain_specific_prompts",
    description=(
        "Code debugging: domain-specific 'trace execution' prompt vs universal "
        "'name wrong intuition' prompt. Tests whether tailored prompts beat generic ones."
    ),
    diff=DiffSpec(
        field="system_prompt",
        description="Domain-specific code debugging prompt vs universal metacognitive prompt",
    ),
    agent_a=AgentConfig(
        name="universal_prompt",
        model="claude-haiku-4-5",
        system_prompt=(
            "Before answering, write one sentence: state the most common wrong "
            "intuitive answer and explain in one phrase why it fails. "
            "Then answer the question."
        ),
        allowed_tools=[],
        max_turns=2,
    ),
    agent_b=AgentConfig(
        name="code_specific",
        model="claude-haiku-4-5",
        system_prompt=(
            "You are debugging code. For every bug:\n"
            "1. TRACE: Walk through the code line by line with concrete values\n"
            "2. SPOT: Identify the exact line where behavior diverges from intent\n"
            "3. PROVE: Show a minimal input that triggers the bug\n"
            "4. FIX: Give the corrected code\n"
            "Be precise — state the actual vs expected output."
        ),
        allowed_tools=[],
        max_turns=2,
    ),
    tasks=[
        # Classic closure bug
        "What does this code print and why?\n"
        "```python\n"
        "funcs = []\n"
        "for i in range(3):\n"
        "    funcs.append(lambda: i)\n"
        "print([f() for f in funcs])\n"
        "```",

        # Off-by-one in binary search
        "This binary search has a bug. What input triggers it?\n"
        "```python\n"
        "def binary_search(arr, target):\n"
        "    lo, hi = 0, len(arr)\n"
        "    while lo < hi:\n"
        "        mid = (lo + hi) // 2\n"
        "        if arr[mid] == target:\n"
        "            return mid\n"
        "        elif arr[mid] < target:\n"
        "            lo = mid + 1\n"
        "        else:\n"
        "            hi = mid\n"
        "    return -1\n"
        "```\n"
        "Hint: it does NOT have the classic overflow bug.",

        # String mutation surprise
        "What's wrong with this deduplication?\n"
        "```python\n"
        "def dedupe(lst):\n"
        "    seen = set()\n"
        "    result = []\n"
        "    for item in lst:\n"
        "        if item not in seen:\n"
        "            seen.add(item)\n"
        "            result.append(item)\n"
        "    return result\n\n"
        "data = [{'a': 1}, {'b': 2}, {'a': 1}]\n"
        "print(dedupe(data))  # TypeError!\n"
        "```",

        # Truthiness trap
        "This function should return the first truthy value or a default. What's the bug?\n"
        "```python\n"
        "def first_truthy(*args, default=None):\n"
        "    for arg in args:\n"
        "        if arg:\n"
        "            return arg\n"
        "    return default\n\n"
        "result = first_truthy(0, '', [], 42)\n"
        "print(result)  # prints 42, correct\n\n"
        "result2 = first_truthy(0, 0.0, False, default='fallback')\n"
        "print(result2)  # prints 'fallback', but what about numpy?\n\n"
        "import numpy as np\n"
        "result3 = first_truthy(np.array([1,2,3]), default='none')\n"
        "print(result3)  # ???\n"
        "```",

        # Sorting stability / key function
        "What does this print? Is the sort stable?\n"
        "```python\n"
        "records = [\n"
        "    ('Alice', 85),\n"
        "    ('Bob', 92),\n"
        "    ('Charlie', 85),\n"
        "    ('Diana', 92),\n"
        "]\n"
        "# Sort by score descending, then by name ascending for ties\n"
        "records.sort(key=lambda r: (-r[1], r[0]))\n"
        "print(records)\n\n"
        "# Now try with a different approach\n"
        "records2 = records.copy()\n"
        "records2.sort(key=lambda r: r[0])  # sort by name\n"
        "records2.sort(key=lambda r: -r[1])  # then by score\n"
        "print(records2)\n"
        "# Are the results the same?\n"
        "```",

        # Integer caching / identity vs equality
        "Explain the output:\n"
        "```python\n"
        "a = 256\n"
        "b = 256\n"
        "print(a is b)  # True\n\n"
        "c = 257\n"
        "d = 257\n"
        "print(c is d)  # ???\n\n"
        "e = 257; f = 257\n"
        "print(e is f)  # ???\n"
        "```\n"
        "Why might `c is d` and `e is f` give different results?",
    ],
    num_samples=1,
    tags=["domain-specific", "code-debugging", "prompt-design"],
)
