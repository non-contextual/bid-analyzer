"""
API 集成测试。
使用 httpx.AsyncClient 测试完整的 HTTP 请求/响应流程。
DeepSeek API 调用被 mock，不消耗真实额度。
"""

import io
import json
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# 测试用的模拟分析结果
MOCK_ANALYSIS = {
    "verdict": "投",
    "verdict_reason": "预算充足，技术参数通用",
    "qualification_match": "符合",
    "qualifications": [{"requirement": "营业执照", "status": "pass"}],
    "budget_score": 4,
    "budget_analysis": "预算合理",
    "competition_score": 4,
    "competition_analysis": "技术参数通用，竞争公平",
    "summary": "综合评估建议投标。",
}


@pytest.fixture
def app():
    from main import app
    return app


@pytest.fixture
def mock_deepseek():
    """patch call_deepseek，所有测试用 mock 结果，不真实调用 API"""
    with patch("routes.analyze.call_deepseek", return_value=MOCK_ANALYSIS) as m:
        yield m


def _make_pdf_bytes(text: str = "Procurement notice: budget 1 million yuan. Bidders must have business license and meet all qualification requirements.") -> bytes:
    """生成测试用 PDF 字节流"""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _make_docx_bytes() -> bytes:
    """生成测试用 docx 字节流"""
    from docx import Document
    doc = Document()
    doc.add_paragraph("采购公告，预算 50 万元，资质要求营业执照。")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ── 正常流程 ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_pdf_returns_brief(app, mock_deepseek):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        pdf_bytes = _make_pdf_bytes()
        resp = await client.post(
            "/analyze",
            files={"file": ("公告.pdf", pdf_bytes, "application/pdf")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"] in ("投", "不投", "谨慎投")
    assert "budget_score" in data


@pytest.mark.asyncio
async def test_upload_word_returns_brief(app, mock_deepseek):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        docx_bytes = _make_docx_bytes()
        resp = await client.post(
            "/analyze",
            files={"file": ("公告.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "verdict" in data


# ── 错误路径 ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_too_large_file_returns_400(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 生成 11MB 的假数据
        big_bytes = b"0" * (11 * 1024 * 1024)
        resp = await client.post(
            "/analyze",
            files={"file": ("big.pdf", big_bytes, "application/pdf")},
        )
    assert resp.status_code == 400
    assert "过大" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_unsupported_format_returns_415(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("photo.jpg", b"fake image data", "image/jpeg")},
        )
    assert resp.status_code == 415
    assert "不支持" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_api_error_returns_500_with_message(app):
    """DeepSeek API 失败时，返回 500 并附带用户友好的中文说明"""
    with patch("routes.analyze.call_deepseek", side_effect=ValueError("AI 分析超时")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            pdf_bytes = _make_pdf_bytes()
            resp = await client.post(
                "/analyze",
                files={"file": ("公告.pdf", pdf_bytes, "application/pdf")},
            )
    assert resp.status_code == 500
    assert "超时" in resp.json()["detail"]
