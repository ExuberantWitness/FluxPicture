# -*- coding: utf-8 -*-
"""FluxPicture MCP Server - 图表生成+标注+视觉修正闭环"""

import os
import json
import re
import sys

# 确保 core/ 可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "fluxpicture",
    instructions=(
        "FluxPicture 图表迭代修正工具。工作流程：\n"
        "1. 先用 fireworks-tech-graph skill 生成初始图表 SVG/PNG\n"
        "2. 用 ask_satisfaction 询问用户是否满意\n"
        "3. 如果不满意，用 open_annotator 让用户在图上标注问题\n"
        "4. 用 refine_with_vision 让 GLM-5V 分析标注+反馈，生成修正 JSON\n"
        "5. 用 render_diagram 从新 JSON 重新渲染图表\n"
        "6. 重复直到用户满意"
    ),
)


@mcp.tool()
def render_diagram(json_data: str, output_dir: str = "") -> str:
    """从 JSON 数据渲染 SVG 和 PNG 技术图表。

    Args:
        json_data: 图表 JSON 字符串（符合 generate-from-template.py 的 schema）
        output_dir: 输出目录，默认为用户桌面

    Returns:
        生成的 SVG 和 PNG 文件路径
    """
    from core.svg_engine import render_svg, render_png_from_svg

    try:
        data = json.loads(json_data) if isinstance(json_data, str) else json_data
    except json.JSONDecodeError as e:
        return f"JSON 解析失败: {e}"

    template_type = data.get("template_type", "architecture")
    title = data.get("title", "diagram")
    # 清理文件名
    safe_name = re.sub(r'[^\w一-鿿-]', '_', title)[:50]

    if not output_dir:
        output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    os.makedirs(output_dir, exist_ok=True)

    svg_path = os.path.join(output_dir, f"{safe_name}.svg")
    png_path = os.path.join(output_dir, f"{safe_name}.png")

    # 渲染 SVG
    svg_string = render_svg(template_type, data)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_string)

    # 渲染 PNG
    render_png_from_svg(svg_string, png_path, 1920)

    return json.dumps({
        "svg": svg_path,
        "png": png_path,
        "svg_size": len(svg_string),
    }, ensure_ascii=False)


@mcp.tool()
def ask_satisfaction(diagram_path: str) -> str:
    """展示生成的图表并询问用户是否满意。

    这个工具提示你应该向用户展示图片并询问反馈。
    直接在对话中向用户展示图片并询问即可。

    Args:
        diagram_path: 图表文件路径（PNG 或 SVG）

    Returns:
        提示信息
    """
    if not os.path.exists(diagram_path):
        return f"文件不存在: {diagram_path}"
    return (
        f"图表已生成: {diagram_path}\n"
        f"请向用户展示这张图片，询问是否满意。\n"
        f"如果不满意，请收集用户的文字反馈，然后调用 open_annotator 让用户标注。"
    )


@mcp.tool()
def open_annotator(image_path: str) -> str:
    """打开浏览器标注页面，让用户在图片上涂改标注并添加评论。

    启动本地 HTTP 服务器，在浏览器中打开标注工具。
    用户可以用画笔、箭头、矩形在图上标注问题，并用评论工具添加文字修改意见。
    标注完成后自动返回标注后的图片路径和评论文件路径。

    Args:
        image_path: 原始图片路径（PNG）

    Returns:
        标注后的图片路径和评论 JSON 路径
    """
    from annotator.server import open_annotator as _open

    if not os.path.exists(image_path):
        return f"文件不存在: {image_path}"

    result = _open(image_path)
    if result:
        annotated_path, comments_path = result
        return json.dumps({
            "annotated_image": annotated_path,
            "comments_path": comments_path,
        }, ensure_ascii=False)
    return "标注超时或取消"


@mcp.tool()
def refine_with_vision(
    annotated_image_path: str,
    user_feedback: str,
    previous_json: str,
    comments_path: str = "",
) -> str:
    """使用 GLM-5V 多模态模型分析标注图片和用户反馈，修正图表 JSON。

    将标注后的图片、用户文字反馈、评论标注和原始 JSON 发送给视觉模型，
    让模型理解标注含义并输出修正后的 JSON。

    Args:
        annotated_image_path: 标注后的图片路径
        user_feedback: 用户的文字反馈描述
        previous_json: 原始图表 JSON 字符串
        comments_path: 评论标注 JSON 文件路径（可选）

    Returns:
        修正后的 JSON 字符串
    """
    from core.vision_client import analyze_image
    from core.prompt_builder import REFINE_PROMPT_TEMPLATE

    if not os.path.exists(annotated_image_path):
        return f"文件不存在: {annotated_image_path}"

    # 读取评论数据
    comments_text = user_feedback
    if comments_path and os.path.exists(comments_path):
        with open(comments_path, "r", encoding="utf-8") as f:
            comments_data = json.load(f)
        lines = []
        for c in comments_data:
            cid = c.get("id", "?")
            cx = c.get("x", 0)
            cy = c.get("y", 0)
            txt = c.get("text", "")
            if txt:
                lines.append(f"#{cid} (位置 x:{cx}, y:{cy}): {txt}")
        if lines:
            comments_text = "\n".join(lines)
            if user_feedback:
                comments_text = f"{user_feedback}\n\n{comments_text}"

    prompt = REFINE_PROMPT_TEMPLATE.format(
        comments=comments_text,
        previous_json=previous_json,
    )

    try:
        result = analyze_image(annotated_image_path, prompt)

        # 尝试提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            json_str = json_match.group()
            # 修复常见问题
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # 尾部逗号
            # 验证
            json.loads(json_str)
            return json_str
        return f"模型返回的内容无法解析为 JSON:\n{result}"
    except Exception as e:
        return f"视觉分析失败: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
