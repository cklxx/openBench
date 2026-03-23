"""
Strategy: Batch Fix vs Iterative Fix on Interacting Bugs

Previous batch vs iterative tests (error_recovery_v2) had tight turns.
This tests the REAL strategic question with generous turns:

When bugs INTERACT (fixing A changes whether B's test passes),
is it better to understand everything first (batch) or iterate?

Design: 4 tasks with INTERACTING bugs:
- Bug A and Bug B have compensating errors
- Fixing A alone changes which tests fail (because B was compensating)
- You need to fix BOTH to pass all tests

Batch agent: "Read all code, understand ALL bugs, fix all at once, then test"
Iterative agent: "Run tests, fix first failure, re-run, fix next, repeat"

max_turns=15 (generous for single-file tasks). 4 tasks × 5 samples.
"""
from openbench.types import AgentConfig, Experiment, DiffSpec, TaskItem

SETUP_FILES = {
    # ═══════════ T1: Normalize/Denormalize — compensating division bugs ═══════════
    # Bug A: normalize divides by max instead of (max - min) — correct when min=0
    # Bug B: denormalize multiplies by max instead of (max - min) — same error
    # When BOTH are wrong, roundtrip with min=0 accidentally works
    # Fixing only one breaks the roundtrip test
    "tasks/t1/transform.py": '''\
def normalize(values):
    """Normalize values to 0-1 range: (v - min) / (max - min)."""
    if not values:
        return []
    min_v = min(values)
    max_v = max(values)
    if max_v == min_v:
        return [0.0] * len(values)
    # Bug A: divides by max_v instead of (max_v - min_v)
    return [(v - min_v) / max_v for v in values]

def denormalize(normalized, original_min, original_max):
    """Convert normalized [0,1] values back to original range."""
    span = original_max  # Bug B: should be (original_max - original_min)
    return [v * span + original_min for v in normalized]

def scale_to_range(values, new_min, new_max):
    """Scale values to a new range [new_min, new_max]."""
    normed = normalize(values)
    return [v * (new_max - new_min) + new_min for v in normed]
''',
    "tasks/t1/test_transform.py": '''\
from transform import normalize, denormalize, scale_to_range

def test_normalize_basic():
    result = normalize([0, 50, 100])
    assert result == [0.0, 0.5, 1.0], f"Got {result}"
    print("  normalize_basic: PASSED")

def test_normalize_shifted():
    """Normalize with non-zero minimum."""
    result = normalize([10, 30, 50])
    # (10-10)/(50-10)=0, (30-10)/40=0.5, (50-10)/40=1.0
    assert result == [0.0, 0.5, 1.0], f"Got {result}"
    print("  normalize_shifted: PASSED")

def test_roundtrip():
    """Normalize then denormalize should recover original values."""
    original = [20, 40, 60, 80]
    normed = normalize(original)
    recovered = denormalize(normed, 20, 80)
    for o, r in zip(original, recovered):
        assert abs(o - r) < 0.01, f"Roundtrip failed: {original} -> {normed} -> {recovered}"
    print("  roundtrip: PASSED")

def test_scale_to_range():
    result = scale_to_range([0, 50, 100], 0, 10)
    assert result == [0.0, 5.0, 10.0], f"Got {result}"
    print("  scale_to_range: PASSED")

if __name__ == "__main__":
    passed = failed = 0
    for name in ["test_normalize_basic", "test_normalize_shifted",
                  "test_roundtrip", "test_scale_to_range"]:
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

    # ═══════════ T2: Temperature converter — F/C offset bugs ═══════════
    # Bug A: celsius_to_fahrenheit uses + 30 instead of + 32
    # Bug B: fahrenheit_to_celsius uses - 30 instead of - 32
    # When BOTH are wrong by the same offset, roundtrip approximately works
    # But direct conversion tests fail
    "tasks/t2/temperature.py": '''\
def celsius_to_fahrenheit(c):
    """Convert Celsius to Fahrenheit: F = C * 9/5 + 32."""
    return c * 9 / 5 + 30  # Bug A: should be + 32

def fahrenheit_to_celsius(f):
    """Convert Fahrenheit to Celsius: C = (F - 32) * 5/9."""
    return (f - 30) * 5 / 9  # Bug B: should be - 32

def convert_batch(values, from_unit, to_unit):
    """Convert a batch of temperatures between units."""
    if from_unit == to_unit:
        return list(values)
    if from_unit == "C" and to_unit == "F":
        return [celsius_to_fahrenheit(v) for v in values]
    if from_unit == "F" and to_unit == "C":
        return [fahrenheit_to_celsius(v) for v in values]
    raise ValueError(f"Unknown conversion: {from_unit} -> {to_unit}")

def find_equal_point():
    """Find the temperature where Celsius == Fahrenheit (should be -40)."""
    # C = C * 9/5 + 32 → C - 9C/5 = 32 → -4C/5 = 32 → C = -40
    # With bug: C = C * 9/5 + 30 → -4C/5 = 30 → C = -37.5
    c = 0
    for _ in range(1000):
        f = celsius_to_fahrenheit(c)
        if abs(f - c) < 0.01:
            return c
        c = c - (f - c) * 0.5  # Newton-like iteration
    return c
''',
    "tasks/t2/test_temperature.py": '''\
from temperature import celsius_to_fahrenheit, fahrenheit_to_celsius, convert_batch, find_equal_point

def test_boiling_point():
    """100°C = 212°F."""
    result = celsius_to_fahrenheit(100)
    assert result == 212, f"100°C should be 212°F, got {result}"
    print("  boiling_point: PASSED")

def test_freezing_point():
    """0°C = 32°F."""
    result = celsius_to_fahrenheit(0)
    assert result == 32, f"0°C should be 32°F, got {result}"
    print("  freezing_point: PASSED")

def test_reverse_conversion():
    """212°F = 100°C."""
    result = fahrenheit_to_celsius(212)
    assert abs(result - 100) < 0.01, f"212°F should be 100°C, got {result}"
    print("  reverse_conversion: PASSED")

def test_roundtrip():
    """C -> F -> C should recover original."""
    for c in [0, 37, 100, -40]:
        f = celsius_to_fahrenheit(c)
        back = fahrenheit_to_celsius(f)
        assert abs(back - c) < 0.01, f"Roundtrip failed for {c}°C: {c} -> {f} -> {back}"
    print("  roundtrip: PASSED")

def test_equal_point():
    """Celsius == Fahrenheit at -40."""
    eq = find_equal_point()
    assert abs(eq - (-40)) < 0.1, f"Equal point should be -40, got {eq}"
    print("  equal_point: PASSED")

if __name__ == "__main__":
    passed = failed = 0
    for name in ["test_boiling_point", "test_freezing_point",
                  "test_reverse_conversion", "test_roundtrip", "test_equal_point"]:
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

    # ═══════════ T3: Encoding/Decoding with bit shift errors ═══════════
    # Bug A: encode shifts left by 3 instead of 2
    # Bug B: decode shifts right by 3 instead of 2
    # Roundtrip works (3 cancels 3), but encoded values are wrong
    "tasks/t3/codec.py": '''\
def encode(data):
    """Simple encoding: shift each byte left by 2 and XOR with 0xAA."""
    result = []
    for b in data:
        shifted = (b << 3) & 0xFF  # Bug A: should be << 2
        result.append(shifted ^ 0xAA)
    return bytes(result)

def decode(encoded):
    """Reverse the encoding."""
    result = []
    for b in encoded:
        unxored = b ^ 0xAA
        # Bug B: should be >> 2 to match encode's << 2
        shifted = (unxored >> 3) & 0xFF
        result.append(shifted)
    return bytes(result)

def encode_string(text):
    """Encode a UTF-8 string."""
    return encode(text.encode("utf-8"))

def decode_string(encoded):
    """Decode back to string."""
    return decode(encoded).decode("utf-8", errors="replace")
''',
    "tasks/t3/test_codec.py": '''\
from codec import encode, decode, encode_string, decode_string

def test_encode_known():
    """Encoding byte 65 (A): 65 << 2 = 260 & 0xFF = 4, 4 ^ 0xAA = 0xAE."""
    result = encode(b"A")
    expected = bytes([0x04 ^ 0xAA])  # (65 << 2) & 0xFF = 4, 4 ^ 0xAA = 0xAE
    assert result == expected, f"encode(b'A') = {result.hex()}, expected {expected.hex()}"
    print("  encode_known: PASSED")

def test_roundtrip():
    """Encode then decode should recover original bytes."""
    original = b"Hello, World!"
    encoded = encode(original)
    decoded = decode(encoded)
    assert decoded == original, f"Roundtrip failed: {original} -> {encoded.hex()} -> {decoded}"
    print("  roundtrip: PASSED")

def test_string_roundtrip():
    original = "Testing 123!"
    encoded = encode_string(original)
    decoded = decode_string(encoded)
    assert decoded == original, f"String roundtrip: '{original}' -> '{decoded}'"
    print("  string_roundtrip: PASSED")

def test_all_bytes():
    """All byte values 0-255 should survive roundtrip."""
    original = bytes(range(256))
    decoded = decode(encode(original))
    assert decoded == original, "Not all bytes survived roundtrip"
    print("  all_bytes: PASSED")

if __name__ == "__main__":
    passed = failed = 0
    for name in ["test_encode_known", "test_roundtrip",
                  "test_string_roundtrip", "test_all_bytes"]:
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

    # ═══════════ T4: Statistics with accumulator errors ═══════════
    # Bug A: variance uses n instead of n-1 (population vs sample variance)
    # Bug B: std_dev takes sqrt of the wrong variance formula
    # Fixing both: use n-1 in variance, sqrt of that for std_dev
    # Fixing only variance: std_dev still wrong (uses its own inline formula)
    "tasks/t4/stats.py": '''\
class RunningStats:
    """Online statistics calculator (Welford's algorithm variant)."""

    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self._m2 = 0.0  # sum of squared differences from mean

    def add(self, value):
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        delta2 = value - self.mean
        self._m2 += delta * delta2

    def variance(self):
        """Sample variance (Bessel's correction: divide by n-1)."""
        if self.n < 2:
            return 0.0
        # Bug A: divides by n instead of (n - 1) — population variance, not sample
        return self._m2 / self.n

    def std_dev(self):
        """Sample standard deviation."""
        if self.n < 2:
            return 0.0
        # Bug B: recalculates instead of using self.variance()
        # ALSO divides by n instead of (n - 1)
        import math
        return math.sqrt(self._m2 / self.n)

    def summary(self):
        return {
            "n": self.n,
            "mean": round(self.mean, 4),
            "variance": round(self.variance(), 4),
            "std_dev": round(self.std_dev(), 4),
        }
''',
    "tasks/t4/test_stats.py": '''\
import math
from stats import RunningStats

def test_mean():
    s = RunningStats()
    for v in [2, 4, 6, 8, 10]:
        s.add(v)
    assert s.mean == 6.0, f"Mean of [2,4,6,8,10] should be 6.0, got {s.mean}"
    print("  mean: PASSED")

def test_variance():
    """Sample variance of [2,4,6,8,10] = 10.0 (with Bessel correction n-1=4)."""
    s = RunningStats()
    for v in [2, 4, 6, 8, 10]:
        s.add(v)
    expected = 10.0  # sum((v-6)^2)/(5-1) = 40/4 = 10.0
    result = s.variance()
    assert abs(result - expected) < 0.01, \\
        f"Sample variance should be {expected}, got {result}"
    print("  variance: PASSED")

def test_std_dev():
    """Sample std dev should be sqrt(sample variance)."""
    s = RunningStats()
    for v in [2, 4, 6, 8, 10]:
        s.add(v)
    expected_var = 10.0
    expected_std = math.sqrt(expected_var)  # ~3.1623
    result = s.std_dev()
    assert abs(result - expected_std) < 0.01, \\
        f"Std dev should be {expected_std:.4f}, got {result}"
    # Also verify consistency: std_dev should equal sqrt(variance)
    assert abs(result - math.sqrt(s.variance())) < 0.001, \\
        f"std_dev ({result}) != sqrt(variance) ({math.sqrt(s.variance())})"
    print("  std_dev: PASSED")

def test_summary():
    s = RunningStats()
    for v in [10, 20, 30]:
        s.add(v)
    summary = s.summary()
    assert summary["n"] == 3
    assert summary["mean"] == 20.0
    # Sample variance of [10,20,30]: sum((v-20)^2)/(3-1) = 200/2 = 100
    assert abs(summary["variance"] - 100.0) < 0.1, f"Variance: {summary['variance']}"
    assert abs(summary["std_dev"] - 10.0) < 0.1, f"Std dev: {summary['std_dev']}"
    print("  summary: PASSED")

if __name__ == "__main__":
    passed = failed = 0
    for name in ["test_mean", "test_variance", "test_std_dev", "test_summary"]:
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

BATCH_PROMPT = """\
You are debugging Python code with interacting bugs.

IMPORTANT: In these tasks, bugs may COMPENSATE each other — fixing one bug
alone may cause a different test to fail. You must understand ALL bugs
before making ANY changes.

Strategy:
1. Read the source file completely
2. Read the test file to understand expected behavior
3. Analyze ALL bugs and how they interact
4. Fix ALL bugs in a single editing pass
5. Run tests to verify

Do NOT run tests before you've read and understood all the code.
Do NOT fix bugs one at a time — fix them all together.

Print the final test output.
"""

ITERATIVE_PROMPT = """\
You are debugging Python code.

Strategy:
1. Run the tests to see what fails
2. Fix the first failure you see
3. Run the tests again
4. If anything still fails, fix it
5. Repeat until all tests pass

Work incrementally — fix one thing at a time and verify after each fix.

Print the final test output.
"""

TASKS = [
    TaskItem(
        prompt="Fix all bugs in tasks/t1/transform.py. Run: cd tasks/t1 && python test_transform.py\nPrint the test output.",
        expected="PASSED", check_fn='"PASSED" in output or "pass" in output.lower()',
        difficulty="hard", tags=["interacting-bugs", "normalize"],
    ),
    TaskItem(
        prompt="Fix all bugs in tasks/t2/temperature.py. Run: cd tasks/t2 && python test_temperature.py\nPrint the test output.",
        expected="PASSED", check_fn='"PASSED" in output or "pass" in output.lower()',
        difficulty="hard", tags=["interacting-bugs", "temperature"],
    ),
    TaskItem(
        prompt="Fix all bugs in tasks/t3/codec.py. Run: cd tasks/t3 && python test_codec.py\nPrint the test output.",
        expected="PASSED", check_fn='"PASSED" in output or "pass" in output.lower()',
        difficulty="hard", tags=["interacting-bugs", "codec"],
    ),
    TaskItem(
        prompt="Fix all bugs in tasks/t4/stats.py. Run: cd tasks/t4 && python test_stats.py\nPrint the test output.",
        expected="PASSED", check_fn='"PASSED" in output or "pass" in output.lower()',
        difficulty="hard", tags=["interacting-bugs", "statistics"],
    ),
]

experiment = Experiment(
    name="strategy_batch_vs_iterative",
    description=(
        "Batch fix (understand all, fix all at once) vs iterative (fix one, re-test, repeat) "
        "on INTERACTING bugs where fixing A changes B's behavior. "
        "max_turns=15, 4 tasks × 5 samples."
    ),
    diff=DiffSpec(
        field="system_prompt",
        description="Batch (read-all, fix-all-at-once) vs iterative (fix-one, re-test, repeat)",
    ),
    agent_a=AgentConfig(
        name="batch",
        model="claude-haiku-4-5",
        system_prompt=BATCH_PROMPT,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=15,
    ),
    agent_b=AgentConfig(
        name="iterative",
        model="claude-haiku-4-5",
        system_prompt=ITERATIVE_PROMPT,
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=15,
    ),
    tasks=TASKS,
    setup_files=SETUP_FILES,
    num_samples=5,
    tags=["strategy", "batch-vs-iterative", "interacting-bugs", "generous-turns"],
)
