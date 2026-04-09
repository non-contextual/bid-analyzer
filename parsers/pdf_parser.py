"""
PDF 解析器。

流程：
  1. 用 PyMuPDF 提取文本（适用于数字 PDF）
  2. 如果提取结果太短（< 50 字符），判定为扫描件，转 OCR
  3. OCR 使用 Tesseract，处理每一页图像

文本截断：超过 MAX_CHARS 字符时取前段，避免超出 AI 上下文窗口。
"""

import io
from typing import Callable

import fitz  # PyMuPDF

MAX_CHARS = 8000  # 大约 4000 个中文字，覆盖大多数公告关键信息
OCR_THRESHOLD = 50  # 提取文本少于此字符数时判定为扫描件


def parse_pdf(
    file_bytes: bytes,
    progress_callback: Callable[[str], None] | None = None,
) -> str:
    """
    从 PDF 字节流中提取文本。

    Args:
        file_bytes: PDF 文件的原始字节
        progress_callback: 可选的进度回调，传入状态字符串（用于通知前端 OCR 进度）

    Returns:
        提取的纯文本，截断到 MAX_CHARS 字符

    Raises:
        ValueError: 文件无法打开（加密、损坏等）
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"无法读取 PDF 文件，请检查文件是否损坏或加密。({e})")

    # 第一步：尝试直接提取文本
    text = ""
    for page in doc:
        text += page.get_text()

    # 第二步：文本太短，判定为扫描件，转 OCR
    if len(text.strip()) < OCR_THRESHOLD:
        if progress_callback:
            progress_callback("检测到扫描件 PDF，正在 OCR 识别文字，大文件可能需要 1-2 分钟...")
        text = _ocr_pdf(doc)

    doc.close()

    # 截断：超长文档只取前 MAX_CHARS 字符
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n[文档内容已截断，以上为前 8000 字]"

    return text.strip()


def _ocr_pdf(doc: fitz.Document) -> str:
    """
    对 PDF 每页做 OCR。
    Tesseract 需要本地安装：
        Windows: https://github.com/UB-Mannheim/tesseract/wiki
        macOS:   brew install tesseract tesseract-lang
        Linux:   apt install tesseract-ocr tesseract-ocr-chi-sim
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise ValueError(
            "OCR 模块未安装，请运行：pip install pytesseract Pillow\n"
            "同时需要安装 Tesseract：https://github.com/UB-Mannheim/tesseract/wiki"
        )

    texts = []
    for page_num, page in enumerate(doc):
        # 渲染为高分辨率图像（2x 放大提高 OCR 准确率）
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))

        # chi_sim = 简体中文，eng = 英文；两者都要以处理混排公告
        page_text = pytesseract.image_to_string(img, lang="chi_sim+eng")
        texts.append(page_text)

        # OCR 可能很慢，每处理 5 页截断一次以控制总时间
        # （前几页包含关键信息：资质要求、预算、技术参数）
        if page_num >= 4:  # 0-indexed，即最多处理前 5 页
            texts.append("\n[扫描件过长，已处理前 5 页]")
            break

    return "\n".join(texts)
