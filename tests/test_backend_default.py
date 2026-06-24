#!/usr/bin/env python3
"""Regression test: the alignment backend must never silently default to the
paid `claude` path.

`bll process` with no `--backend` used to default to `claude`, which shells out
to the Claude CLI and spends the user's tokens with no warning. Both the CLI
argument and the `gloss_and_align()` signature now default to the local, no-cost
`ollama` path; `claude` is an explicit, disclaimed opt-in (see the backend gate
in `cli.cmd_process`).

Run: python tests/test_backend_default.py   (exits non-zero on any failure)
"""
import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bll import cli, gloss

fails = []


def check(name, got, want):
    if got != want:
        fails.append(f"{name}: got {got!r}, want {want!r}")


# 1. The CLI `process` command must default --backend to ollama. This is the
#    active bug: it defaulted to claude, so a bare `bll process` spent tokens.
#    Patch the dispatch target (bound via set_defaults when main() builds the
#    parser) to capture the resolved args without running a real process.
captured = {}


def _fake_process(args):
    captured["backend"] = args.backend
    return 0


cli.cmd_process = _fake_process
cli.main(["process", "a.ja.srt", "b.en.srt"])
check("cli --backend default", captured.get("backend"), "ollama")

# 2. The library entry point must not silently default to claude either —
#    defense in depth for any caller that omits the backend.
sig = inspect.signature(gloss.gloss_and_align)
check("gloss_and_align backend default",
      sig.parameters["backend"].default, "ollama")

if fails:
    print("FAIL:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("PASS: backend never silently defaults to the paid claude path "
      "(cli + gloss_and_align both default to ollama)")
