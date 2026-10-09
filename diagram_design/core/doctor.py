"""System diagnostic and readiness doctor for Diagram Design."""

from __future__ import annotations
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List
from diagram_design.core.templates import find_assets_dir
from diagram_design.core.types import DIAGRAM_TYPES


@dataclass
class DiagnosticCheck:
    name: str
    status: str  # "OK", "WARN", "FAIL"
    message: str
    recommendation: str = ""


def run_doctor() -> List[DiagnosticCheck]:
    """Run all diagnostic checks and return report."""
    results: List[DiagnosticCheck] = []

    # 1. Python version check
    py_major, py_minor = sys.version_info.major, sys.version_info.minor
    if py_major == 3 and py_minor >= 9:
        results.append(
            DiagnosticCheck("Python Version", "OK", f"Python {py_major}.{py_minor}.{sys.version_info.micro}")
        )
    else:
        results.append(
            DiagnosticCheck(
                "Python Version",
                "FAIL",
                f"Python {py_major}.{py_minor} (requires Python 3.9+)",
                "Upgrade Python to 3.9 or newer.",
            )
        )

    # 2. Assets & Templates check
    try:
        assets_dir = find_assets_dir()
        template_files = list(assets_dir.glob("template*.html"))
        example_files = list(assets_dir.glob("example*.html"))
        results.append(
            DiagnosticCheck(
                "Assets & Templates",
                "OK",
                f"Found {len(template_files)} templates and {len(example_files)} examples at {assets_dir}",
            )
        )
    except Exception as exc:
        results.append(
            DiagnosticCheck(
                "Assets & Templates",
                "FAIL",
                f"Missing assets directory: {exc}",
                "Ensure skills/diagram-design/assets exists.",
            )
        )

    # 3. Type Catalog Check
    types_count = len(DIAGRAM_TYPES)
    if types_count >= 44:
        results.append(
            DiagnosticCheck("Diagram Types", "OK", f"Registered all {types_count} canonical diagram types")
        )
    else:
        results.append(
            DiagnosticCheck("Diagram Types", "WARN", f"Registered {types_count} types (expected 44)")
        )

    # 4. Playwright & Chromium check (for PNG export)
    try:
        import playwright
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            chromium_path = p.chromium.executable_path
            if chromium_path and Path(chromium_path).exists():
                results.append(
                    DiagnosticCheck(
                        "PNG Rasterizer (Playwright Chromium)",
                        "OK",
                        f"Chromium available: {Path(chromium_path).name}",
                    )
                )
            else:
                results.append(
                    DiagnosticCheck(
                        "PNG Rasterizer (Playwright Chromium)",
                        "WARN",
                        "Chromium executable not located",
                        "Run: playwright install chromium",
                    )
                )
    except ImportError:
        results.append(
            DiagnosticCheck(
                "PNG Rasterizer (Playwright)",
                "WARN",
                "Playwright python package not installed",
                "Install with: pip install playwright && playwright install chromium",
            )
        )
    except Exception as exc:
        results.append(
            DiagnosticCheck(
                "PNG Rasterizer",
                "WARN",
                f"Playwright check error: {exc}",
                "Check Playwright installation.",
            )
        )

    # 5. Antigravity Global Skill
    global_skill = Path.home() / ".gemini" / "config" / "skills" / "diagram-design" / "SKILL.md"
    if global_skill.exists():
        results.append(
            DiagnosticCheck(
                "Antigravity Global Skill",
                "OK",
                f"Installed in global config ({global_skill.parent})",
            )
        )
    else:
        results.append(
            DiagnosticCheck(
                "Antigravity Global Skill",
                "WARN",
                "Not installed in ~/.gemini/config/skills/diagram-design",
                "Run: diagram install --global",
            )
        )

    # 6. Antigravity Workspace Skill
    workspace_skill = Path.cwd() / ".agents" / "skills" / "diagram-design" / "SKILL.md"
    if workspace_skill.exists():
        results.append(
            DiagnosticCheck(
                "Antigravity Workspace Skill",
                "OK",
                f"Installed in workspace (.agents/skills/diagram-design)",
            )
        )
    else:
        results.append(
            DiagnosticCheck(
                "Antigravity Workspace Skill",
                "WARN",
                "Not present in current workspace .agents/skills/",
                "Run: diagram install --workspace",
            )
        )

    return results
