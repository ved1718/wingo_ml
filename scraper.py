from __future__ import annotations

import re
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

NUMBER_RE = re.compile(r"\b\d+\b")
PERIOD_RE = re.compile(r"\b\d{6,}\b")


def _infer_color(number: int) -> str:
    # Common color rule used by many WinGo variants.
    return "green" if number % 2 else "red"


def _infer_size(number: int) -> str:
    return "big" if number >= 5 else "small"


def _extract_rows(payload: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload:
        text_blob = " ".join(str(v) for v in item.values())

        period_match = PERIOD_RE.search(text_blob)
        all_numbers = [int(x) for x in NUMBER_RE.findall(text_blob)]

        number = None
        for candidate in all_numbers:
            if 0 <= candidate <= 9:
                number = candidate
                break

        if not period_match or number is None:
            continue

        rows.append(
            {
                "period": period_match.group(0),
                "number": number,
                "color": _infer_color(number),
                "size": _infer_size(number),
            }
        )

        if len(rows) >= limit:
            break

    if len(rows) < limit:
        raise ValueError(
            f"Only extracted {len(rows)} periods. The website layout/API may have changed."
        )

    return rows


def fetch_wingo_history(url: str, limit: int = 50) -> list[dict[str, Any]]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            # Try to discover likely JSON responses from the app runtime.
            response_data: list[dict[str, Any]] = []

            def capture_response(response):
                if "application/json" not in (response.headers.get("content-type") or ""):
                    return
                try:
                    data = response.json()
                except Exception:
                    return
                if isinstance(data, dict):
                    for key in ("data", "list", "records", "rows", "result"):
                        value = data.get(key)
                        if isinstance(value, list):
                            response_data.extend(x for x in value if isinstance(x, dict))
                elif isinstance(data, list):
                    response_data.extend(x for x in data if isinstance(x, dict))

            page.on("response", capture_response)
            page.reload(wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(6000)

            rows = _extract_rows(response_data, limit=limit)
            return rows

        except PlaywrightTimeoutError as exc:
            raise RuntimeError("Timed out while loading the WinGo page.") from exc
        finally:
            browser.close()
