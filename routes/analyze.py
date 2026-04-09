"""
POST /analyze 端点。

接收上传的采购公告文件（PDF / Word / HTML），
返回 AI 生成的投标可行性分析 JSON。

错误处理：
  - 文件过大（> 10MB）→ 400
  - 不支持的格式 → 415
  - 解析失败 / AI 超时等 → 500，附带用户友好的中文说明
"""

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from analysis.deepseek_client import call_deepseek
from analysis.prompt_builder import build_prompt
from parsers.detector import detect_format
from parsers.html_parser import parse_html
from parsers.pdf_parser import parse_pdf
from parsers.word_parser import parse_word

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB，超过此大小直接拒绝


@router.post("/analyze")
async def analyze_announcement(file: UploadFile) -> JSONResponse:
    """
    分析上传的采购公告，返回投标可行性决策简报。

    数据流：
        文件上传 → 格式检测 → 文本提取（含 OCR 回退）→ 提示词构建 → DeepSeek 分析 → JSON 返回

    Response 200: 分析成功
        {
            "verdict": "投" | "不投" | "谨慎投",
            "verdict_reason": str,
            "qualification_match": str,
            "qualifications": [...],
            "budget_score": 1-5,
            "budget_analysis": str,
            "competition_score": 1-5,
            "competition_analysis": str,
            "summary": str,
            "ocr_used": bool  ← 是否触发了 OCR（前端可据此显示提示）
        }
    """
    # ── 1. 文件大小检查 ──────────────────────────────────────────
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大（{len(file_bytes) // 1024 // 1024}MB），请上传 10MB 以下的文件。"
            "政府采购公告一般不超过 5MB，超大文件通常包含附件图片，可以尝试去掉附件后重新上传。",
        )

    # ── 2. 格式检测 ──────────────────────────────────────────────
    filename = file.filename or "unknown"
    try:
        fmt = detect_format(filename)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))

    # ── 3. 文本提取 ──────────────────────────────────────────────
    ocr_used = False

    try:
        if fmt == "pdf":
            # OCR 回退：检测到扫描件时 ocr_used 变为 True
            # 使用列表作为可变容器，以便在回调中修改外部变量
            ocr_flag = [False]

            def on_ocr_start(msg: str):
                ocr_flag[0] = True

            text = parse_pdf(file_bytes, progress_callback=on_ocr_start)
            ocr_used = ocr_flag[0]

        elif fmt == "word":
            text = parse_word(file_bytes)

        else:  # html
            text = parse_html(file_bytes)

    except ValueError as e:
        # 解析失败：文件损坏、加密、内容为空等
        raise HTTPException(status_code=400, detail=str(e))

    # ── 4. AI 分析 ───────────────────────────────────────────────
    try:
        messages = build_prompt(text)
        result = call_deepseek(messages)
    except ValueError as e:
        # API key 未配置、超时、JSON 解析失败等
        raise HTTPException(status_code=500, detail=str(e))

    # ── 5. 返回结果 ──────────────────────────────────────────────
    result["ocr_used"] = ocr_used  # 告知前端是否用了 OCR（方便显示进度提示）
    return JSONResponse(content=result)
