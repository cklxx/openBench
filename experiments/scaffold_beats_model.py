"""
The Holy Grail: Can haiku + optimal scaffold beat sonnet + naive scaffold?

Based on all experiments so far, the best haiku optimizations are:
- Few-shot tool examples (+5%)
- Cost-normalized retry (pass@3)
- max_turns=20 (100% vs 67% at max_turns=5)

Combine them all into "optimized haiku" and compare against "naive sonnet".

Design:
- haiku_optimized: few-shot examples + good system prompt + max_turns=20
- sonnet_naive: no system prompt, max_turns=10 (what a casual user would do)
- sonnet_optimized: same optimizations as haiku (upper bound reference)

8 tasks spanning easy→very hard, n=5 per condition.
"""
from openbench.types import AgentConfig, TaskItem, TournamentConfig

OPTIMIZED_PROMPT = """\
You are a senior developer fixing bugs and implementing features.

WORKFLOW:
1. Read relevant files to understand context before making changes
2. Run tests FIRST to see current state
3. Make minimal, precise edits
4. Run tests AGAIN to verify your changes
5. If tests fail, read the error carefully and fix

## Example 1: Fixing a logic bug
Task: "Fix the bug in calculator.py"
1. Bash: python test_calc.py → see AssertionError on line 5
2. Read calculator.py → find the logic error in add()
3. Edit calculator.py → fix the specific line
4. Bash: python test_calc.py → all pass

## Example 2: Adding a feature
Task: "Add a delete method to UserStore"
1. Read user_store.py → understand existing API
2. Read test_user_store.py → see what's expected
3. Edit user_store.py → add delete() method following existing patterns
4. Bash: python test_user_store.py → verify

KEY: Read before edit. Test before and after. Minimal changes only.
"""

