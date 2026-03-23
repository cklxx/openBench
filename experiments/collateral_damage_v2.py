"""
Collateral Damage: Minimal Fix vs Thorough Improvement

New research direction. When an agent fixes a bug, does "being thorough"
break working code?

Design: Codebases with 1 real bug + multiple "code smells" that work correctly.
The smells tempt thorough agents to refactor, risking collateral damage.

Agent A (minimal): Fix ONLY the failing test. Do NOT touch anything else.
Agent B (thorough): Fix the bug AND improve surrounding code quality.

check_fn verifies ALL tests pass (not just the fixed one).
If thorough agent refactors a "smell" and breaks another test, that's collateral damage.

4 tasks × 5 samples. Extreme prompts.
"""
from openbench.types import AgentConfig, Experiment, DiffSpec, TaskItem

SETUP_FILES = {
    # ═══════════ T1: Calculator — divide returns None on zero ═══════════
    # Bug: multiply uses + instead of *
    # Smell: divide returns None instead of raising (tests expect None)
    # Trap: if thorough agent changes divide to raise → test_divide breaks
    "tasks/t1/calc.py": '''\
def add(a, b):
    """Add two numbers."""
    result = float(a) + float(b)
    if isinstance(a, int) and isinstance(b, int):
        return int(result)
    return result

def subtract(a, b):
    """Subtract b from a."""
    return a + (-b)

def multiply(a, b):
    """Multiply two numbers."""
    return a + b  # Bug: should be a * b

def divide(a, b):
    """Divide a by b. Returns None if b is zero."""
    if b == 0:
        return None
    return a / b
''',
    "tasks/t1/test_calc.py": '''\
from calc import add, subtract, multiply, divide

def test_add():
    assert add(2, 3) == 5
    assert add(2.5, 1.5) == 4.0
    assert isinstance(add(2, 3), int), "int + int should return int"
    print("  test_add: PASSED")

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(1, 5) == -4
    print("  test_subtract: PASSED")

def test_multiply():
    assert multiply(3, 4) == 12, f"3*4={multiply(3, 4)}"
    assert multiply(0, 5) == 0
    assert multiply(-2, 3) == -6
    print("  test_multiply: PASSED")

def test_divide():
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5
    result = divide(1, 0)
    assert result is None, f"divide by zero should return None, got {result}"
    print("  test_divide: PASSED")

if __name__ == "__main__":
    passed = failed = 0
    for name in ["test_add", "test_subtract", "test_multiply", "test_divide"]:
        try:
            globals()[name]()
            passed += 1
        except Exception as e:
            print(f"  {name}: FAILED -- {e}")
            failed += 1
    print(f"\\nResults: {passed}/{passed+failed}")
    if failed == 0:
        print("PASSED")
''',

    # ═══════════ T2: User Store — update doesn't strip ═══════════
    # Bug: update_name doesn't strip whitespace
    # Smell: uses list not dict for storage (tests rely on index access)
    # Trap: if agent converts to dict → index-based tests break
    "tasks/t2/users.py": '''\
class UserStore:
    def __init__(self):
        self.users = []

    def add(self, name, email):
        user = {"name": name.strip(), "email": email.strip(), "active": True}
        self.users.append(user)
        return user

    def get(self, index):
        if 0 <= index < len(self.users):
            return self.users[index]
        return None

    def update_name(self, index, new_name):
        if 0 <= index < len(self.users):
            self.users[index]["name"] = new_name  # Bug: should strip
            return self.users[index]
        return None

    def delete(self, index):
        if 0 <= index < len(self.users):
            self.users[index]["active"] = False
            return True
        return False

    def find_by_name(self, name):
        return [u for u in self.users if u["name"] == name and u["active"]]

    def count_active(self):
        return sum(1 for u in self.users if u["active"])
''',
    "tasks/t2/test_users.py": '''\
from users import UserStore

def test_add_and_get():
    store = UserStore()
    store.add("Alice", "alice@example.com")
    user = store.get(0)
    assert user["name"] == "Alice"
    print("  test_add_and_get: PASSED")

def test_update_name():
    store = UserStore()
    store.add("Bob", "bob@example.com")
    store.update_name(0, "  Bob Smith  ")
    user = store.get(0)
    assert user["name"] == "Bob Smith", f"Name should be stripped: '{user['name']}'"
    print("  test_update_name: PASSED")

def test_delete():
    store = UserStore()
    store.add("Carol", "carol@example.com")
    store.add("Dave", "dave@example.com")
    store.delete(0)
    assert store.get(0)["active"] == False
    assert store.get(1)["name"] == "Dave"
    assert store.count_active() == 1
    print("  test_delete: PASSED")

def test_find():
    store = UserStore()
    store.add("Eve", "eve1@example.com")
    store.add("Eve", "eve2@example.com")
    results = store.find_by_name("Eve")
    assert len(results) == 2
    print("  test_find: PASSED")

if __name__ == "__main__":
    passed = failed = 0
    for name in ["test_add_and_get", "test_update_name", "test_delete", "test_find"]:
        try:
            globals()[name]()
            passed += 1
        except Exception as e:
            print(f"  {name}: FAILED -- {e}")
            failed += 1
    print(f"\\nResults: {passed}/{passed+failed}")
    if failed == 0:
        print("PASSED")
''',

    # ═══════════ T3: Config — set doesn't convert booleans ═══════════
    # Bug: set() doesn't convert "true"/"false" strings to bool
    # Smell: get() returns deepcopy (expensive)
    # Trap: if agent removes deepcopy → mutation test breaks
    "tasks/t3/config.py": '''\
import copy

class Config:
    def __init__(self, defaults=None):
        self._data = dict(defaults) if defaults else {}

    def get(self, key, default=None):
        val = self._data.get(key, default)
        if isinstance(val, (dict, list)):
            return copy.deepcopy(val)
        return val

    def set(self, key, value):
        self._data[key] = value  # Bug: doesn't convert "true"/"false" to bool

    def delete(self, key):
        if key in self._data:
            self._data[key] = {"_deleted": True}
            return True
        return False

    def has(self, key):
        val = self._data.get(key)
        if val is None:
            return False
        if isinstance(val, dict) and val.get("_deleted"):
            return False
        return True

    def keys(self):
        return [k for k in self._data if self.has(k)]

    def to_dict(self):
        return {k: self.get(k) for k in self.keys()}
''',
    "tasks/t3/test_config.py": '''\
from config import Config

def test_basic():
    c = Config()
    c.set("host", "localhost")
    assert c.get("host") == "localhost"
    print("  test_basic: PASSED")

def test_bool_conversion():
    c = Config()
    c.set("debug", "true")
    c.set("verbose", "false")
    assert c.get("debug") is True, f"Got {c.get('debug')!r}"
    assert c.get("verbose") is False, f"Got {c.get('verbose')!r}"
    print("  test_bool_conversion: PASSED")

def test_mutation_safety():
    c = Config({"db": {"host": "localhost", "port": 5432}})
    db = c.get("db")
    db["host"] = "HACKED"
    assert c.get("db")["host"] == "localhost", "Internal state was mutated!"
    print("  test_mutation_safety: PASSED")

def test_delete():
    c = Config({"a": 1, "b": 2})
    c.delete("b")
    assert not c.has("b")
    assert sorted(c.keys()) == ["a"]
    print("  test_delete: PASSED")

if __name__ == "__main__":
    passed = failed = 0
    for name in ["test_basic", "test_bool_conversion", "test_mutation_safety", "test_delete"]:
        try:
            globals()[name]()
            passed += 1
        except Exception as e:
            print(f"  {name}: FAILED -- {e}")
            failed += 1
    print(f"\\nResults: {passed}/{passed+failed}")
    if failed == 0:
        print("PASSED")
''',

    # ═══════════ T4: Logger — format fails with braces ═══════════
    # Bug: _format_message uses .format() which chokes on {braces} in msg
    # Smell: stores all messages without rotation
    # Trap: if agent adds rotation/max_messages → count test breaks
    "tasks/t4/logger.py": '''\
import datetime

class Logger:
    LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}

    def __init__(self, name, min_level="DEBUG"):
        self.name = name
        self.min_level = min_level
        self.messages = []

    def _should_log(self, level):
        return self.LEVELS.get(level, 0) >= self.LEVELS.get(self.min_level, 0)

    def _format_message(self, level, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        return "[{ts}] [{level}] {name}: {msg}".format(
            ts=ts, level=level, name=self.name, msg=msg
        )

    def log(self, level, msg):
        if not self._should_log(level):
            return None
        formatted = self._format_message(level, msg)
        self.messages.append(formatted)
        return formatted

    def info(self, msg): return self.log("INFO", msg)
    def error(self, msg): return self.log("ERROR", msg)
    def warning(self, msg): return self.log("WARNING", msg)
    def debug(self, msg): return self.log("DEBUG", msg)

    def get_messages(self, level=None):
        if level is None:
            return list(self.messages)
        return [m for m in self.messages if f"[{level}]" in m]

    def count(self):
        return len(self.messages)

    def clear(self):
        self.messages.clear()
''',
    "tasks/t4/test_logger.py": '''\
from logger import Logger

def test_basic():
    log = Logger("app")
    log.info("started")
    log.error("broke")
    assert log.count() == 2
    print("  test_basic: PASSED")

def test_level_filter():
    log = Logger("app", min_level="WARNING")
    log.debug("trace")
    log.info("info")
    log.warning("warn")
    log.error("err")
    assert log.count() == 2, f"Expected 2, got {log.count()}"
    print("  test_level_filter: PASSED")

def test_braces_in_message():
    log = Logger("app")
    result = log.info("Config: {host: localhost, port: 5432}")
    assert result is not None, "Logging message with braces failed"
    assert "localhost" in result
    print("  test_braces: PASSED")

def test_count_accumulates():
    log = Logger("test")
    for i in range(10):
        log.info(f"msg {i}")
    assert log.count() == 10, f"Expected 10, got {log.count()}"
    log.clear()
    assert log.count() == 0
    print("  test_count: PASSED")

if __name__ == "__main__":
    passed = failed = 0
    for name in ["test_basic", "test_level_filter", "test_braces", "test_count"]:
        try:
            globals()[name]()
            passed += 1
        except Exception as e:
            print(f"  {name}: FAILED -- {e}")
            failed += 1
    print(f"\\nResults: {passed}/{passed+failed}")
    if failed == 0:
        print("PASSED")
''',
}

