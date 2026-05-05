# -*- coding: utf-8 -*-
"""视觉修正 Prompt 构建"""

REFINE_PROMPT_TEMPLATE = """你是一个技术图表 JSON 修正助手。

用户在原有图表上进行了标注（用画笔/箭头/矩形圈出了问题区域），并添加了带编号的评论图钉。
图中红色圆形图钉上的数字对应下方评论编号。请结合评论内容和标注位置，修正原始 JSON。

## 修正规则
1. 保持 JSON schema 不变（template_type, style, title, containers, nodes, arrows, legend）
2. 根据评论和标注调整节点标签、位置、大小
3. 根据评论和标注调整箭头连接关系、路径
4. 根据评论和标注增删节点或箭头
5. 只输出修正后的完整 JSON，不要有任何其他文字
6. 不要使用 markdown 代码块标记
7. 不要在 JSON 中添加注释
8. 不要在最后一个元素后加逗号

## 用户评论标注
{comments}

## 原始 JSON
{previous_json}

请输出修正后的完整 JSON："""
