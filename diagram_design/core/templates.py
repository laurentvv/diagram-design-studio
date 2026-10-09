"""Template engine and diagram scaffolding for Diagram Design."""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Optional, Tuple
from diagram_design.core.types import get_type, DIAGRAM_TYPES


def find_assets_dir() -> Path:
    """Locate the assets directory across possible install locations."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "skills" / "diagram-design" / "assets",
        Path.cwd() / "skills" / "diagram-design" / "assets",
        Path.home() / ".gemini" / "config" / "skills" / "diagram-design" / "assets",
    ]
    for c in candidates:
        if c.exists() and (c / "template.html").exists():
            return c
    raise FileNotFoundError("Could not find skills/diagram-design/assets directory.")


def get_template(theme: str = "light") -> str:
    """Load a base template file (light, dark, full, motion, terminal)."""
    assets = find_assets_dir()
    theme = theme.lower().strip()
    if theme == "dark":
        filename = "template-dark.html"
    elif theme == "full":
        filename = "template-full.html"
    elif theme == "motion":
        filename = "template-motion.html"
    elif theme == "terminal":
        filename = "template-terminal.html"
    else:
        filename = "template.html"

    path = assets / filename
    if not path.exists():
        path = assets / "template.html"
    return path.read_text(encoding="utf-8")


def find_example_file(type_id: str, variant: str = "light") -> Optional[Path]:
    """Find the best matching example file for a given type and variant."""
    assets = find_assets_dir()
    dtype = get_type(type_id)
    stem = dtype.example_stem if dtype and dtype.example_stem else f"example-{type_id}"

    variant = variant.lower().strip()
    suffix = ""
    if variant in ("dark", "-dark"):
        suffix = "-dark"
    elif variant in ("full", "-full"):
        suffix = "-full"
    elif variant in ("motion", "-animated", "animated"):
        suffix = "-animated"
    elif variant in ("terminal", "-terminal"):
        suffix = "-terminal"

    target_name = f"{stem}{suffix}.html"
    candidate = assets / target_name
    if candidate.exists():
        return candidate

    # Fallback to plain stem if variant not found
    fallback = assets / f"{stem}.html"
    if fallback.exists():
        return fallback

    return None


def scaffold_diagram(
    type_id: str,
    title: str = "System Architecture",
    description: str = "Architectural overview of system components and connections",
    theme: str = "light",
    use_canonical_body: bool = True,
) -> str:
    """Scaffold a complete, self-contained diagram HTML."""
    dtype = get_type(type_id)
    type_name = dtype.name if dtype else type_id.capitalize()
    view_box = dtype.view_box if dtype else "0 0 960 600"
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", title.lower()).strip("-") or "diagram"
    if slug[0].isdigit():
        slug = f"d-{slug}"

    if use_canonical_body:
        example_path = find_example_file(type_id, variant=theme)
        if example_path and example_path.exists():
            content = example_path.read_text(encoding="utf-8")
            # Replace title, desc, eyebrow
            content = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", content)
            content = re.sub(
                r'<p class="eyebrow">.*?</p>',
                f'<p class="eyebrow">{type_name} · Diagram Design</p>',
                content,
            )
            content = re.sub(
                r'<h1>.*?</h1>',
                f'<h1>{title}</h1>',
                content,
            )
            return content

    # Otherwise build from base template
    template = get_template(theme)
    content = template.replace("[Type]", type_name)
    content = content.replace("[Diagram title]", title)
    content = content.replace("[One sentence describing what the diagram shows]", description)
    content = content.replace("[diagram-slug]", slug)
    content = content.replace('viewBox="0 0 960 600"', f'viewBox="{view_box}"')

    return content