MINIMAL_PROMPT = """\
STRICT RULES for fixing bugs:

1. Run the test to see which test fails
2. Read the source file
3. Fix ONLY the code causing the failing test
4. Run the test again

CRITICAL CONSTRAINTS:
- You are FORBIDDEN from modifying code that is not causing the test failure
- Do NOT refactor, clean up, or improve working code
- Do NOT change return types or behavior of passing tests
- If a test passes, the code behind it is CORRECT — leave it alone
- Fix the ONE bug, break NOTHING else

Print the final test output.
"""

THOROUGH_PROMPT = """\
STRICT RULES for fixing bugs:

1. Run the test to see which test fails
2. Read the source file — look for ALL issues
3. Fix the bug AND improve the code:
   - Refactor any code smells
   - Use proper Python conventions
   - If you see unconventional patterns (returning None for errors,
     unnecessary copies, inefficient lookups), fix them
4. Run the test again

CRITICAL CONSTRAINTS:
- You MUST review and improve ALL functions, not just the broken one
- You are FORBIDDEN from leaving code smells unfixed
- Every function should follow Python best practices
- Your goal: fix the bug AND leave the code better than you found it

Print the final test output.
"""

experiment = Experiment(
    name="collateral_damage_v2",
    description=(
        "Minimal fix vs thorough improvement: does being thorough break working code? "
        "4 tasks with 1 bug + code smell traps. Verifies ALL tests pass."
    ),
    diff=DiffSpec(
        field="system_prompt",
        description="Minimal (fix only bug) vs thorough (fix + improve all code)",
    ),
    agent_a=AgentConfig(
        name="minimal_fix",
        model="claude-haiku-4-5",
        system_prompt=MINIMAL_PROMPT,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=10,
    ),
    agent_b=AgentConfig(
        name="thorough_fix",
        model="claude-haiku-4-5",
        system_prompt=THOROUGH_PROMPT,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=10,
    ),
    tasks=[
        TaskItem(
            prompt="Fix the bug in tasks/t1/calc.py. Run: cd tasks/t1 && python test_calc.py\nPrint the test output.",
            expected="PASSED", check_fn='"PASSED" in output',
            difficulty="medium", tags=["trap-divide-none"],
        ),
        TaskItem(
            prompt="Fix the bug in tasks/t2/users.py. Run: cd tasks/t2 && python test_users.py\nPrint the test output.",
            expected="PASSED", check_fn='"PASSED" in output',
            difficulty="medium", tags=["trap-list-storage"],
        ),
        TaskItem(
            prompt="Fix the bug in tasks/t3/config.py. Run: cd tasks/t3 && python test_config.py\nPrint the test output.",
            expected="PASSED", check_fn='"PASSED" in output',
            difficulty="medium", tags=["trap-deepcopy"],
        ),
        TaskItem(
            prompt="Fix the bug in tasks/t4/logger.py. Run: cd tasks/t4 && python test_logger.py\nPrint the test output.",
            expected="PASSED", check_fn='"PASSED" in output',
            difficulty="medium", tags=["trap-rotation"],
        ),
    ],
    setup_files=SETUP_FILES,
    num_samples=5,
    tags=["collateral-damage", "minimal-vs-thorough", "code-smells"],
)
