"""Command-line interface for Diagram Design."""

from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path

from diagram_design import __version__
from diagram_design.core.checker import check_file
from diagram_design.core.doctor import run_doctor
from diagram_design.core.exporter import export_both, export_png, export_svg
from diagram_design.core.importer import import_diagram
from diagram_design.core.templates import find_assets_dir, scaffold_diagram
from diagram_design.core.types import DIAGRAM_CATEGORIES, DIAGRAM_TYPES, get_type, list_types
from diagram_design.studio.server import start_studio_server


def cmd_list(args):
    """List diagram types."""
    category = args.category
    types = list_types(category)
    print(f"\nDiagram Design · 44 Editorial Visual Types (Total: {len(types)})\n" + "=" * 60)
    current_cat = None
    for t in sorted(types, key=lambda x: (x.category, x.name)):
        if t.category != current_cat:
            current_cat = t.category
            print(f"\n[{current_cat}]")
        print(f"  • {t.id:<22} - {t.name:<20} : {t.description}")
    print()


def cmd_info(args):
    """Show details for a diagram type."""
    dtype = get_type(args.type)
    if not dtype:
        print(f"Error: Unknown diagram type '{args.type}'. Run 'diagram list' to see all 44 types.", file=sys.stderr)
        return 1

    print(f"\nType: {dtype.name} ({dtype.id})")
    print(f"Category:        {dtype.category}")
    print(f"ViewBox:         {dtype.view_box}")
    print(f"Description:     {dtype.description}")
    print(f"When to use:     {dtype.when_to_use}")
    print(f"Reference file:  skills/diagram-design/references/{dtype.reference_file}")
    if dtype.semantic_patterns:
        print(f"Semantic slots:  {', '.join(dtype.semantic_patterns)}")
    print()


def cmd_new(args):
    """Scaffold a new diagram file."""
    type_id = args.type
    dtype = get_type(type_id)
    if not dtype:
        print(f"Error: Unknown diagram type '{type_id}'. Run 'diagram list' to see all 44 types.", file=sys.stderr)
        return 1

    title = args.title or f"{dtype.name} Diagram"
    desc = args.desc or dtype.description
    theme = args.theme
    use_canonical = not args.blank

    html = scaffold_diagram(
        type_id=type_id,
        title=title,
        description=desc,
        theme=theme,
        use_canonical_body=use_canonical,
    )

    out_path = Path(args.output) if args.output else Path(f"{dtype.id}.html")
    out_path.write_text(html, encoding="utf-8")
    print(f"Created diagram: {out_path} ({len(html)} bytes)")
    return 0


def cmd_check(args):
    """Run self-check on diagram HTML files."""
    failed = False
    for f in args.files:
        path = Path(f)
        if not path.is_file():
            print(f"FAIL {path} (file not found)")
            failed = True
            continue
        errors = check_file(path)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for err in errors:
                print(f"  ✗ {err}")
        else:
            print(f"OK   {path}")
    return 1 if failed else 0


def cmd_export(args):
    """Export diagram HTML to SVG and/or PNG."""
    path = Path(args.file)
    if not path.is_file():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    fmt = args.format.lower()
    scale = args.scale
    out = Path(args.output) if args.output else None

    if fmt == "svg":
        res = export_svg(path, out)
        print(f"Exported SVG: {res}")
    elif fmt == "png":
        res = export_png(path, out, scale=scale)
        print(f"Exported PNG: {res}")
    elif fmt == "both":
        res_svg, res_png = export_both(path, out, scale=scale)
        print(f"Exported SVG: {res_svg}")
        print(f"Exported PNG: {res_png}")
    else:
        print(f"Error: Unknown format '{fmt}'. Choose 'svg', 'png', or 'both'.", file=sys.stderr)
        return 1
    return 0


