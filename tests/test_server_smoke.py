"""Smoke tests that import the server module without starting network listeners."""

from __future__ import annotations

import importlib.util
import pathlib
import sys


def test_server_module_imports():
    spec = importlib.util.spec_from_file_location(
        "server", str(pathlib.Path("server.py").resolve())
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["server_test_tmp"] = mod
    # Do not execute the module (it would start asyncio Future),
    # just check syntax via compile
    source = pathlib.Path("server.py").read_text(encoding="utf-8")
    compile(source, "server.py", "exec")


def test_desktop_client_syntax():
    import pathlib

    source = pathlib.Path("desktop_client.py").read_text(encoding="utf-8")
    compile(source, "desktop_client.py", "exec")