SETUP_FILES = {
    "tasks/t1/math_utils.py": '''\
def gcd(a, b):
    """Greatest common divisor using Euclidean algorithm."""
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    """Least common multiple."""
    return a * b // gcd(a, b)

def is_prime(n):
    """Check if n is prime."""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return True  # Bug: should return False
    return True  # Bug: should return True only if no divisor found (logic inverted)
''',
    "tasks/t1/test_math.py": '''\
from math_utils import gcd, lcm, is_prime
assert gcd(12, 8) == 4
assert lcm(4, 6) == 12
assert is_prime(7) == True
assert is_prime(4) == False
assert is_prime(1) == False
assert is_prime(2) == True
assert is_prime(97) == True
assert is_prime(100) == False
print("test_math: PASSED")
''',

    "tasks/t2/text_stats.py": '''\
def word_frequency(text):
    """Return dict of word -> count, case-insensitive."""
    words = text.lower().split()
    freq = {}
    for w in words:
        w = w.strip(".,!?;:'\"")
        freq[w] = freq.get(w, 0) + 1
    return freq

def top_n_words(text, n=5):
    """Return top N most frequent words as list of (word, count)."""
    freq = word_frequency(text)
    sorted_words = sorted(freq.items(), key=lambda x: x[1])  # Bug: should be reverse=True
    return sorted_words[:n]

def sentence_count(text):
    """Count sentences (split by . ! ?)."""
    import re
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])
''',
    "tasks/t2/test_text.py": '''\
from text_stats import word_frequency, top_n_words, sentence_count
freq = word_frequency("the cat sat on the mat")
assert freq["the"] == 2
top = top_n_words("the cat sat on the mat the", 2)
assert top[0][0] == "the" and top[0][1] == 3, f"Top word wrong: {top}"
assert sentence_count("Hello. World! How?") == 3
print("test_text: PASSED")
''',

    "tasks/t3/stack.py": '''\
class Stack:
    def __init__(self, max_size=None):
        self._items = []
        self._max_size = max_size

    def push(self, item):
        if self._max_size and len(self._items) >= self._max_size:
            raise OverflowError("Stack is full")
        self._items.append(item)

    def pop(self):
        return self._items.pop()  # Bug: no empty check

    def peek(self):
        return self._items[-1]  # Bug: no empty check

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)
''',
    "tasks/t3/test_stack.py": '''\
from stack import Stack
s = Stack()
assert s.is_empty()
s.push(1); s.push(2); s.push(3)
assert s.size() == 3
assert s.peek() == 3
assert s.pop() == 3
assert s.size() == 2
# Empty stack operations should raise IndexError
try:
    Stack().pop()
    assert False, "Should raise IndexError"
except IndexError:
    pass
try:
    Stack().peek()
    assert False, "Should raise IndexError"
except IndexError:
    pass
# Max size
ms = Stack(max_size=2)
ms.push(1); ms.push(2)
try:
    ms.push(3)
    assert False, "Should raise OverflowError"
except OverflowError:
    pass
print("test_stack: PASSED")
''',

    "tasks/t4/matrix.py": '''\
def multiply(a, b):
    """Multiply two matrices."""
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    if cols_a != rows_b:
        raise ValueError("Incompatible dimensions")
    result = [[0] * cols_b for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    return result

def transpose(m):
    """Transpose a matrix."""
    if not m:
        return []
    return [[m[j][i] for j in range(len(m))] for i in range(len(m[0]))]

def determinant(m):
    """Calculate determinant of a square matrix."""
    n = len(m)
    if n == 1:
        return m[0][0]
    if n == 2:
        return m[0][0] * m[1][1] - m[0][1] * m[1][0]
    det = 0
    for j in range(n):
        minor = [row[:j] + row[j+1:] for row in m[1:]]
        # Bug: cofactor sign alternation wrong
        det += m[0][j] * determinant(minor)  # Missing (-1)**j
    return det
''',
    "tasks/t4/test_matrix.py": '''\
from matrix import multiply, transpose, determinant
# Multiply
assert multiply([[1,2],[3,4]], [[5,6],[7,8]]) == [[19,22],[43,50]]
# Transpose
assert transpose([[1,2,3],[4,5,6]]) == [[1,4],[2,5],[3,6]]
# Determinant
assert determinant([[1]]) == 1
assert determinant([[1,2],[3,4]]) == -2
assert determinant([[1,0,0],[0,1,0],[0,0,1]]) == 1  # Identity
assert determinant([[2,1,1],[1,3,2],[1,0,0]]) == 1
print("test_matrix: PASSED")
''',

    "tasks/t5/scheduler.py": '''\
"""Job scheduler with priorities and dependencies."""
from collections import deque

class Job:
    def __init__(self, name, priority=0, deps=None):
        self.name = name
        self.priority = priority
        self.deps = deps or []
        self.status = "pending"

class Scheduler:
    def __init__(self):
        self.jobs = {}

    def add_job(self, job):
        self.jobs[job.name] = job

    def _topo_sort(self):
        """Topological sort respecting dependencies."""
        in_degree = {name: 0 for name in self.jobs}
        for job in self.jobs.values():
            for dep in job.deps:
                in_degree[job.name] = in_degree.get(job.name, 0) + 1

        queue = deque()
        for name, degree in in_degree.items():
            if degree == 0:
                queue.append(name)

        # Bug: doesn't sort by priority within same dependency level
        order = []
        while queue:
            name = queue.popleft()  # Should pick highest priority from queue
            order.append(name)
            for job in self.jobs.values():
                if name in job.deps:
                    in_degree[job.name] -= 1
                    if in_degree[job.name] == 0:
                        queue.append(job.name)
        return order

    def run(self):
        order = self._topo_sort()
        results = []
        for name in order:
            self.jobs[name].status = "done"
            results.append(name)
        return results
''',
    "tasks/t5/test_scheduler.py": '''\
from scheduler import Scheduler, Job
# Basic priority ordering (no deps)
s = Scheduler()
s.add_job(Job("low", priority=1))
s.add_job(Job("high", priority=3))
s.add_job(Job("mid", priority=2))
result = s.run()
assert result == ["high", "mid", "low"], f"Priority order wrong: {result}"

# Dependencies override priority
s2 = Scheduler()
s2.add_job(Job("B", priority=3, deps=["A"]))
s2.add_job(Job("A", priority=1))
result2 = s2.run()
assert result2.index("A") < result2.index("B"), f"Deps wrong: {result2}"

# Mixed deps + priority
s3 = Scheduler()
s3.add_job(Job("D", priority=1, deps=["B", "C"]))
s3.add_job(Job("C", priority=2, deps=["A"]))
s3.add_job(Job("B", priority=3, deps=["A"]))
s3.add_job(Job("A", priority=4))
result3 = s3.run()
assert result3[0] == "A"
assert result3[-1] == "D"
# B has higher priority than C, both depend on A
assert result3.index("B") < result3.index("C"), f"Priority tiebreak wrong: {result3}"
print("test_scheduler: PASSED")
''',

    "tasks/t6/cache.py": '''\
"""TTL cache with size limit and statistics."""
import time

class TTLCache:
    def __init__(self, max_size=100, default_ttl=60):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._store = {}  # key -> (value, expires_at)
        self._hits = 0
        self._misses = 0

    def get(self, key, current_time=None):
        now = current_time or time.time()
        if key in self._store:
            value, expires = self._store[key]
            if now < expires:
                self._hits += 1
                return value
            else:
                del self._store[key]
        self._misses += 1
        return None

    def set(self, key, value, ttl=None, current_time=None):
        now = current_time or time.time()
        # Bug: doesn't evict when at max_size
        self._store[key] = (value, now + (ttl or self.default_ttl))

    def delete(self, key):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

    def stats(self):
        total = self._hits + self._misses
        return {
            "size": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }
''',
    "tasks/t6/test_cache.py": '''\
from cache import TTLCache
c = TTLCache(max_size=3, default_ttl=10)
c.set("a", 1, current_time=100)
c.set("b", 2, current_time=100)
c.set("c", 3, current_time=100)
assert c.get("a", current_time=105) == 1
assert c.get("b", current_time=105) == 2
# At max_size, adding new should evict oldest
c.set("d", 4, current_time=106)
assert len(c._store) <= 3, f"Over max_size: {len(c._store)}"
# TTL expiry
assert c.get("a", current_time=115) is None  # expired
# Stats
s = c.stats()
assert s["hits"] >= 2
assert s["misses"] >= 1
assert 0 <= s["hit_rate"] <= 1
print("test_cache: PASSED")
''',

    "tasks/t7/json_query.py": '''\
"""Simple JSON query engine — supports dot notation and array indexing."""

def query(data, path):
    """Query nested JSON data with dot notation.
    Examples:
        query({"a": {"b": 1}}, "a.b") → 1
        query({"items": [1,2,3]}, "items[1]") → 2
        query({"a": 1}, "b") → None (missing key)
    """
    parts = _parse_path(path)
    current = data
    for part in parts:
        if isinstance(part, int):
            # Array index
            if not isinstance(current, list) or part >= len(current):
                return None
            current = current[part]
        elif isinstance(part, str):
            if not isinstance(current, dict):
                return None
            current = current.get(part)  # Bug: doesn't handle None vs missing key
            if current is None:
                return None  # Bug: can't distinguish null value from missing key
        else:
            return None
    return current

def _parse_path(path):
    """Parse 'a.b[0].c' into ['a', 'b', 0, 'c']."""
    parts = []
    current = ""
    for ch in path:
        if ch == '.':
            if current:
                parts.append(current)
                current = ""
        elif ch == '[':
            if current:
                parts.append(current)
                current = ""
        elif ch == ']':
            if current.isdigit():
                parts.append(int(current))
            current = ""
        else:
            current += ch
    if current:
        parts.append(current)
    return parts
''',
    "tasks/t7/test_json_query.py": '''\
from json_query import query
data = {
    "user": {"name": "Alice", "age": 30, "active": None},
    "items": [{"id": 1}, {"id": 2}, {"id": 3}],
    "count": 0,
}
assert query(data, "user.name") == "Alice"
assert query(data, "items[1].id") == 2
assert query(data, "count") == 0  # Falsy but exists
assert query(data, "missing") is None
# Bug trigger: None value vs missing key
assert query(data, "user.active") is None  # Value IS None (exists)
# This test distinguishes "key exists with None" from "key missing":
assert query(data, "user.nonexistent") is None  # Key missing
# Both return None — that's ambiguous but acceptable.
# The REAL bug: falsy values
assert query(data, "count") == 0, f"Falsy value lost: {query(data, 'count')}"
print("test_json_query: PASSED")
''',

    "tasks/t8/rate_limiter.py": '''\
"""Token bucket rate limiter."""
import time

class RateLimiter:
    def __init__(self, rate, burst, current_time=None):
        """
        rate: tokens per second
        burst: maximum tokens (bucket size)
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst  # Start full
        self.last_refill = current_time or time.time()

    def _refill(self, current_time=None):
        now = current_time or time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.burst, self.tokens + new_tokens)
        self.last_refill = now

    def allow(self, cost=1, current_time=None):
        """Return True if request is allowed, consuming `cost` tokens."""
        self._refill(current_time)
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def wait_time(self, cost=1, current_time=None):
        """Return seconds to wait before `cost` tokens are available."""
        self._refill(current_time)
        if self.tokens >= cost:
            return 0.0
        deficit = cost - self.tokens
        return deficit / self.rate  # Bug: doesn't account for burst cap
''',
    "tasks/t8/test_limiter.py": '''\
from rate_limiter import RateLimiter
# 10 tokens/sec, burst of 5
rl = RateLimiter(rate=10, burst=5, current_time=0)
# Should allow 5 requests immediately (burst)
for _ in range(5):
    assert rl.allow(current_time=0) == True
# 6th should fail
assert rl.allow(current_time=0) == False
# After 0.5 sec, 5 new tokens
assert rl.allow(current_time=0.5) == True
# Wait time calculation
rl2 = RateLimiter(rate=10, burst=5, current_time=0)
for _ in range(5):
    rl2.allow(current_time=0)
wt = rl2.wait_time(cost=3, current_time=0)
assert abs(wt - 0.3) < 0.01, f"Wait time wrong: {wt}"
# Large cost exceeding burst should return correct wait (even if impossible)
rl3 = RateLimiter(rate=10, burst=5, current_time=0)
for _ in range(5):
    rl3.allow(current_time=0)
wt2 = rl3.wait_time(cost=10, current_time=0)
# 10 tokens needed, 0 available, rate 10/sec = 1 sec wait
# BUT burst is only 5, so 10 tokens can NEVER be accumulated
# This should either return infinity or raise an error
assert wt2 > 100 or wt2 == float("inf"), f"Impossible cost should signal error: {wt2}"
print("test_limiter: PASSED")
''',
}