def cmd_import(args):
    """Import and parse a Mermaid, Draw.io, or Excalidraw file."""
    path = Path(args.file)
    if not path.is_file():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        ir, digest = import_diagram(path)
    except Exception as exc:
        print(f"Import error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        output = json.dumps(ir, indent=2)
    else:
        output = digest

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Wrote output to {args.out}")
    else:
        print(output)
    return 0


def cmd_doctor(args):
    """Run system diagnostics."""
    print(f"\nDiagram Design Doctor v{__version__}\n" + "=" * 50)
    checks = run_doctor()
    has_fail = False
    for c in checks:
        badge = f"[{c.status:<4}]"
        print(f"{badge} {c.name:<32} : {c.message}")
        if c.recommendation:
            print(f"       -> Action: {c.recommendation}")
        if c.status == "FAIL":
            has_fail = True
    print()
    return 1 if has_fail else 0


def cmd_serve(args):
    """Start Diagram Design Studio web app."""
    start_studio_server(port=args.port, open_browser=args.open)


def cmd_install(args):
    """Install skill into Antigravity global or workspace config."""
    source_dir = find_assets_dir().parent
    installed_any = False

    if args.all or args.workspace:
        ws_target = Path.cwd() / ".agents" / "skills" / "diagram-design"
        ws_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, ws_target, dirs_exist_ok=True)
        print(f"Installed workspace skill: {ws_target}")
        installed_any = True

    if args.all or args.global_install:
        global_target = Path.home() / ".gemini" / "config" / "skills" / "diagram-design"
        global_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, global_target, dirs_exist_ok=True)
        print(f"Installed global skill: {global_target}")
        installed_any = True

    if not installed_any:
        print("Specify --workspace, --global, or --all to install.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="diagram",
        description="Diagram Design: Editorial diagram design system for HTML + SVG (44 visual types).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # list
    p_list = subparsers.add_parser("list", help="List all 44 diagram types")
    p_list.add_argument("-c", "--category", help="Filter by category")

    # info
    p_info = subparsers.add_parser("info", help="Show details on a diagram type")
    p_info.add_argument("type", help="Diagram type slug (e.g. architecture, sequence, sankey)")

    # new / create
    p_new = subparsers.add_parser("new", aliases=["create"], help="Scaffold a new diagram HTML file")
    p_new.add_argument("type", help="Diagram type (e.g. architecture, flowchart, sequence)")
    p_new.add_argument("-t", "--title", help="Diagram title")
    p_new.add_argument("-d", "--desc", help="Diagram description")
    p_new.add_argument(
        "--theme",
        default="light",
        choices=["light", "dark", "full", "animated", "terminal"],
        help="Visual theme (default: light)",
    )
    p_new.add_argument("-o", "--output", help="Output file path (default: <type>.html)")
    p_new.add_argument("--blank", action="store_true", help="Start from minimal empty skeleton rather than canonical example")

    # check
    p_check = subparsers.add_parser("check", help="Verify diagram HTML accessibility & design contract")
    p_check.add_argument("files", nargs="+", help="Diagram HTML files to check")

    # export
    p_export = subparsers.add_parser("export", help="Export diagram HTML to SVG or PNG")
    p_export.add_argument("file", help="Source diagram HTML file")
    p_export.add_argument(
        "-f",
        "--format",
        default="both",
        choices=["svg", "png", "both"],
        help="Target format (default: both)",
    )
    p_export.add_argument("-o", "--output", help="Target output file or directory")
    p_export.add_argument("-s", "--scale", type=int, default=2, help="PNG device scale factor (default: 2)")

    # import
    p_import = subparsers.add_parser("import", help="Import Mermaid, Draw.io, or Excalidraw diagram")
    p_import.add_argument("file", help="Input file (.mmd, .drawio, .excalidraw)")
    p_import.add_argument(
        "-f",
        "--format",
        default="markdown",
        choices=["markdown", "json"],
        help="Output format (default: markdown)",
    )
    p_import.add_argument("-o", "--out", help="Output file path")

    # doctor
    p_doc = subparsers.add_parser("doctor", help="Run system readiness checks")

    # serve / studio
    p_serve = subparsers.add_parser("serve", aliases=["studio"], help="Start Diagram Design Studio web app")
    p_serve.add_argument("-p", "--port", type=int, default=8765, help="Port to listen on (default: 8765)")
    p_serve.add_argument("--open", action="store_true", help="Automatically open browser")

    # install
    p_inst = subparsers.add_parser("install", help="Install skill into Antigravity")
    p_inst.add_argument("-w", "--workspace", action="store_true", help="Install into current workspace .agents/")
    p_inst.add_argument("-g", "--global", dest="global_install", action="store_true", help="Install into global config")
    p_inst.add_argument("-a", "--all", action="store_true", help="Install into both workspace and global")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    if args.command == "list":
        return cmd_list(args)
    elif args.command == "info":
        return cmd_info(args)
    elif args.command in ("new", "create"):
        return cmd_new(args)
    elif args.command == "check":
        return cmd_check(args)
    elif args.command == "export":
        return cmd_export(args)
    elif args.command == "import":
        return cmd_import(args)
    elif args.command == "doctor":
        return cmd_doctor(args)
    elif args.command in ("serve", "studio"):
        return cmd_serve(args)
    elif args.command == "install":
        return cmd_install(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
