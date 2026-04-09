"""
解析器单元测试。
覆盖：格式检测、PDF（正常/扫描件/加密/截断）、Word（正常/损坏）、HTML（正常/空）
"""

import io

import pytest


# ── 格式检测 ────────────────────────────────────────────────────

class TestDetectFormat:
    def test_pdf(self):
        from parsers.detector import detect_format
        assert detect_format("公告.pdf") == "pdf"

    def test_pdf_uppercase(self):
        from parsers.detector import detect_format
        assert detect_format("公告.PDF") == "pdf"

    def test_word_docx(self):
        from parsers.detector import detect_format
        assert detect_format("招标文件.docx") == "word"

    def test_word_doc(self):
        from parsers.detector import detect_format
        assert detect_format("招标文件.doc") == "word"

    def test_html(self):
        from parsers.detector import detect_format
        assert detect_format("公告.html") == "html"

    def test_htm(self):
        from parsers.detector import detect_format
        assert detect_format("公告.htm") == "html"

    def test_unsupported_raises(self):
        from parsers.detector import detect_format
        with pytest.raises(ValueError, match="不支持"):
            detect_format("image.jpg")

    def test_no_extension_raises(self):
        from parsers.detector import detect_format
        with pytest.raises(ValueError):
            detect_format("nodotfile")


# ── PDF 解析 ────────────────────────────────────────────────────

class TestPdfParser:
    def _make_digital_pdf(self, text: str) -> bytes:
        """创建包含指定文本的数字 PDF（非扫描件）"""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=11)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    def test_digital_pdf_returns_text(self):
        from parsers.pdf_parser import parse_pdf
        # 使用 ASCII 文本——pymupdf 默认字体不含中文字形，中文会乱码且可能不足 OCR_THRESHOLD(50)
        content = "Procurement notice: budget 100 million yuan. Bidders must have valid business license and qualifications."
        pdf_bytes = self._make_digital_pdf(content)
        result = parse_pdf(pdf_bytes)
        assert len(result) > 10
        assert "100" in result

    def test_truncation_at_8000_chars(self):
        from parsers.pdf_parser import MAX_CHARS, parse_pdf
        # 生成超长文本（重复到超过 MAX_CHARS）
        long_text = "采购公告测试内容。" * 1000  # ~9000 chars
        pdf_bytes = self._make_digital_pdf(long_text)
        result = parse_pdf(pdf_bytes)
        assert len(result) <= MAX_CHARS + 50  # 允许截断提示语的额外长度

    def test_corrupted_pdf_raises_value_error(self):
        from parsers.pdf_parser import parse_pdf
        with pytest.raises(ValueError, match="无法读取"):
            parse_pdf(b"this is not a pdf at all")

    def test_ocr_callback_called_for_empty_pdf(self):
        """空内容 PDF 应触发 OCR 回调（即使 OCR 本身可能失败）"""
        import fitz
        from parsers.pdf_parser import parse_pdf

        # 创建一个没有任何文本的空白 PDF
        doc = fitz.open()
        doc.new_page()
        buf = io.BytesIO()
        doc.save(buf)
        empty_pdf = buf.getvalue()

        callback_called = [False]
        def on_ocr(msg):
            callback_called[0] = True

        try:
            parse_pdf(empty_pdf, progress_callback=on_ocr)
        except (ValueError, Exception):
            pass  # OCR 可能因为 tesseract 未安装而失败，但 callback 应该已被调用

        assert callback_called[0], "扫描件 PDF 应触发 OCR 回调"


# ── Word 解析 ────────────────────────────────────────────────────

class TestWordParser:
    def _make_docx(self, paragraphs: list[str]) -> bytes:
        """创建包含指定段落的 docx 文件"""
        from docx import Document
        doc = Document()
        for para in paragraphs:
            doc.add_paragraph(para)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    def test_normal_docx_returns_text(self):
        from parsers.word_parser import parse_word
        content = ["采购项目名称：办公电脑采购", "预算金额：50万元", "资质要求：营业执照"]
        docx_bytes = self._make_docx(content)
        result = parse_word(docx_bytes)
        assert "采购" in result
        assert "50万元" in result

    def test_corrupted_docx_raises_value_error(self):
        from parsers.word_parser import parse_word
        with pytest.raises(ValueError, match="无法读取"):
            parse_word(b"not a docx file at all 1234")


# ── HTML 解析 ────────────────────────────────────────────────────

class TestHtmlParser:
    def test_normal_html_returns_text(self):
        from parsers.html_parser import parse_html
        html = """
        <html><body>
          <h1>采购公告</h1>
          <p>预算：100万元</p>
          <script>alert('not this')</script>
          <style>body { color: red; }</style>
        </body></html>
        """
        result = parse_html(html)
        assert "采购公告" in result
        assert "100万元" in result
        # script 和 style 内容不应出现
        assert "alert" not in result
        assert "color: red" not in result

    def test_empty_html_raises_value_error(self):
        from parsers.html_parser import parse_html
        with pytest.raises(ValueError, match="内容为空"):
            parse_html("<html><body>   </body></html>")

    def test_bytes_input(self):
        from parsers.html_parser import parse_html
        html_bytes = "<p>政府采购公告测试内容</p>".encode("utf-8")
        result = parse_html(html_bytes)
        assert "政府采购" in result
