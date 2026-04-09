"""
Word 文档解析器（.docx）。
使用 python-docx 提取段落文本，同时处理表格内容（资质要求常以表格形式呈现）。
"""

import io

from parsers.pdf_parser import MAX_CHARS  # 复用同一截断长度


def parse_word(file_bytes: bytes) -> str:
    """
    从 Word (.docx) 字节流中提取文本。

    提取顺序：段落文本 → 表格单元格文本（表格里常有资质要求清单）

    Returns:
        提取的纯文本，截断到 MAX_CHARS 字符

    Raises:
        ValueError: 文件无法解析（损坏、格式不对等）
    """
    try:
        from docx import Document
    except ImportError:
        raise ValueError("python-docx 未安装，请运行：pip install python-docx")

    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"无法读取 Word 文件，请检查文件是否损坏。({e})")

    parts = []

    # 提取段落文本（正文、标题等）
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text.strip())

    # 提取表格内容（资质要求、技术参数表格）
    # 格式：每行合并为 "| 列1 | 列2 | ..."
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append("| " + " | ".join(cells) + " |")

    text = "\n".join(parts)

    if not text.strip():
        raise ValueError("Word 文件内容为空，请检查文件是否有效。")

    # 截断
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n[文档内容已截断，以上为前 8000 字]"

    return text.strip()
