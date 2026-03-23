"""
Context Pressure: Replace Scratchpad vs Additive Scratchpad

Research insight (JetBrains "Complexity Trap", NeurIPS 2025):
- Observation masking (hiding old tool outputs) matches LLM summarization
- Simple masking is 50% cheaper than raw agent
- LLM summarization caused 15% longer trajectories

Our previous scratchpad experiments used ADDITIVE notes — agent reads files
AND writes notes, increasing total context. Research suggests the scratchpad
should REPLACE context, not add to it.

Design: Two scratchpad strategies on 15-file codebase:
- Agent A (additive): Current approach — read files + write notes + can re-read
- Agent B (replace): Read file → summarize in notes → FORBIDDEN from re-reading

If replace > additive: The problem was context bloat, not note-taking itself
If replace ≈ additive: Note-taking is inherently wasteful at this scale
If replace < additive: Losing raw file access is worse than the context savings

max_turns=25, num_samples=5. Uses context_pressure_boundary's 15-file codebase.
"""
import importlib.util, os
_spec = importlib.util.spec_from_file_location(
    "cpb", os.path.join(os.path.dirname(__file__), "context_pressure_boundary.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

from openbench.types import AgentConfig, Experiment, DiffSpec, TaskItem

ADDITIVE_SCRATCHPAD = """\
You are a senior developer debugging a Python e-commerce application.

STRICT RULES — follow these EXACTLY:

STEP 1: Create _notes.md as your FIRST action.

STEP 2: Run test_app.py to see failures. Update _notes.md with failures.

STEP 3: Read each source file in app/. After reading EACH file, update _notes.md:
  - File purpose, key functions, imports
  - Suspicious code — potential bugs

STEP 4: Review _notes.md and write a DIAGNOSIS section.

STEP 5: Fix all bugs. Run tests to verify. Print the output.

CONSTRAINTS:
- You MUST update _notes.md after reading each file
- You CAN re-read source files whenever needed
- Your notes supplement your memory — they don't replace it
"""

REPLACE_SCRATCHPAD = """\
You are a senior developer debugging a Python e-commerce application.

STRICT RULES — follow these EXACTLY:

STEP 1: Create _notes.md as your FIRST action.

STEP 2: Run test_app.py to see failures. Update _notes.md with failures.

STEP 3: Read each source file in app/ ONE TIME. After reading each file,
write a COMPLETE summary in _notes.md:
  - All function signatures and what they do
  - All imports and dependencies
  - Suspicious code — potential bugs
  - Key implementation details you'll need for fixing

STEP 4: You are now FORBIDDEN from using Read on any app/*.py file you have
already summarized. Work ONLY from _notes.md for all subsequent analysis.

STEP 5: Review _notes.md and write a DIAGNOSIS section.

STEP 6: Fix all bugs based on your notes. Run tests to verify. Print output.

CONSTRAINTS:
- After summarizing a file in _notes.md, you are FORBIDDEN from re-reading it
- Your notes REPLACE the source files — make them comprehensive
- If you need details from a file, check _notes.md first
- This approach saves context space by not re-loading file contents
"""

experiment = Experiment(
    name="context_pressure_replace",
    description=(
        "Additive scratchpad (notes + re-read files) vs replace scratchpad "
        "(notes replace files, no re-reading). 15-file codebase. "
        "Tests whether observation masking helps vs raw note-taking."
    ),
    diff=DiffSpec(
        field="system_prompt",
        description="Additive scratchpad (can re-read) vs replace scratchpad (notes replace files)",
    ),
    agent_a=AgentConfig(
        name="additive_scratchpad",
        model="claude-haiku-4-5",
        system_prompt=ADDITIVE_SCRATCHPAD,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=25,
    ),
    agent_b=AgentConfig(
        name="replace_scratchpad",
        model="claude-haiku-4-5",
        system_prompt=REPLACE_SCRATCHPAD,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=25,
    ),
    tasks=[
        TaskItem(
            prompt=(
                "Fix all bugs in this e-commerce application. The code is in app/. "
                "Run: python test_app.py\n"
                "There are multiple bugs across different files. "
                "Print the final test output."
            ),
            expected="PASSED",
            check_fn='"PASSED" in output or "pass" in output.lower()',
            difficulty="very_hard",
            tags=["multi-file", "cross-dependency", "15-files"],
        ),
    ],
    setup_files=_mod.SETUP_FILES,
    num_samples=5,
    tags=["working-memory", "observation-masking", "replace-vs-additive"],
)
