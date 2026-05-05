# -*- coding: utf-8 -*-
"""标注 HTTP 服务器 - 托管标注页面 + 接收提交"""

import os
import json
import threading
import webbrowser
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ANNOTATOR_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(ANNOTATOR_DIR, "index.html")
PORT = 8765


class AnnotationState:
    """全局标注状态"""
    def __init__(self):
        self.result_path = None
        self.comments_path = None
        self.event = threading.Event()
        self.image_path = None

    def reset(self, image_path: str):
        self.result_path = None
        self.comments_path = None
        self.event.clear()
        self.image_path = image_path

    def wait(self, timeout=600) -> tuple:
        """等待用户完成标注，返回 (图片路径, 评论路径)"""
        self.event.wait(timeout)
        return self.result_path, self.comments_path

    def submit(self, result_path: str, comments_path: str = None):
        self.result_path = result_path
        self.comments_path = comments_path
        self.event.set()


annotator_state = AnnotationState()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self._serve_file(INDEX_HTML, "text/html; charset=utf-8")

        elif parsed.path == "/image":
            params = parse_qs(parsed.query)
            path = params.get("path", [None])[0]
            if path and os.path.exists(path):
                ext = os.path.splitext(path)[1].lower()
                ct = {".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml"}.get(ext, "application/octet-stream")
                self._serve_file(path, ct)
            else:
                self._send_json(404, {"error": "image not found"})

        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/submit":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            image_data = body.get("image", "")
            comments_data = body.get("comments", [])

            # 解码 base64 并保存
            if image_data.startswith("data:image/png;base64,"):
                image_data = image_data[len("data:image/png;base64,"):]

            # 保存到与源图片同目录
            src = annotator_state.image_path or "annotated"
            base = os.path.splitext(src)[0]
            out_path = base + "_annotated.png"

            with open(out_path, "wb") as f:
                f.write(base64.b64decode(image_data))

            # 保存评论为 JSON
            comments_path = None
            if comments_data:
                comments_path = base + "_comments.json"
                with open(comments_path, "w", encoding="utf-8") as f:
                    json.dump(comments_data, f, ensure_ascii=False, indent=2)

            annotator_state.submit(out_path, comments_path)
            self._send_json(200, {"ok": True, "path": out_path, "comments": len(comments_data)})
        else:
            self._send_json(404, {"error": "not found"})

    def _serve_file(self, path, content_type):
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


_server = None
_server_thread = None


def ensure_server_running():
    """确保 HTTP server 在运行"""
    global _server, _server_thread
    if _server is not None:
        return

    _server = HTTPServer(("127.0.0.1", PORT), Handler)
    _server_thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _server_thread.start()


def open_annotator(image_path: str) -> tuple:
    """打开标注页面并等待结果，返回 (图片路径, 评论路径)"""
    ensure_server_running()
    annotator_state.reset(image_path)

    # 打开浏览器
    import urllib.parse
    url = f"http://localhost:{PORT}/?image={urllib.parse.quote(image_path)}"
    webbrowser.open(url)

    # 阻塞等待
    img_path, comments_path = annotator_state.wait(timeout=600)
    return img_path, comments_path


if __name__ == "__main__":
    print(f"Starting annotator server on http://localhost:{PORT}")
    ensure_server_running()
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
