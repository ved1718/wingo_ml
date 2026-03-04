# WinGo 1M Trend Dashboard (Educational)

This project provides a small web app that:

1. Attempts to scrape the latest WinGo 1M periods from the public website.
2. Extracts color (`green`/`red`) and size (`big`/`small`) labels from past rounds.
3. Trains simple machine-learning style sequence models on the most recent 50 periods.
4. Shows a probability forecast for the next period.

> ⚠️ **Important:** Lottery/wingo outcomes are usually designed to be random. This tool is for educational data analysis only and cannot guarantee future outcomes.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python app.py
```

Open: `http://127.0.0.1:5000`

## Notes

- The target site is a dynamic SPA and may change selectors or block automation.
- If scraping fails, the app will return an actionable error.
