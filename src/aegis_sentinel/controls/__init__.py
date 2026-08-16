"""Deterministic control test functions — the verdict path.

Every module here is a pure function from a captured API response to a
verdict. No network, no AI-client import, anywhere in this package or its
callers: tests/test_verdict_path_purity.py enforces it at the AST level.
"""
