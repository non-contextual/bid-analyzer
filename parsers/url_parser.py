"""
网页链接解析器。
用 httpx 抓取页面，再交给 html_parser 提取正文。
"""

import httpx

from parsers.html_parser import parse_html

FETCH_TIMEOUT = 30  # 秒


def parse_url(url: str) -> str:
    """
    抓取网页并提取正文文本。

    Args:
        url: 公告页面的 HTTP/HTTPS 链接

    Returns:
        提取的纯文本

    Raises:
        ValueError: URL 格式错误、无法访问、内容为空等
    """
    if not url.startswith(("http://", "https://")):
        raise ValueError("链接格式不正确，请以 http:// 或 https:// 开头。")

    headers = {
        # 部分政府网站会拦截没有 User-Agent 的请求
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        response = httpx.get(
            url,
            headers=headers,
            follow_redirects=True,
            timeout=FETCH_TIMEOUT,
        )
    except httpx.TimeoutException:
        raise ValueError(f"抓取页面超时（超过 {FETCH_TIMEOUT} 秒），请检查链接是否可以正常访问。")
    except httpx.RequestError as e:
        raise ValueError(f"无法连接到该地址，请检查链接是否有效。({e})")

    if response.status_code != 200:
        raise ValueError(
            f"页面返回错误（状态码 {response.status_code}），"
            "请检查链接是否有效，或尝试直接下载文件后上传。"
        )

    content_type = response.headers.get("content-type", "")
    if "pdf" in content_type:
        raise ValueError("该链接直接指向 PDF 文件，请下载后使用「上传文件」功能分析。")

    return parse_html(response.content)
