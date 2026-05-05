[English](README.md) | [中文](README.zh.md)

# FluxPicture

> **AI-driven iterative diagram refinement.** Generate technical diagrams, annotate issues visually, and let a multimodal vision model refine them — in a closed loop until you're satisfied.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP Server](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)
[![7 Visual Styles](https://img.shields.io/badge/Styles-7-purple)]()
[![14 Diagram Types](https://img.shields.io/badge/Diagram%20Types-14-green)]()
[![GLM-5V Powered](https://img.shields.io/badge/Vision-GLM--5V-orange)]()

---

## What Makes FluxPicture Different?

FluxPicture extends the diagram generation workflow with a **multimodal refinement loop**. Traditional tools stop at "generate and hope it's right." FluxPicture adds:

1. **Generate** — Create SVG/PNG diagrams from natural language via the `fireworks-tech-graph` skill
2. **Annotate** — Open a browser-based annotator with pen, arrow, rect, and **comment pins** directly on the diagram
3. **Refine** — Send the annotated image + structured comments to a vision model (GLM-5V) for intelligent JSON correction
4. **Re-render** — Produce an updated diagram and repeat until satisfied

```
User: "Draw a RAG pipeline architecture"
  → Skill generates initial SVG/PNG
  → User: "Not satisfied"
  → Browser annotator opens — user draws arrows and adds comments:
      #1: "This module should be named 'Retriever'"
      #2: "Add an arrow from Cache to LLM"
      #3: "Delete this node"
  → GLM-5V analyzes image + comments → outputs corrected JSON
  → Re-render → repeat until satisfied
```

---

## Architecture

```
Claude Code
  ├── fireworks-tech-graph skill    (SVG/PNG generation)
  └── FluxPicture MCP Server
        ├── render_diagram          → JSON → SVG + PNG
        ├── ask_satisfaction        → Prompt user feedback
        ├── open_annotator          → Browser annotation tool
        └── refine_with_vision      → GLM-5V multimodal refinement
```

---

## Core Components

### MCP Server (`mcp_server.py`)

Four tools exposed via Model Context Protocol:

| Tool | Description |
|------|-------------|
| `render_diagram` | Render SVG + PNG from JSON data |
| `ask_satisfaction` | Show diagram and ask user for feedback |
| `open_annotator` | Open browser annotator with comment pins |
| `refine_with_vision` | GLM-5V analyzes annotations + comments → corrected JSON |

### Browser Annotator (`annotator/`)

A single-page annotation tool served at `localhost:8765`:

- **Pen** — Freehand drawing in 5 colors
- **Arrow** — Directional arrows
- **Rectangle** — Dashed selection rectangles
- **Comment** — Numbered pins with editable text in a side panel
- **Eraser** — Remove annotations

Comments are saved as structured JSON alongside the annotated image, providing both visual context (on the canvas) and precise text (in the JSON) for the vision model.

### Vision Client (`core/vision_client.py`)

Sends annotated images + prompts to GLM-5V multimodal API for diagram refinement. Uses the ZhipuAI (智谱) API endpoint with `glm-4v-plus` model.

### SVG Engine (`core/svg_engine.py`)

Wraps `generate-from-template.py` for SVG generation and supports PNG export via Qt or sharp.

---

## Showcase

### Style 6 — Claude Official
*System Architecture — warm cream background, Anthropic brand colors*
![Style 6 — Claude Official](assets/samples/sample-style6-claude.png)

### Style 1 — Flat Icon (default)
*Mem0 Memory Architecture — white background, semantic arrows*
![Style 1 — Flat Icon](assets/samples/sample-style1-flat.png)

### Style 2 — Dark Terminal
*Tool Call Flow — dark background, neon accents*
![Style 2 — Dark Terminal](assets/samples/sample-style2-dark.png)

### Style 5 — Glassmorphism
*Multi-Agent Collaboration — frosted glass cards*
![Style 5 — Glassmorphism](assets/samples/sample-style5-glass.png)

All 7 visual styles are supported. See `references/` for style details.

---

## Supported Diagram Types

| Type | Description |
|------|-------------|
| Architecture | Services, components, horizontal layers |
| Data Flow | Data movement with labeled arrows |
| Flowchart | Decision/process steps |
| Agent Architecture | LLM + tools + memory (5-layer model) |
| Memory Architecture | Read/write paths, memory tiers |
| Sequence | Time-ordered message exchanges |
| Comparison | Feature matrix, side-by-side |
| Mind Map | Radial concept maps |
| Class / ER / State Machine / Use Case | Full UML support (14 types) |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ExuberantWitness/FluxPicture.git
```

### 2. Install dependencies

```bash
pip install "mcp[cli]"
```

### 3. Register as MCP Server

Create a `.mcp.json` in your project directory:

```json
{
  "mcpServers": {
    "fluxpicture": {
      "command": "python",
      "args": ["/path/to/FluxPicture/mcp_server.py"],
      "env": { "PYTHONUTF8": "1" }
    }
  }
}
```

Or use the CLI:

```bash
claude mcp add fluxpicture -- python /path/to/FluxPicture/mcp_server.py
```

### 4. (Optional) Set API key for GLM-5V

```bash
export FLUXPICTURE_API_KEY="your-zhipuai-api-key"
```

---

## File Structure

```
FluxPicture/
  mcp_server.py               # MCP Server entry point (FastMCP)
  annotator/
    server.py                 # HTTP server (localhost:8765)
    index.html                # Browser annotation UI
  core/
    svg_engine.py             # SVG rendering engine
    vision_client.py          # GLM-5V multimodal API client
    prompt_builder.py         # Vision refinement prompt templates
    __init__.py
  scripts/
    generate-from-template.py # SVG template generator
    generate-diagram.sh       # Validate + export
    validate-svg.sh           # SVG syntax validator
    test-all-styles.sh        # Batch style test
  references/                 # 7 style reference docs
  templates/                  # SVG templates per diagram type
  fixtures/                   # Sample JSON fixtures
  requirements.txt
```

---

## Styles

| # | Name | Background | Best For |
|---|------|-----------|----------|
| 1 | **Flat Icon** | White | Blogs, slides, docs |
| 2 | **Dark Terminal** | `#0f0f1a` | GitHub README, dev articles |
| 3 | **Blueprint** | `#0a1628` | Architecture docs |
| 4 | **Notion Clean** | White | Wikis, internal docs |
| 5 | **Glassmorphism** | Dark gradient | Product sites, keynotes |
| 6 | **Claude Official** | `#f8f6f3` | Anthropic-style diagrams |
| 7 | **OpenAI Official** | White | OpenAI-style diagrams |

---

## Acknowledgments

FluxPicture is built on top of [fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) by [yizhiyanhua-ai](https://github.com/yizhiyanhua-ai), which provides the excellent SVG generation engine with 7 visual styles, 14 diagram types, and AI/Agent domain pattern knowledge.

Key extensions added by FluxPicture:
- MCP Server integration for Claude Code
- Browser-based annotation with comment pin system
- Multimodal vision refinement via GLM-5V
- Closed-loop iterative diagram improvement

---

## License

MIT