tournament = TournamentConfig(
    name="scaffold_beats_model",
    description=(
        "Holy grail: haiku+optimized scaffold vs sonnet+naive scaffold. "
        "8 tasks, n=5. Tests whether workflow > model capability."
    ),
    configs=[
        AgentConfig(
            name="haiku_optimized",
            model="claude-haiku-4-5",
            system_prompt=OPTIMIZED_PROMPT,
            allowed_tools=["Read", "Write", "Bash", "Glob", "Edit"],
            max_turns=20,
        ),
        AgentConfig(
            name="sonnet_naive",
            model="claude-sonnet-4-6",
            system_prompt=None,  # No guidance at all
            allowed_tools=["Read", "Write", "Bash", "Glob", "Edit"],
            max_turns=10,  # Lower budget — casual user setting
        ),
        AgentConfig(
            name="sonnet_optimized",
            model="claude-sonnet-4-6",
            system_prompt=OPTIMIZED_PROMPT,
            allowed_tools=["Read", "Write", "Bash", "Glob", "Edit"],
            max_turns=20,
        ),
    ],
    tasks=[
        TaskItem(prompt=f"Fix the bug in tasks/t{i}/. Run the test to verify.",
                 expected="PASSED", check_fn='"passed" in output.lower()',
                 difficulty=d, tags=[t])
        for i, d, t in [
            (1, "easy", "logic-inversion"),
            (2, "easy", "sort-direction"),
            (3, "medium", "missing-guard"),
            (4, "hard", "cofactor-sign"),
            (5, "hard", "priority-topo-sort"),
            (6, "medium", "eviction-missing"),
            (7, "medium", "falsy-value"),
            (8, "hard", "impossible-cost"),
        ]
    ],
    setup_files=SETUP_FILES,
    num_samples=5,
    tags=["scaffold-vs-model", "holy-grail", "workflow-optimization"],
)
