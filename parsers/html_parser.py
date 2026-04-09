"""
HTML 解析器。
去掉 script/style 标签后提取纯文本，保留换行结构。
用于处理直接从政府采购网复制的 HTML 页面。
"""

from parsers.pdf_parser import MAX_CHARS  # 复用同一截断长度


def parse_html(content: str | bytes) -> str:
    """
    从 HTML 字符串或字节流中提取纯文本。

    Args:
        content: HTML 内容（字符串或 bytes）

    Returns:
        提取的纯文本，截断到 MAX_CHARS 字符

    Raises:
        ValueError: HTML body 为空
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ValueError("beautifulsoup4 未安装，请运行：pip install beautifulsoup4")

    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    soup = BeautifulSoup(content, "html.parser")

    # 移除脚本和样式，它们不含有效信息
    for tag in soup(["script", "style", "meta", "link", "noscript"]):
        tag.decompose()

    # get_text 用换行分隔，strip 去除多余空白
    text = soup.get_text(separator="\n")

    # 合并连续空行（HTML 解析后常有大量空行）
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]  # 去掉空行
    text = "\n".join(lines)

    if not text.strip():
        raise ValueError("HTML 内容为空，请检查上传的文件是否包含公告正文。")

    # 截断
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n[文档内容已截断，以上为前 8000 字]"

    return text.strip()
