#!/usr/bin/env python3
"""Run all 5 stealth injection variants as separate experiments."""
import importlib.util
import sys

from openbench.runner import ExperimentRunner
from openbench.storage import ResultStore
from openbench.compare import compare

spec = importlib.util.spec_from_file_location("inj", "experiments/injection_stealth.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

store = ResultStore()
runner = ExperimentRunner(store=store)

variants = [
    ("todo", mod.exp_todo),
    ("docstring", mod.exp_docstring),
    ("error_msg", mod.exp_error),
    ("migration", mod.exp_migration),
    ("assert", mod.exp_assert),
]

for name, exp in variants:
    print(f"\n{'='*60}")
    print(f"Running injection variant: {name}")
    print(f"{'='*60}")
    result = runner.run(exp)
    store.save_result(result)
    compare(result)
    print(f"Done: {name} → {result.run_id}")
