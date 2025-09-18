import re
from typing import Dict, List, Optional

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


