"""Diagram verification and contract checker.

Validates accessibility, safety, styling, and motion constraints.
"""

from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path
from typing import List, Optional


def _load_self_check_module():
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "skills" / "diagram-design" / "scripts" / "self_check.py",
        Path.cwd() / "skills" / "diagram-design" / "scripts" / "self_check.py",
        Path.home() / ".gemini" / "config" / "skills" / "diagram-design" / "scripts" / "self_check.py",
    ]
    for c in candidates:
        if c.exists():
            spec = importlib.util.spec_from_file_location("self_check", c)
            if spec and spec.loader:
                import sys
                module = importlib.util.module_from_spec(spec)
                sys.modules["self_check"] = module
                spec.loader.exec_module(module)
                return module
    raise FileNotFoundError("Could not find self_check.py in skill scripts.")


def check_file(path: Path) -> List[str]:
    """Verify an existing diagram HTML file."""
    module = _load_self_check_module()
    try:
        return module.verify(path)
    except Exception as exc:
        return [f"Verification exception: {exc}"]


def check_html_content(content: str) -> List[str]:
    """Verify diagram HTML content in memory."""
    module = _load_self_check_module()
    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        return module.verify(tmp_path)
    except Exception as exc:
        return [f"Verification exception: {exc}"]
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
