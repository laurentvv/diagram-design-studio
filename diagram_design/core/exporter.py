"""Diagram exporter for SVG and PNG formats."""

from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Optional, Tuple


def _load_export_svg_module():
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "skills" / "diagram-design" / "scripts" / "export_svg.py",
        Path.cwd() / "skills" / "diagram-design" / "scripts" / "export_svg.py",
        Path.home() / ".gemini" / "config" / "skills" / "diagram-design" / "scripts" / "export_svg.py",
    ]
    for c in candidates:
        if c.exists():
            spec = importlib.util.spec_from_file_location("export_svg", c)
            if spec and spec.loader:
                import sys
                module = importlib.util.module_from_spec(spec)
                sys.modules["export_svg"] = module
                spec.loader.exec_module(module)
                return module
    raise FileNotFoundError("Could not find export_svg.py in skill scripts.")


def export_svg(source_html: Path, output_svg: Optional[Path] = None) -> Path:
    """Export a diagram HTML file to standalone, inline-safe SVG."""
    source_html = Path(source_html).resolve()
    if not source_html.is_file():
        raise FileNotFoundError(f"Source file not found: {source_html}")

    module = _load_export_svg_module()
    html_content = source_html.read_text(encoding="utf-8")
    svg_document = module.export_svg_document(html_content, source_html)

    target = output_svg if output_svg is not None else source_html.with_suffix(".svg")
    target = Path(target).resolve()
    target.write_text(svg_document, encoding="utf-8")
    return target


def export_png(source_html: Path, output_png: Optional[Path] = None, scale: int = 2) -> Path:
    """Export the first SVG in a diagram HTML file to high-res transparent PNG via Playwright."""
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
    except ImportError as err:
        raise RuntimeError(
            "Playwright is not installed. Run 'pip install playwright && playwright install chromium'."
        ) from err

    source_html = Path(source_html).resolve()
    if not source_html.is_file():
        raise FileNotFoundError(f"Source file not found: {source_html}")

    target = output_png if output_png is not None else source_html.with_suffix(".png")
    target = Path(target).resolve()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(device_scale_factor=scale)
            # Add ?motion=static so animated diagrams freeze at the static complete frame
            url = source_html.as_uri() + "?motion=static"
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=12000)
            except PlaywrightTimeoutError:
                page.evaluate("window.stop()")
                page.wait_for_timeout(2000)

            svg_locator = page.locator("svg").first
            svg_locator.screenshot(path=str(target), omit_background=True)
        finally:
            browser.close()

    return target


def export_both(source_html: Path, output_dir: Optional[Path] = None, scale: int = 2) -> Tuple[Path, Path]:
    """Export both SVG and PNG for a diagram HTML file."""
    source_html = Path(source_html).resolve()
    out_dir = Path(output_dir).resolve() if output_dir else source_html.parent
    stem = source_html.stem

    svg_target = out_dir / f"{stem}.svg"
    png_target = out_dir / f"{stem}.png"

    res_svg = export_svg(source_html, svg_target)
    res_png = export_png(source_html, png_target, scale=scale)

    return res_svg, res_png
