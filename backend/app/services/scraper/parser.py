from typing import Optional, Tuple

from selectolax.parser import HTMLParser
from readability import Document


def extract_title_and_meta(html: str) -> Tuple[Optional[str], Optional[str]]:
    if not html:
        return None, None
    tree = HTMLParser(html)
    title = None
    meta_desc = None

    # Title
    # Prefer og:title, then <title>, then first H1
    og_title = tree.css_first('meta[property="og:title"], meta[name="og:title"]')
    if og_title:
        t = og_title.attributes.get("content")
        if t:
            title = t.strip() or None
    if not title:
        title_node = tree.css_first("title")
        if title_node and title_node.text():
            title = title_node.text().strip() or None
    if not title:
        h1 = tree.css_first("h1")
        if h1 and h1.text():
            title = h1.text().strip() or None

    # Meta description
    meta_node = tree.css_first('meta[name="description"], meta[name="Description"], meta[name="og:description"], meta[property="og:description"]')
    if meta_node:
        content = meta_node.attributes.get("content")
        if content:
            meta_desc = content.strip() or None

    return title, meta_desc


def extract_main_text(html: str) -> Optional[str]:
    if not html:
        return None
    try:
        doc = Document(html)
        summary_html = doc.summary(html_partial=True)
        tree = HTMLParser(summary_html)
        # Remove script/style/nav
        for sel in ("script", "style", "nav", "footer", "header"):  # best-effort cleanup
            for n in tree.css(sel):
                n.decompose()
        text = tree.text(separator=" ")
        text = " ".join(text.split())
        return text if text else None
    except Exception:
        return None


