# tender-ai

> Read this in: English · [简体中文](./README.zh-CN.md)

Upload a government or school procurement notice. AI tells you whether it's worth bidding.

The output is a one-page decision brief: **Bid / Don't bid / Bid with caution**, with a qualifications checklist, a budget attractiveness score, and a competitive density score.

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env, fill in DEEPSEEK_API_KEY (apply at https://platform.deepseek.com/)

# Run
uvicorn main:app --reload --port 8000
```

Open `http://localhost:8000` in a browser and drop in the notice file.

## Supported formats

| Format | Notes |
|--------|-------|
| PDF | Digital PDFs are extracted directly; scanned PDFs use OCR (requires Tesseract) |
| Word | `.docx` / `.doc` |
| HTML | Paste the notice page directly |

File size limit: 10 MB.

## Analysis output

```json
{
  "verdict": "Bid with caution",
  "verdict_reason": "Budget is reasonable, but technical specs are unusually specific",
  "qualification_match": "Pass",
  "qualifications": [
    { "requirement": "Business license (IT category)", "status": "pass" },
    { "requirement": "ISO 9001 certification", "status": "unknown" }
  ],
  "budget_score": 4,
  "budget_analysis": "500K RMB budget is above industry average",
  "competition_score": 2,
  "competition_analysis": "Specs name a specific brand and model, suggesting a preferred supplier may already be in mind",
  "summary": "Budget is acceptable, but heavily customized technical specs hint at a likely incumbent. Evaluate carefully before bidding."
}
```

## OCR setup (for scanned PDFs)

```bash
# Windows
# Installer: https://github.com/UB-Mannheim/tesseract/wiki
# Check the Chinese Simplified language pack during install

# macOS
brew install tesseract tesseract-lang

# Linux
apt install tesseract-ocr tesseract-ocr-chi-sim
```

## Tests

```bash
pytest tests/ -v
```

## Stack

- **Backend**: FastAPI + uvicorn
- **PDF parsing**: PyMuPDF + Tesseract OCR
- **Word parsing**: python-docx
- **AI analysis**: DeepSeek API (JSON mode)
- **Frontend**: Single-page HTML, no framework

## Environment variables

| Variable | Notes |
|----------|-------|
| `DEEPSEEK_API_KEY` | DeepSeek API key (required) |

## License

MIT
