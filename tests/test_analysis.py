"""
AI 分析层单元测试。
使用 mock 替代真实 API 调用，避免每次测试消耗 DeepSeek 额度。
"""

import json
from unittest.mock import MagicMock, patch

import pytest


# ── Prompt Builder ───────────────────────────────────────────────

class TestPromptBuilder:
    def test_valid_text_returns_messages(self):
        from analysis.prompt_builder import build_prompt
        text = "采购项目：服务器采购，预算 50 万元，要求营业执照。"
        messages = build_prompt(text)
        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert text in messages[1]["content"]

    def test_empty_text_raises(self):
        from analysis.prompt_builder import build_prompt
        with pytest.raises(ValueError, match="内容为空"):
            build_prompt("")

    def test_whitespace_only_raises(self):
        from analysis.prompt_builder import build_prompt
        with pytest.raises(ValueError, match="内容为空"):
            build_prompt("   \n  ")


# ── DeepSeek Client ──────────────────────────────────────────────

MOCK_VALID_RESPONSE = {
    "verdict": "谨慎投",
    "verdict_reason": "预算合理，但技术参数过于具体，可能是预定标",
    "qualification_match": "符合",
    "qualifications": [
        {"requirement": "营业执照（信息技术类）", "status": "pass"},
        {"requirement": "ISO 9001 认证", "status": "unknown"},
    ],
    "budget_score": 4,
    "budget_analysis": "50万元预算在行业内属中等偏上",
    "competition_score": 2,
    "competition_analysis": "技术参数指定了特定品牌型号，竞争风险较高",
    "summary": "预算尚可，但高度定制的技术参数暗示可能已有意向供应商，建议谨慎评估。",
}


class TestDeepSeekClient:
    def _make_mock_response(self, content_dict: dict, status_code: int = 200):
        """构建模拟的 httpx 响应对象"""
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(content_dict)}}]
        }
        return mock_resp

    def test_valid_response_returns_dict(self):
        from analysis.deepseek_client import call_deepseek
        messages = [{"role": "user", "content": "test"}]

        with patch("analysis.deepseek_client.httpx.post") as mock_post:
            mock_post.return_value = self._make_mock_response(MOCK_VALID_RESPONSE)
            result = call_deepseek(messages)

        assert result["verdict"] == "谨慎投"
        assert result["budget_score"] == 4
        assert len(result["qualifications"]) == 2

    def test_timeout_raises_friendly_error(self):
        import httpx
        from analysis.deepseek_client import call_deepseek

        with patch("analysis.deepseek_client.httpx.post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("timeout")
            with pytest.raises(ValueError, match="超时"):
                call_deepseek([{"role": "user", "content": "test"}])

    def test_invalid_json_response_raises_friendly_error(self):
        from analysis.deepseek_client import call_deepseek

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "这不是 JSON 格式的内容"}}]
        }

        with patch("analysis.deepseek_client.httpx.post", return_value=mock_resp):
            with pytest.raises(ValueError, match="无法解析"):
                call_deepseek([{"role": "user", "content": "test"}])

    def test_missing_api_key_raises(self, monkeypatch):
        from analysis.deepseek_client import call_deepseek
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        # 也确保 os.getenv 返回 None
        with patch("analysis.deepseek_client.os.getenv", return_value=None):
            with pytest.raises(ValueError, match="API key"):
                call_deepseek([{"role": "user", "content": "test"}])

    def test_default_values_filled_for_missing_fields(self):
        """AI 返回不完整 JSON 时，默认值应填充缺失字段"""
        from analysis.deepseek_client import call_deepseek

        partial_response = {"verdict": "投"}  # 只有 verdict，其他字段缺失

        with patch("analysis.deepseek_client.httpx.post") as mock_post:
            mock_post.return_value = self._make_mock_response(partial_response)
            result = call_deepseek([{"role": "user", "content": "test"}])

        assert result["verdict"] == "投"
        assert "budget_score" in result  # 默认值应被填充
        assert "qualifications" in result
