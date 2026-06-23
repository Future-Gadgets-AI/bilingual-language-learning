#!/usr/bin/env python3
"""Regression test: the backend gate must STOP when the local (ollama) path is
selected but unreachable — it must never silently fall through to the paid
`claude` backend.

`test_backend_default.py` locks the default *values*; this locks the gate
*behavior*. A future refactor that drops the reachability pre-flight, or routes
an unreachable-ollama run to claude, fails here — which is the exact regression
class of the original bug.

Run: python tests/test_backend_gate.py   (exits non-zero on any failure)
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bll import bootstrap, cli, gloss

fails = []


def check(name, got, want):
    if got != want:
        fails.append(f"{name}: got {got!r}, want {want!r}")


# Simulate "ollama is not running", and trap any call into the aligner so we can
# prove the run stopped at the gate before reaching either backend.
bootstrap.reachable = lambda *a, **k: False
align_calls = []
gloss.gloss_and_align = lambda *a, **k: align_calls.append(k.get("backend", "?")) or {}

JA = ("1\n00:00:01,000 --> 00:00:03,000\n世界を変える約束だ。\n\n"
      "2\n00:00:04,000 --> 00:00:06,000\nその約束は世界の希望だ。\n")
EN = ("1\n00:00:01,000 --> 00:00:03,000\nA promise to change the world.\n\n"
      "2\n00:00:04,000 --> 00:00:06,000\nThat promise is the world's hope.\n")

with tempfile.TemporaryDirectory() as d:
    ja, en = os.path.join(d, "ep.ja.srt"), os.path.join(d, "ep.en.srt")
    with open(ja, "w") as f:
        f.write(JA)
    with open(en, "w") as f:
        f.write(EN)
    # No --backend → defaults to ollama; ollama is "unreachable" (patched above).
    rc = cli.main(["--db", os.path.join(d, "t.db"), "process", ja, en,
                   "-o", os.path.join(d, "o.ass"), "--no-dict", "--min-count", "1"])

check("no-backend run stops (exit 1) when ollama is unreachable", rc, 1)
check("aligner never invoked on the default path", align_calls, [])

if fails:
    print("FAIL:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("PASS: backend gate stops on unreachable ollama; never falls through to claude")
