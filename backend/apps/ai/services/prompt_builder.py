"""Prompt engineering — system prompts and context assembly."""
from django.conf import settings

# 系统级 Prompt：约束 AI 的角色与输出风格
SYSTEM_PROMPT = """你是 ram-adminx 后台管理系统的 AI 助手。

你的职责：
1. 用自然语言回答管理员关于系统数据的提问。
2. 提供数据分析与运营洞察。
3. 严格遵守安全原则：不得输出任何密码、Token、密钥等敏感信息。

输出要求：
- 用简洁的中文回答。
- 涉及数据时优先使用 Markdown 表格或列表。
- 不确定时如实说明，不要编造数据。
- 拒绝任何越权操作（如批量删除用户）的请求，并提示走正式审批流程。
"""

DASHBOARD_INSIGHT_PROMPT = """基于以下仪表盘统计数据，给出 3-5 条关键运营洞察（每条不超过 60 字）：

数据：
{stats}

请用 JSON 数组返回，每项形如：{{"insight": "...", "level": "info|warning|danger"}}
"""


def build_chat_messages(user_messages: list, context: str = '') -> list[dict]:
    """组装对话消息列表（前置 System Prompt + 用户消息）.

    Args:
        user_messages: [{role, content}, ...]
        context: 可选的上下文标记（dashboard / user_list / role_list）

    Returns:
        OpenAI 兼容的消息列表
    """
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    # 上下文提示（轻量）
    if context:
        messages.append({
            'role': 'system',
            'content': f"当前页面上下文: {context}",
        })

    for m in user_messages:
        role = m.get('role', 'user')
        content = m.get('content', '')
        if role not in ('user', 'assistant'):
            role = 'user'
        if content:
            messages.append({'role': role, 'content': content})

    return messages


def build_insight_prompt(stats: dict) -> str:
    """仪表盘洞察 Prompt."""
    return DASHBOARD_INSIGHT_PROMPT.format(stats=stats)


def build_analyze_prompt(question: str, data: dict) -> list[dict]:
    """数据分析 Prompt — 把结构化数据喂给 AI 做分析."""
    import json
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    messages.append({
        'role': 'user',
        'content': (
            f"分析问题: {question}\n\n"
            f"相关数据（JSON）:\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```\n\n"
            "请基于以上数据给出分析结论。"
        ),
    })
    return messages


def build_report_prompt(report_type: str, data: dict) -> list[dict]:
    """报告生成 Prompt."""
    import json
    title_map = {
        'user_activity': '用户活跃度报告',
        'role_distribution': '角色分布报告',
        'system_overview': '系统总览报告',
    }
    title = title_map.get(report_type, report_type)
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    messages.append({
        'role': 'user',
        'content': (
            f"请生成一份《{title}》。要求：包含关键指标、趋势分析、风险提示、改进建议。"
            f"使用 Markdown 格式。\n\n数据:\n```json\n"
            f"{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
        ),
    })
    return messages
