import re
from typing import Dict, List, Optional
from selectolax.parser import HTMLParser
import json

import phonenumbers


EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

SOCIAL_DOMAINS = {
    "linkedin": ["linkedin.com"],
    "twitter": ["twitter.com", "x.com"],
    "facebook": ["facebook.com"],
    "youtube": ["youtube.com", "youtu.be"],
    "instagram": ["instagram.com"],
    "tiktok": ["tiktok.com"],
}


def extract_emails(text: str) -> List[str]:
    candidates = set(m.group(0).lower() for m in EMAIL_REGEX.finditer(text or ""))
    # Filter obvious placeholders
    filtered = [e for e in candidates if not any(x in e for x in ("example.com", "test@", "no-reply@"))]
    return sorted(filtered)


def extract_phone_numbers(text: str, default_region: str = "US") -> List[str]:
    if not text:
        return []
    found: List[str] = []
    for match in phonenumbers.PhoneNumberMatcher(text, default_region):
        try:
            num = phonenumbers.parse(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164))
            if phonenumbers.is_valid_number(num):
                formatted = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
                found.append(formatted)
        except Exception:
            continue
    # Dedupe while preserving order
    seen = set()
    deduped: List[str] = []
    for n in found:
        if n not in seen:
            seen.add(n)
            deduped.append(n)
    return deduped


def extract_social_links(html: str) -> Dict[str, Optional[str]]:
    # Simple href scan to avoid full DOM parsing for now
    result: Dict[str, Optional[str]] = {k: None for k in SOCIAL_DOMAINS.keys()}
    if not html:
        return result
    lower = html.lower()
    for platform, domains in SOCIAL_DOMAINS.items():
        for d in domains:
            idx = lower.find(d)
            if idx != -1:
                # Find start of URL
                start = lower.rfind("http", 0, idx)
                if start == -1:
                    continue
                # Find end of URL (quote or whitespace)
                end = idx
                while end < len(lower) and lower[end] not in ('"', "'", ' ', '\\n', '\\r', '<'):  # crude
                    end += 1
                url = html[start:end]
                result[platform] = url
                break
    return result


def extract_location(text: str) -> Optional[str]:
    """
    Best-effort location sniffing from free text.
    Targets common Indian address patterns like "Sector 63, Noida" first,
    then falls back to detecting a known city mention.
    """
    if not text:
        return None
    try:
        # Generic address-looking line: contains commas or keywords like sector/road/street/avenue, etc.
        line_regex = re.compile(r"((?:sector|road|street|st\.|ave\.|avenue|block|phase|park|plaza|tower|suite|floor|#)\s*[^\n,]{0,50}(?:,\s*[^\n]+)+)", re.IGNORECASE)
        m = line_regex.search(text)
        if m:
            return m.group(1).strip()[:200]
    except Exception:
        return None
    return None


def extract_dom_location(html: str) -> Optional[str]:
    """
    Deterministic address extraction from DOM:
    - Prefer <address> tags
    - Search footer for address-like lines
    - Search elements with class/id indicating address/location/contact/office/hq
    Returns a concise single-line string if found.
    """
    if not html:
        return None
    try:
        tree = HTMLParser(html)

        def clean(text: str) -> str:
            t = " ".join((text or "").split())
            return t.strip()

        # 1) JSON-LD schema.org
        for node in tree.css('script[type="application/ld+json"]'):
            try:
                data = json.loads(node.text() or "{}")
            except Exception:
                continue
            def pick_addr(obj) -> Optional[str]:
                if not isinstance(obj, dict):
                    return None
                addr = obj.get("address")
                if isinstance(addr, dict):
                    parts = [
                        addr.get("streetAddress"),
                        addr.get("addressLocality"),
                        addr.get("addressRegion"),
                        addr.get("postalCode"),
                        addr.get("addressCountry"),
                    ]
                    line = ", ".join([p for p in parts if p])
                    return line or None
                return None
            candidate = None
            if isinstance(data, list):
                for item in data:
                    candidate = pick_addr(item) or candidate
            else:
                candidate = pick_addr(data)
            if candidate:
                return candidate[:200]

        # 2) <address>
        for node in tree.css("address"):
            t = clean(node.text())
            if len(t) >= 6:
                return t[:200]

        # Helper: check if a node looks like an address by regex
        def find_address_like(root) -> Optional[str]:
            # Generic address-looking lines: look for separators/keywords commonly used in addresses
            line_regex = re.compile(r"((?:sector|road|street|st\.|ave\.|avenue|block|phase|park|plaza|tower|suite|floor|#)\s*[^\n,]{0,50}(?:,\s*[^\n]+)+)", re.IGNORECASE)
            # Scan text chunks of candidate nodes
            for node in root.css("p, li, span, div"):
                t = clean(node.text())
                if not t:
                    continue
                m = line_regex.search(t)
                if m:
                    cand = m.group(1).strip()
                    if 6 <= len(cand) <= 200:
                        return cand
            return None

        # 3) Footer section
        for footer in tree.css("footer"):
            t = find_address_like(footer)
            if t:
                return t

        # 4) Elements with address-like class/id or labels
        selectors = [
            "[class*='address']",
            "[id*='address']",
            "[class*='location']",
            "[id*='location']",
            "[class*='contact']",
            "[id*='contact']",
            "[class*='office']",
            "[id*='office']",
            "[class*='hq']",
            "[id*='hq']",
            "[class*='footer']",
            "[id*='footer']",
        ]
        for sel in selectors:
            for node in tree.css(sel):
                t = find_address_like(node)
                if t:
                    return t
                # Fallback to raw text if moderately long and not just links
                raw = clean(node.text())
                if raw and 6 <= len(raw) <= 200:
                    return raw
    except Exception:
        return None
    return None


