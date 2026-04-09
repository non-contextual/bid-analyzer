"""
pytest 全局 fixtures。
"""

import pytest


@pytest.fixture(autouse=True)
def fake_deepseek_api_key(monkeypatch):
    """为所有测试提供假 API key，避免 'API key 未配置' 错误干扰 mock 测试。
    test_missing_api_key_raises 会自己用 monkeypatch.delenv 覆盖掉这个值。
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-fake-key-for-testing")
