"""Local HTTP API and static file server for Diagram Design Studio."""

from __future__ import annotations
import base64
import json
import mimetypes
import os
import sys
import tempfile
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

from diagram_design.core.checker import check_html_content
from diagram_design.core.doctor import run_doctor
from diagram_design.core.exporter import export_png, export_svg
from diagram_design.core.importer import import_mermaid_code
from diagram_design.core.templates import find_assets_dir, scaffold_diagram
from diagram_design.core.types import DIAGRAM_CATEGORIES, DIAGRAM_TYPES, get_type, list_types

STATIC_DIR = Path(__file__).resolve().parent / "static"


class StudioServer(ThreadingHTTPServer):
    """Threading HTTP server with graceful client disconnect handling."""
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        exc_type, exc_val, _ = sys.exc_info()
        # Suppress normal client disconnection noise on Windows
        if exc_type in (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            return
        super().handle_error(request, client_address)


class StudioRequestHandler(SimpleHTTPRequestHandler):
    """HTTP Request handler for studio web app and backend API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format, *args):
        # Silence verbose request logs
        pass

    def _send_json(self, data: Any, status: int = 200, head_only: bool = False):
        try:
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            if not head_only:
                self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        try:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_HEAD(self):
        try:
            self._handle_get(head_only=True)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_GET(self):
        try:
            self._handle_get(head_only=False)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _handle_get(self, head_only: bool = False):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Assets route: serve example diagrams and templates from skills assets directory
        if path.startswith("/assets/"):
            asset_filename = path.replace("/assets/", "")
            assets_dir = find_assets_dir()
            target = assets_dir / asset_filename

            # Fallback if variant does not exist
            if not target.is_file():
                for sfx in ("-animated", "-terminal", "-full", "-dark"):
                    if sfx in asset_filename:
                        fallback_name = asset_filename.replace(sfx, "")
                        fallback_target = assets_dir / fallback_name
                        if fallback_target.is_file():
                            target = fallback_target
                            break

            if target.is_file():
                mime, _ = mimetypes.guess_type(target.name)
                mime = mime or "application/octet-stream"
                data = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", f"{mime}; charset=utf-8" if "text" in mime or "html" in mime else mime)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                if not head_only:
                    self.wfile.write(data)
                return
            else:
                self.send_error(404, "Asset not found")
                return

        # API: List all types & categories with available variants
        if path == "/api/types":
            assets_dir = find_assets_dir()
            types_list = []
            for t in DIAGRAM_TYPES.values():
                stem = t.example_stem or f"example-{t.id}"
                variants = ["light"]
                if (assets_dir / f"{stem}-dark.html").exists():
                    variants.append("dark")
                if (assets_dir / f"{stem}-full.html").exists():
                    variants.append("full")
                if (assets_dir / f"{stem}-animated.html").exists():
                    variants.append("animated")
                if (assets_dir / f"{stem}-terminal.html").exists():
                    variants.append("terminal")

                types_list.append({
                    "id": t.id,
                    "name": t.name,
                    "category": t.category,
                    "description": t.description,
                    "when_to_use": t.when_to_use,
                    "view_box": t.view_box,
                    "example_stem": t.example_stem,
                    "reference_file": t.reference_file,
                    "variants": variants,
                })
            self._send_json({
                "categories": DIAGRAM_CATEGORIES,
                "types": types_list,
            }, head_only=head_only)
            return

        # API: Get template for a type
        if path == "/api/template":
            type_id = query.get("type", ["architecture"])[0]
            theme = query.get("theme", ["light"])[0]
            title = query.get("title", ["System Architecture"])[0]
            desc = query.get("desc", ["Components and interactions"])[0]
            use_canonical = query.get("canonical", ["true"])[0].lower() in ("true", "1")

            html = scaffold_diagram(
                type_id=type_id,
                title=title,
                description=desc,
                theme=theme,
                use_canonical_body=use_canonical,
            )
            self._send_json({"type": type_id, "theme": theme, "html": html}, head_only=head_only)
            return

        # API: Doctor system diagnostics
        if path == "/api/doctor":
            checks = run_doctor()
            self._send_json({
                "checks": [
                    {
                        "name": c.name,
                        "status": c.status,
                        "message": c.message,
                        "recommendation": c.recommendation,
                    }
                    for c in checks
                ]
            }, head_only=head_only)
            return

        # Default static files
        if head_only:
            super().do_HEAD()
        else:
            super().do_GET()

    def do_POST(self):
        try:
            self._handle_post()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _handle_post(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # API: Check HTML content
        if path == "/api/check":
            html_content = body.get("html", "")
            if not html_content.strip():
                self._send_json({"ok": False, "errors": ["HTML content is empty"]})
                return
            errors = check_html_content(html_content)
            self._send_json({
                "ok": len(errors) == 0,
                "errors": errors,
            })
            return

        # API: Export SVG
        if path == "/api/export/svg":
            html_content = body.get("html", "")
            title = body.get("title", "diagram")
            slug = urllib.parse.quote_plus(title.lower().replace(" ", "-")) or "diagram"

            with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tmp:
                tmp.write(html_content)
                tmp_path = Path(tmp.name)

            try:
                svg_path = export_svg(tmp_path)
                svg_content = svg_path.read_text(encoding="utf-8")
                self._send_json({
                    "ok": True,
                    "svg": svg_content,
                    "filename": f"{slug}.svg",
                })
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=400)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
                if "svg_path" in locals() and svg_path.exists():
                    svg_path.unlink()
            return

        # API: Export PNG
        if path == "/api/export/png":
            html_content = body.get("html", "")
            scale = int(body.get("scale", 2))
            title = body.get("title", "diagram")
            slug = urllib.parse.quote_plus(title.lower().replace(" ", "-")) or "diagram"

            with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tmp:
                tmp.write(html_content)
                tmp_path = Path(tmp.name)

            try:
                png_path = export_png(tmp_path, scale=scale)
                png_bytes = png_path.read_bytes()
                png_b64 = base64.b64encode(png_bytes).decode("ascii")
                self._send_json({
                    "ok": True,
                    "png_base64": f"data:image/png;base64,{png_b64}",
                    "filename": f"{slug}.png",
                    "size_bytes": len(png_bytes),
                })
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=400)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
                if "png_path" in locals() and png_path.exists():
                    png_path.unlink()
            return

        # API: Convert Mermaid code
        if path == "/api/convert/mermaid":
            code = body.get("code", "")
            if not code.strip():
                self._send_json({"ok": False, "error": "Mermaid code is empty"}, status=400)
                return
            try:
                ir, digest = import_mermaid_code(code)
                suggested_type = "architecture"
                if ir.get("diagrams"):
                    d = ir["diagrams"][0]
                    candidates = d.get("analysis", {}).get("type_candidates", [])
                    if candidates:
                        suggested_type = candidates[0]
                self._send_json({
                    "ok": True,
                    "ir": ir,
                    "digest": digest,
                    "suggested_type": suggested_type,
                })
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=400)
            return

        self.send_error(404, "Endpoint not found")


def start_studio_server(port: int = 8765, open_browser: bool = False):
    """Start the Diagram Design Studio server."""
    host = "127.0.0.1"
    
    # Try specified port or increment if in use
    httpd = None
    actual_port = port
    for p in range(port, port + 20):
        try:
            httpd = StudioServer((host, p), StudioRequestHandler)
            actual_port = p
            break
        except OSError:
            continue

    if not httpd:
        raise OSError(f"Could not bind to any port between {port} and {port + 20}")

    url = f"http://{host}:{actual_port}"
    print(f"\n=======================================================", flush=True)
    print(f"  Diagram Design Studio is running at:", flush=True)
    print(f"  --> {url}", flush=True)
    print(f"=======================================================\n", flush=True)

    if open_browser:
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Diagram Design Studio...", flush=True)
    finally:
        httpd.server_close()
