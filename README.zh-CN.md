# tender-ai

> 其他语言：[English](./README.md) · 简体中文

上传政府/学校采购公告，AI 帮你判断值不值得投标。

输出一份一页纸的决策简报：**投 / 不投 / 谨慎投**，附资质核查清单、预算吸引力评分、竞争密度评分。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API key
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY（在 https://platform.deepseek.com/ 申请）

# 启动
uvicorn main:app --reload --port 8000
```

浏览器打开 `http://localhost:8000`，拖入公告文件即可。

## 支持格式

| 格式 | 说明 |
|------|------|
| PDF | 数字 PDF 直接提取文本；扫描件自动 OCR（需安装 Tesseract） |
| Word | `.docx` / `.doc` |
| HTML | 直接粘贴公告网页 |

文件大小限制：10MB

## 分析输出

```json
{
  "verdict": "谨慎投",
  "verdict_reason": "预算合理，但技术参数过于具体",
  "qualification_match": "符合",
  "qualifications": [
    { "requirement": "营业执照（信息技术类）", "status": "pass" },
    { "requirement": "ISO 9001 认证", "status": "unknown" }
  ],
  "budget_score": 4,
  "budget_analysis": "50万元预算在行业内属中等偏上",
  "competition_score": 2,
  "competition_analysis": "技术参数指定了特定品牌型号，竞争风险较高",
  "summary": "预算尚可，但高度定制的技术参数暗示可能已有意向供应商，建议谨慎评估。"
}
```

## OCR 安装（扫描件支持）

```bash
# Windows
# 下载安装包：https://github.com/UB-Mannheim/tesseract/wiki
# 安装时勾选 Chinese Simplified 语言包

# macOS
brew install tesseract tesseract-lang

# Linux
apt install tesseract-ocr tesseract-ocr-chi-sim
```

## 运行测试

```bash
pytest tests/ -v
```

## 技术栈

- **后端**：FastAPI + uvicorn
- **PDF 解析**：PyMuPDF + Tesseract OCR
- **Word 解析**：python-docx
- **AI 分析**：DeepSeek API（JSON mode）
- **前端**：单页 HTML，无框架依赖

## 环境变量

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（必填） |

## 许可

MIT
