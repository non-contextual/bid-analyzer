"""
文件格式检测器。
根据文件名后缀判断文件类型，返回对应的解析器标识符。
"""


def detect_format(filename: str) -> str:
    """
    根据文件名后缀判断文件类型。

    返回值:
        "pdf"  - PDF 文件
        "word" - Word 文件 (.doc / .docx)
        "html" - HTML 文件 (.html / .htm)

    如果格式不支持，抛出 ValueError。
    """
    name = filename.lower()

    if name.endswith(".pdf"):
        return "pdf"

    if name.endswith(".docx") or name.endswith(".doc"):
        return "word"

    if name.endswith(".html") or name.endswith(".htm"):
        return "html"

    # 不支持的格式：向上抛出，由 API 层转成 415 错误
    raise ValueError(f"不支持的文件格式：{filename}。请上传 PDF、Word 或 HTML 文件。")
