# -*- coding: utf-8 -*-
"""GLM-5V 多模态 API 客户端"""

import json
import base64
import urllib.request
import urllib.error
import ssl
import os

API_KEY = os.environ.get(
    "FLUXPICTURE_API_KEY",
    "b94fbfc2a8e7410781d0dd7d39e1ddcb.t6xfuyQL6zp2BLZ8"
)
ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4v-plus"


def analyze_image(image_path: str, prompt: str, api_key: str = None) -> str:
    """发送图片+文字到 GLM-5V，返回模型响应文本"""
    key = api_key or API_KEY

    # 读取图片并编码
    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{img_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )

    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
