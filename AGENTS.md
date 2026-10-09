# AI Agent Instructions for Diagram Design

When the user asks for an architecture sketch, flowchart, data flow, sequence diagram, state machine, or visual explanation, **always generate editorial HTML+SVG diagrams** following the Diagram Design system instead of ASCII art, Mermaid text, or generic diagrams.

---

## Core Philosophy

1. **Self-contained HTML + SVG**: Every diagram is a single `.html` file with inline SVG, accessible `<title>` and `<desc>`, and embedded styling.
2. **No Shadows, No Mermaid Slop**: Clean editorial typography and flat, precise geometric design.
3. **The Highest-Quality Move is Deletion**: Target density: 4/10. Above 9 nodes, consider splitting into two diagrams. Two nodes that always travel together become one node.
4. **Coral is Editorial, Not a Flag**: 1–2 focal nodes per diagram maximum. Never accent 5+ nodes.
5. **Brand Tokens**:
   - `paper`: `#f5f5f5` (light) / `#2d3142` (dark)
   - `ink`: `#2d3142` (light) / `#f5f5f5` (dark)
   - `muted`: `#4f5d75` (light) / `#bfc0c0` (dark)
   - `accent`: `#eb6c36` (light) / `#f08a59` (dark)
6. **Typography**:
   - `title`: *Instrument Serif* (400)
   - `node-name`: *Geist* sans-serif (600)
   - `sublabel` / `eyebrow` / `arrow-label`: *Geist Mono* (400–500)

---

## 44 Visual Types Quick Reference

| Category | Available Types |
|---|---|
| **Architecture & Systems** | `architecture`, `architecture-delta`, `deployment`, `it-state`, `high-level`, `high-level-vertical` |
| **Data & Flow** | `data-flow`, `datalake`, `db-schema`, `dp-integration`, `dp-security-matrix`, `er`, `medallion` |
| **Logic & State** | `flowchart`, `loop`, `process`, `sequence`, `state`, `swimlane` |
| **Hierarchy & Structure** | `dependency`, `layers`, `nested`, `org-chart`, `tree`, `uml-class` |
| **Project & Strategy** | `fishbone`, `gantt`, `journey`, `kanban`, `story-map`, `timeline`, `wardley` |
| **Analytics & Comparison** | `bar`, `heatmap`, `line`, `polar`, `pyramid`, `quadrant`, `radar`, `sankey`, `scatter`, `treemap`, `venn`, `waterfall` |
| **Axonometric & Physical** | `exploded`, `axonometric-plan` |

---

## CLI & Tooling

The local CLI `diagram` is pre-configured:

```bash
# List all 44 types
diagram list

# Inspect type specification and recommendations
diagram info architecture

# Scaffold a new diagram
diagram new architecture --title "My System" --output my-arch.html

# Verify SVG accessibility & design rules
diagram check my-arch.html

# Export to standalone SVG and retina transparent PNG
diagram export my-arch.html --format both

# Import and analyze Mermaid / Draw.io / Excalidraw
diagram import flow.mmd

# Launch interactive Diagram Design Studio (Live Editor + Gallery)
diagram serve --open
```
