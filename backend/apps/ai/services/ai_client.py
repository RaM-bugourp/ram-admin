"""HTTP client for OpenAI-compatible chat completions API.

使用标准库 urllib 实现，避免引入 requests / openai SDK 依赖。
兼容 OpenAI / DeepSeek / QClaw 等 OpenAI 兼容协议的 Provider。
"""
import json
import logging
import urllib.error
import urllib.request

from apps.ai.services.ai_failover import ProviderConfig
from apps.ai.services.ai_errors import AIProviderError

logger = logging.getLogger(__name__)

# OpenAI 兼容的 Chat Completions 端点
CHAT_COMPLETIONS_PATH = '/chat/completions'


def _build_url(base_url: str, path: str) -> str:
    base = base_url.rstrip('/')
    if path == CHAT_COMPLETIONS_PATH:
        # OpenAI v1: https://api.openai.com/v1/chat/completions
        # DeepSeek:  https://api.deepseek.com/chat/completions (已有 v1 在 base)
        # 统一策略：若 base 已含路径段，直接拼接；否则补 /v1
        if base.endswith('/v1') or '/v1/' in base or 'deepseek.com' in base:
            return f"{base}{path}"
        return f"{base}/v1{path}"
    return f"{base}{path}"


def call_chat(config: ProviderConfig, messages: list[dict],
              temperature: float = 0.7, max_tokens: int | None = None) -> str:
    """调用单个 Provider 的 Chat Completions 接口.

    Returns:
        assistant 回复文本

    Raises:
        AIProviderError: 当请求失败、超时或响应格式错误时
    """
    url = _build_url(config.base_url, CHAT_COMPLETIONS_PATH)

    payload = {
        'model': config.model,
        'messages': messages,
        'temperature': temperature,
        'stream': False,
    }
    if max_tokens:
        payload['max_tokens'] = max_tokens

    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        method='POST',
    )
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {config.api_key}')

    try:
        with urllib.request.urlopen(req, timeout=config.timeout) as resp:
            raw = resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        detail = ''
        try:
            detail = e.read().decode('utf-8', errors='replace')[:500]
        except Exception:
            pass
        logger.warning("Provider '%s' HTTP %s: %s", config.name, e.code, detail)
        raise AIProviderError(config.name, f"HTTP {e.code}: {detail or e.reason}")
    except urllib.error.URLError as e:
        logger.warning("Provider '%s' URLError: %s", config.name, e.reason)
        raise AIProviderError(config.name, f"网络错误: {e.reason}")
    except Exception as e:  # noqa: BLE001 — 兜底
        logger.warning("Provider '%s' 未知错误: %s", config.name, e)
        raise AIProviderError(config.name, f"未知错误: {e}")

    # 解析响应
    try:
        data = json.loads(raw)
        # OpenAI 标准格式: choices[0].message.content
        choices = data.get('choices') or []
        if not choices:
            raise AIProviderError(config.name, f"响应无 choices: {raw[:200]}")
        content = choices[0].get('message', {}).get('content', '')
        if not content:
            raise AIProviderError(config.name, f"响应内容为空: {raw[:200]}")
        return content.strip()
    except (ValueError, KeyError, IndexError) as e:
        raise AIProviderError(config.name, f"响应解析失败: {e}; raw={raw[:200]}")
