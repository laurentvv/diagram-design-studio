"""Importer and extractor for external diagram formats (Mermaid, Draw.io, Excalidraw)."""

from __future__ import annotations
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _load_script_module(script_name: str):
    module_key = script_name.replace(".py", "")
    if module_key in sys.modules:
        return sys.modules[module_key]

    candidates = [
        Path(__file__).resolve().parent.parent.parent / "skills" / "diagram-design" / "scripts" / script_name,
        Path.cwd() / "skills" / "diagram-design" / "scripts" / script_name,
        Path.home() / ".gemini" / "config" / "skills" / "diagram-design" / "scripts" / script_name,
    ]
    for c in candidates:
        if c.exists():
            spec = importlib.util.spec_from_file_location(module_key, c)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_key] = module
                spec.loader.exec_module(module)
                return module
    raise FileNotFoundError(f"Could not find {script_name} in skill scripts.")


def import_diagram(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Import and parse a diagram file to (ir_dict, digest_markdown)."""
    path = Path(file_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Diagram source not found: {path}")

    ext = path.suffix.lower()
    if ext in (".mmd", ".mermaid", ".md"):
        m = _load_script_module("mermaid_extract.py")
        blocks = m.load_blocks(path)
        selected = [m.parse_block(b) for b in m.select_blocks(blocks, "all")]
        json_str = m.to_json(path, blocks, selected)
        digest_str = m.digest(path, blocks, selected, 40)
        return json.loads(json_str), digest_str

    elif ext in (".drawio", ".xml"):
        m = _load_script_module("drawio_extract.py")
        pages, raw_xml = m.load_mxfile(path)
        selected = [m.parse_page(p) for p in m.select_pages(pages, "all")]
        json_str = m.to_json(path, pages, selected)
        digest_str = m.digest(path, pages, selected, 40)
        return json.loads(json_str), digest_str

    elif ext in (".excalidraw", ".json"):
        m = _load_script_module("excalidraw_extract.py")
        scenes, raw_json = m.load_scene_data(path)
        selected = [m.parse_scene(s) for s in scenes]
        json_str = m.to_json(path, scenes, selected)
        scene = selected[0] if selected else None
        digest_str = m.digest(path, scene, 40) if scene else ""
        return json.loads(json_str), digest_str

    else:
        raise ValueError(f"Unsupported format {ext}. Supported: .mmd, .drawio, .excalidraw")


def import_mermaid_code(mermaid_text: str) -> Tuple[Dict[str, Any], str]:
    """Parse raw Mermaid code string to (ir_dict, digest_markdown)."""
    with tempfile.NamedTemporaryFile("w", suffix=".mmd", encoding="utf-8", delete=False) as tmp:
        tmp.write(mermaid_text)
        tmp_path = Path(tmp.name)
    try:
        return import_diagram(tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
