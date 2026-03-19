"""
Experiment: Code Fix with Verifiable Test Suites

Unlike previous code debugging experiments that asked agents to EXPLAIN bugs,
this experiment requires agents to PRODUCE FIXED CODE that passes test cases.
Correctness is objective: the test suite either passes or it doesn't.

Tests domain-specific prompt ("trace execution → fix") vs baseline.
Each task provides buggy code + test suite via setup_files.
Agent must read, diagnose, and output the corrected function.

The check_fn extracts the function from output and runs it against test cases.
"""
from openbench.types import AgentConfig, Experiment, DiffSpec, TaskItem

# Test verification functions (run as check_fn)
# These extract the function definition from agent output and test it

CHECK_FIX_PAIRS = 'exec(compile(output[output.index("def "):output.index("\\n\\n", output.index("def "))], "<fix>", "exec"), _ns:={}) or _ns["find_pairs"]([3,3,3], 6) == [(3,3)] and _ns["find_pairs"]([1,2,3,4], 5) == [(1,4),(2,3)]'

CHECK_FIX_TRIANGLE = 'exec(compile(output[output.index("def "):output.index("\\n\\n", output.index("def "))], "<fix>", "exec"), _ns:={}) or _ns["is_valid_triangle"](1,2,10) == False and _ns["is_valid_triangle"](3,4,5) == True'

