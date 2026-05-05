# -*- coding: utf-8 -*-
"""SVG 渲染引擎 - 封装 generate-from-template.py"""

import sys
import os

_SCRIPTS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "scripts"
))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _get_module():
    import importlib
    return importlib.import_module("generate-from-template")


def render_svg(template_type: str, data: dict) -> str:
    """从 JSON data 渲染 SVG 字符串"""
    mod = _get_module()
    return mod.build_svg(template_type, data)


def render_png_from_svg(svg_string: str, output_path: str, width: int = 1920) -> str:
    """用 sharp (Node.js) 将 SVG 渲染为 PNG"""
    import subprocess
    import tempfile

    # 写临时 SVG
    tmp_svg = output_path.rsplit(".", 1)[0] + ".svg"
    with open(tmp_svg, "w", encoding="utf-8") as f:
        f.write(svg_string)

    # 尝试用 sharp
    try:
        script = f"""
const sharp = require('sharp');
const fs = require('fs');
const buf = fs.readFileSync({repr(tmp_svg)});
sharp(buf).resize({width}, null, {{fit: 'inside'}}).png().toFile({repr(output_path)})
  .then(() => process.exit(0))
  .catch(e => {{ console.error(e.message); process.exit(1); }});
"""
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
    except Exception:
        pass

    # Fallback: 用 Qt 渲染
    try:
        from PyQt5.QtSvg import QSvgRenderer
        from PyQt5.QtGui import QPixmap, QPainter
        from PyQt5.QtCore import QByteArray

        renderer = QSvgRenderer()
        data = QByteArray(svg_string.encode("utf-8"))
        if renderer.load(data):
            default_size = renderer.defaultSize()
            scale = width / default_size.width()
            height = int(default_size.height() * scale)
            pixmap = QPixmap(width, height)
            pixmap.fill()
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            renderer.render(painter)
            painter.end()
            pixmap.save(output_path, "PNG")
            return output_path
    except ImportError:
        pass

    # Fallback: 返回 SVG 路径
    return tmp_svg
