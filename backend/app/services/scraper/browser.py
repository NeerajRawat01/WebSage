from typing import Optional, Tuple

from playwright.async_api import async_playwright


async def render_page(
    url: str,
    user_agent: str,
    timeout_seconds: int = 15,
    max_bytes: int = 10 * 1024 * 1024,
) -> Tuple[str, int, Optional[str]]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()
        try:
            resp = await page.goto(url, wait_until="networkidle", timeout=timeout_seconds * 1000)
            final_url = page.url
            status_code = resp.status if resp else 0
            html = await page.content()
            if html and len(html.encode("utf-8")) > max_bytes:
                html = html.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
            return final_url, status_code, html
        finally:
            await context.close()
            await browser.close()


