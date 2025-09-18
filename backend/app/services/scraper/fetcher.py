from typing import Optional, Tuple

import httpx


async def fetch_url(
    url: str,
    user_agent: str,
    timeout_seconds: int,
    max_redirects: int,
    max_bytes: int = 10 * 1024 * 1024,
) -> Tuple[str, int, Optional[str]]:
    """Fetch URL with sane defaults. Returns (final_url, status_code, text or None).

    Caps response body to max_bytes to avoid huge downloads.
    """
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, br",
        "Connection": "keep-alive",
    }

    limits = httpx.Limits(max_redirects=max_redirects)
    timeout = httpx.Timeout(timeout_seconds)

    async with httpx.AsyncClient(
        headers=headers,
        http2=True,
        follow_redirects=True,
        limits=limits,
        timeout=timeout,
    ) as client:
        resp = await client.get(url)
        final_url = str(resp.url)
        status_code = resp.status_code
        content = resp.content[:max_bytes]
        try:
            text = content.decode(resp.encoding or "utf-8", errors="replace")
        except Exception:
            text = None
        return final_url, status_code, text