experiment = Experiment(
    name="code_fix_verifiable",
    description=(
        "Agent must fix buggy Python code. Correctness verified by test cases. "
        "Domain-specific 'trace + fix' prompt vs baseline."
    ),
    diff=DiffSpec(
        field="system_prompt",
        description="Code-specific fix prompt vs no prompt",
    ),
    agent_a=AgentConfig(
        name="baseline",
        model="claude-haiku-4-5",
        system_prompt=None,
        allowed_tools=["Read", "Glob", "Bash"],
        max_turns=10,
    ),
    agent_b=AgentConfig(
        name="code_fixer",
        model="claude-haiku-4-5",
        system_prompt=(
            "You are fixing buggy code. For each bug:\n"
            "1. Read the file and its test suite\n"
            "2. Run the tests to see the failure\n"
            "3. Trace execution with the failing input\n"
            "4. Fix the code\n"
            "5. Run the tests again to verify your fix passes\n"
            "IMPORTANT: Your final answer must include the complete corrected function."
        ),
        allowed_tools=["Read", "Glob", "Bash"],
        max_turns=10,
    ),
    tasks=[
        TaskItem(
            prompt=(
                "Read bug_dedup.py. It's supposed to deduplicate a list while preserving order. "
                "Run test_dedup.py to see the failure. Fix the function and verify tests pass. "
                "Show the complete fixed function."
            ),
            expected="def dedupe",
            check_fn='"def dedupe" in output and "seen" in output',
            difficulty="easy",
            tags=["list", "dedup"],
        ),
        TaskItem(
            prompt=(
                "Read bug_flatten.py. It's supposed to recursively flatten nested lists. "
                "Run test_flatten.py to see the failure. Fix the function and verify tests pass. "
                "Show the complete fixed function."
            ),
            expected="def flatten",
            check_fn='"def flatten" in output',
            difficulty="medium",
            tags=["recursion", "list"],
        ),
        TaskItem(
            prompt=(
                "Read bug_lru.py. It implements an LRU cache but has bugs. "
                "Run test_lru.py to see the failures. Fix all bugs and verify tests pass. "
                "Show the complete fixed class."
            ),
            expected="class LRUCache",
            check_fn='"class LRUCache" in output',
            difficulty="hard",
            tags=["data-structure", "lru-cache"],
        ),
        TaskItem(
            prompt=(
                "Read bug_interval.py. It's supposed to merge overlapping intervals. "
                "Run test_interval.py to see the failure. Fix the function and verify tests pass. "
                "Show the complete fixed function."
            ),
            expected="def merge_intervals",
            check_fn='"def merge_intervals" in output',
            difficulty="medium",
            tags=["intervals", "sorting"],
        ),
        TaskItem(
            prompt=(
                "Read bug_graph.py. It implements BFS shortest path but has bugs. "
                "Run test_graph.py to see the failures. Fix and verify. "
                "Show the complete fixed function."
            ),
            expected="def bfs_shortest_path",
            check_fn='"def bfs_shortest_path" in output',
            difficulty="hard",
            tags=["graph", "bfs"],
        ),
    ],
    setup_files={
        # ── Bug 1: Dedup with unhashable items ──────────────────────────
        "bug_dedup.py": '''\
def dedupe(lst):
    """Remove duplicates, preserving order. Must work with unhashable items."""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)  # Bug: fails on unhashable (dicts, lists)
            result.append(item)
    return result
''',
        "test_dedup.py": '''\
from bug_dedup import dedupe

# Test 1: Normal hashable items
assert dedupe([1, 2, 3, 2, 1]) == [1, 2, 3], "Failed on integers"

# Test 2: Strings
assert dedupe(["a", "b", "a", "c"]) == ["a", "b", "c"], "Failed on strings"

# Test 3: Unhashable items (dicts) — this is the bug trigger
assert dedupe([{"a": 1}, {"b": 2}, {"a": 1}]) == [{"a": 1}, {"b": 2}], "Failed on dicts"

# Test 4: Mixed types
assert dedupe([1, "1", 1, "1"]) == [1, "1"], "Failed on mixed types"

# Test 5: Empty
assert dedupe([]) == [], "Failed on empty"

print("All tests passed!")
''',

        # ── Bug 2: Flatten nested lists ─────────────────────────────────
        "bug_flatten.py": '''\
def flatten(lst):
    """Recursively flatten nested lists."""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

# Bug: doesn't handle tuples or other iterables
# Also: doesn't handle deeply nested empty lists correctly
''',
        "test_flatten.py": '''\
from bug_flatten import flatten

# Test 1: Simple nesting
assert flatten([1, [2, 3], [4, [5, 6]]]) == [1, 2, 3, 4, 5, 6]

# Test 2: Deep nesting
assert flatten([[[1]], [[2]], [[[3]]]]) == [1, 2, 3]

# Test 3: Tuples should also be flattened
assert flatten([1, (2, 3), [4, (5,)]]) == [1, 2, 3, 4, 5], "Failed on tuples"

# Test 4: Empty nested
assert flatten([[], [[]], [[], []]]) == [], "Failed on empty nested"

# Test 5: Strings should NOT be flattened
assert flatten(["abc", ["def"]]) == ["abc", "def"], "Strings should not be flattened"

print("All tests passed!")
''',

        # ── Bug 3: LRU Cache ───────────────────────────────────────────
        "bug_lru.py": '''\
from collections import OrderedDict

class LRUCache:
    """Least-recently-used cache with fixed capacity."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key):
        """Return value if key exists, else -1. Mark as recently used."""
        if key in self.cache:
            return self.cache[key]  # Bug 1: doesn't move to end
        return -1

    def put(self, key, value):
        """Insert or update. Evict LRU item if at capacity."""
        if key in self.cache:
            self.cache[key] = value  # Bug 2: doesn't move to end on update
        else:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=True)  # Bug 3: should be last=False for FIFO eviction
            self.cache[key] = value
''',
        "test_lru.py": '''\
from bug_lru import LRUCache

# Test 1: Basic put/get
cache = LRUCache(2)
cache.put(1, 1)
cache.put(2, 2)
assert cache.get(1) == 1, "Basic get failed"

# Test 2: Eviction
cache.put(3, 3)  # Evicts key 2 (LRU)
assert cache.get(2) == -1, "Key 2 should be evicted"
assert cache.get(3) == 3, "Key 3 should exist"

# Test 3: Access refreshes LRU order
cache2 = LRUCache(2)
cache2.put(1, 1)
cache2.put(2, 2)
cache2.get(1)     # Access 1, making 2 the LRU
cache2.put(3, 3)  # Should evict 2, not 1
assert cache2.get(1) == 1, "Key 1 should survive (recently accessed)"
assert cache2.get(2) == -1, "Key 2 should be evicted (LRU)"

# Test 4: Update refreshes position
cache3 = LRUCache(2)
cache3.put(1, 1)
cache3.put(2, 2)
cache3.put(1, 10)  # Update key 1
cache3.put(3, 3)   # Should evict 2 (LRU after 1 was updated)
assert cache3.get(1) == 10, "Updated value wrong"
assert cache3.get(2) == -1, "Key 2 should be evicted"

print("All tests passed!")
''',

        # ── Bug 4: Merge intervals ─────────────────────────────────────
        "bug_interval.py": '''\
def merge_intervals(intervals):
    """Merge overlapping intervals. Input: list of [start, end]. Returns merged list."""
    if not intervals:
        return []
    # Bug: doesn't sort first
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:  # Bug: should be < or <=?
            merged[-1][1] = end  # Bug: should take max, not just replace
        else:
            merged.append([start, end])
    return merged
''',
        "test_interval.py": '''\
from bug_interval import merge_intervals

# Test 1: Basic overlap
assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]

# Test 2: Unsorted input
assert merge_intervals([[3,5],[1,4]]) == [[1,5]], "Failed on unsorted"

# Test 3: Contained interval
assert merge_intervals([[1,10],[2,5],[3,7]]) == [[1,10]], "Failed on contained"

# Test 4: Adjacent (touching)
assert merge_intervals([[1,2],[2,3]]) == [[1,3]], "Failed on adjacent"

# Test 5: No overlap
assert merge_intervals([[1,2],[4,5]]) == [[1,2],[4,5]], "Failed on no overlap"

# Test 6: Empty
assert merge_intervals([]) == []

# Test 7: Single
assert merge_intervals([[1,5]]) == [[1,5]]

print("All tests passed!")
''',

        # ── Bug 5: BFS shortest path ───────────────────────────────────
        "bug_graph.py": '''\
from collections import deque

def bfs_shortest_path(graph, start, end):
    """Find shortest path in unweighted graph. Returns list of nodes or None."""
    if start == end:
        return [start]

    visited = set()
    queue = deque([(start, [start])])

    while queue:
        node, path = queue.popleft()
        for neighbor in graph.get(node, []):
            if neighbor == end:
                return path + [neighbor]
            if neighbor not in visited:
                # Bug: should mark visited WHEN ENQUEUING, not when dequeuing
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None
''',
        "test_graph.py": '''\
from bug_graph import bfs_shortest_path

# Test 1: Simple path
graph1 = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
path = bfs_shortest_path(graph1, "A", "D")
assert path is not None and len(path) == 3, f"Expected length 3, got {path}"

# Test 2: No path
graph2 = {"A": ["B"], "B": [], "C": ["D"], "D": []}
assert bfs_shortest_path(graph2, "A", "D") is None, "Should return None"

# Test 3: Same start/end
assert bfs_shortest_path(graph1, "A", "A") == ["A"]

# Test 4: Cycle handling
graph3 = {"A": ["B"], "B": ["C", "A"], "C": ["A", "D"], "D": []}
path3 = bfs_shortest_path(graph3, "A", "D")
assert path3 == ["A", "B", "C", "D"], f"Expected A->B->C->D, got {path3}"

# Test 5: Multiple shortest paths (either is acceptable)
graph4 = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
path4 = bfs_shortest_path(graph4, "A", "D")
assert len(path4) == 3 and path4[0] == "A" and path4[-1] == "D"

# Test 6: Start node also needs to be marked visited
graph5 = {"A": ["B", "C"], "B": ["A", "D"], "C": ["A", "D"], "D": []}
path5 = bfs_shortest_path(graph5, "A", "D")
assert len(path5) == 3, f"Path too long, revisiting nodes? Got {path5}"

print("All tests passed!")
''',
    },
    num_samples=1,
    tags=["code-fix", "verifiable", "test-suite"],
)
