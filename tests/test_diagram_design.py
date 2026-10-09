"""Unit tests for diagram_design package."""

import unittest
from pathlib import Path

from diagram_design.core.checker import check_html_content
from diagram_design.core.doctor import run_doctor
from diagram_design.core.exporter import export_svg
from diagram_design.core.importer import import_diagram, import_mermaid_code
from diagram_design.core.templates import get_template, scaffold_diagram
from diagram_design.core.types import DIAGRAM_TYPES, get_type, list_types


class TestDiagramTypes(unittest.TestCase):
    def test_types_count(self):
        self.assertGreaterEqual(len(DIAGRAM_TYPES), 44)

    def test_get_type(self):
        arch = get_type("architecture")
        self.assertIsNotNone(arch)
        self.assertEqual(arch.name, "Architecture")
        self.assertEqual(arch.category, "Architecture & Systems")

    def test_list_types_filter(self):
        logic_types = list_types("Logic & State")
        self.assertTrue(len(logic_types) >= 5)
        type_ids = [t.id for t in logic_types]
        self.assertIn("flowchart", type_ids)
        self.assertIn("sequence", type_ids)


class TestDiagramTemplates(unittest.TestCase):
    def test_get_template(self):
        template = get_template("light")
        self.assertIn("<!DOCTYPE html>", template)
        self.assertIn("<svg", template)
        self.assertIn("Instrument Serif", template)

    def test_scaffold_diagram(self):
        html = scaffold_diagram(
            type_id="sequence",
            title="OAuth Flow",
            description="Client authenticating with identity provider",
            theme="light",
        )
        self.assertIn("<title>OAuth Flow</title>", html)
        self.assertIn("<svg", html)
        self.assertIn("role=\"img\"", html)


class TestDiagramChecker(unittest.TestCase):
    def test_check_valid_diagram(self):
        html = scaffold_diagram(
            type_id="architecture",
            title="System Topology",
            description="Clean architecture diagram",
            theme="light",
        )
        errors = check_html_content(html)
        self.assertEqual(errors, [])

    def test_check_invalid_diagram(self):
        bad_html = "<html><body><svg></svg></body></html>"
        errors = check_html_content(bad_html)
        self.assertTrue(len(errors) > 0)


class TestDiagramImporter(unittest.TestCase):
    def test_mermaid_inline(self):
        code = """graph LR
            A[Client] --> B[Server]
            B --> C[(Database)]
        """
        ir, digest = import_mermaid_code(code)
        self.assertEqual(len(ir.get("diagrams", [])), 1)
        nodes = ir["diagrams"][0]["nodes"]
        self.assertEqual(len(nodes), 3)
        self.assertIn("Database", digest)


class TestDiagramDoctor(unittest.TestCase):
    def test_doctor_runs(self):
        checks = run_doctor()
        self.assertTrue(len(checks) >= 5)
        statuses = {c.status for c in checks}
        self.assertIn("OK", statuses)


if __name__ == "__main__":
    unittest.main()
