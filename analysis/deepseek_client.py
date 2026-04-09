"""
DeepSeek API 客户端。

使用 JSON mode 确保输出格式稳定可解析。
错误处理：API 超时、限流、格式错误都返回友好的中文错误消息，不暴露内部 stack trace。
"""

import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()  # 从 .env 文件读取 DEEPSEEK_API_KEY

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
TIMEOUT_SECONDS = 60  # DeepSeek 响应通常 5-15s，60s 是充足的安全边界


def call_deepseek(messages: list[dict]) -> dict:
    """
    调用 DeepSeek API，返回解析好的 JSON 分析结果。

    Args:
        messages: 由 prompt_builder.build_prompt() 构建的消息列表

    Returns:
        解析好的 dict，包含 verdict/budget_score/competition_score 等字段

    Raises:
        ValueError: API key 未配置、响应超时、JSON 解析失败等，均附带用户友好的中文说明
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "DeepSeek API key 未配置。请创建 .env 文件并填入：\n"
            "DEEPSEEK_API_KEY=your_api_key_here\n"
            "在 https://platform.deepseek.com/ 申请免费额度。"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        # JSON mode：强制 AI 输出合法 JSON，避免自由格式导致解析失败
        "response_format": {"type": "json_object"},
        "temperature": 0.1,  # 低温度 = 更稳定、更少随机性，适合结构化分析
        "max_tokens": 1500,  # 足够输出完整分析
    }

    try:
        response = httpx.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
    except httpx.TimeoutException:
        raise ValueError("AI 分析超时（超过 60 秒），请稍后重试。如果公告很长，可以尝试压缩文件后重新上传。")
    except httpx.RequestError as e:
        raise ValueError(f"网络连接失败，请检查网络后重试。({e})")

    # HTTP 错误处理
    if response.status_code == 401:
        raise ValueError("API key 无效或已过期，请检查 .env 文件中的 DEEPSEEK_API_KEY。")
    if response.status_code == 429:
        raise ValueError("API 请求频率超限，请稍等几秒后重试。")
    if response.status_code != 200:
        raise ValueError(f"AI 服务返回错误（状态码 {response.status_code}），请稍后重试。")

    # 解析响应
    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise ValueError(
            f"AI 返回了无法解析的格式，请重试。如果持续出现，请联系开发者。({e})"
        )

    # 基础字段校验：确保关键字段存在（优雅降级：缺失字段用默认值填充）
    result.setdefault("verdict", "无法判断")
    result.setdefault("verdict_reason", "分析结果不完整，请重试")
    result.setdefault("qualification_match", "无法判断")
    result.setdefault("qualifications", [])
    result.setdefault("budget_score", 3)
    result.setdefault("budget_analysis", "预算信息不足，无法评估")
    result.setdefault("competition_score", 3)
    result.setdefault("competition_analysis", "竞争信息不足，无法评估")
    result.setdefault("summary", "分析结果不完整，建议手动审阅公告")

    return result
