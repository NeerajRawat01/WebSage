from datetime import datetime, timezone
import os

from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

from app.core.security import verify_bearer_token
from app.core.config import (
    SCRAPER_TIMEOUT_SECONDS,
    SCRAPER_MAX_REDIRECTS,
    SCRAPER_USER_AGENT,
    PLAYWRIGHT_ENABLED,
    PLAYWRIGHT_TIMEOUT_SECONDS,
    AI_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from app.services.scraper.guard import validate_url_and_resolve
from app.services.scraper.robots import can_fetch
from app.services.scraper.fetcher import fetch_url
from app.services.scraper.parser import extract_title_and_meta
from app.services.scraper.browser import render_page
from app.services.scraper.extract_contact import (
    extract_emails,
    extract_phone_numbers,
    extract_social_links,
)
from app.services.scraper.parser import extract_main_text
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.gemini_provider import GeminiProvider
from .schemas import AnalyzeRequest, AnalyzeResponse, CompanyInfoSchema


router = APIRouter(prefix="/analyze", tags=["analyze"]) 


@router.post("", response_model=AnalyzeResponse, dependencies=[Depends(verify_bearer_token)])
async def analyze_endpoint(payload: AnalyzeRequest, rate_limited: None = Depends(RateLimiter(times=10, seconds=60))):
    # 1) SSRF guard + resolve
    normalized_url, _ = validate_url_and_resolve(str(payload.url))

    # 2) robots.txt check (fail-open policy can be tuned later)
    if not can_fetch(SCRAPER_USER_AGENT, normalized_url):
        now = datetime.now(timezone.utc)
        return AnalyzeResponse(
            url=normalized_url,
            analysis_timestamp=now,
            company_info=CompanyInfoSchema(),
            extracted_answers=[],
        )

    # 3) Fetch HTML (we will parse minimal info)
    try:
        final_url, status_code, html = await fetch_url(
            normalized_url,
            user_agent=SCRAPER_USER_AGENT,
            timeout_seconds=SCRAPER_TIMEOUT_SECONDS,
            max_redirects=SCRAPER_MAX_REDIRECTS,
        )
    except Exception:
        final_url = normalized_url
        status_code = 0
        html = None

    # Fallback to Playwright if no HTML or very short content and enabled
    if (not html or len(html) < 200) and PLAYWRIGHT_ENABLED:
        try:
            final_url, status_code, html = await render_page(
                normalized_url,
                user_agent=SCRAPER_USER_AGENT,
                timeout_seconds=PLAYWRIGHT_TIMEOUT_SECONDS,
            )
        except Exception:
            pass

    # 4) Minimal parse for title/meta and contact info
    company = CompanyInfoSchema()
    if html:
        title, meta = extract_title_and_meta(html)
        if title:
            company.unique_selling_proposition = title
        if meta:
            company.core_products_services = [meta]

        # Contact and socials (best-effort)
        emails = extract_emails(html)
        phones = extract_phone_numbers(html)
        socials = extract_social_links(html)
        if emails or phones or any(socials.values()):
            company.contact_info = {
                "email": emails[0] if emails else None,
                "phone": phones[0] if phones else None,
                "social_media": socials,
            }

        # 5) Main text extraction and AI inference (if key provided)
        main_text = extract_main_text(html)
        print(f"[Analyze] main_text length: {len(main_text) if main_text else 0}")
        answers = []
        if main_text:
            try:
                print(
                    f"[Analyze] AI_PROVIDER={AI_PROVIDER} has_openai={bool(OPENAI_API_KEY)} has_gemini={bool(os.getenv('GEMINI_API_KEY'))}"
                )
                if AI_PROVIDER == "openai" and OPENAI_API_KEY:
                    ai = OpenAIProvider(model=OPENAI_MODEL)
                    print("[Analyze] Using OpenAI provider")
                elif AI_PROVIDER == "gemini" and os.getenv("GEMINI_API_KEY"):
                    ai = GeminiProvider(os.getenv("GEMINI_MODEL", "gemini-1.5-pro"))
                    print("[Analyze] Using Gemini provider")
                else:
                    ai = None

                if ai:
                    inferred = await ai.infer_company_attributes(main_text)
                    print(f"[Analyze] Inferred attributes: {inferred}")
                    company.industry = inferred.get("industry")
                    company.company_size = inferred.get("company_size")
                    company.location = inferred.get("location")
                    company.target_audience = inferred.get("target_audience")

                    if payload.questions:
                        answers = await ai.answer_questions(main_text, payload.questions)
                        print(f"[Analyze] Answered {len(answers)} questions")
            except Exception as e:
                print(f"[Analyze] AI inference error: {e}")

    now = datetime.now(timezone.utc)
    print(f"Analysis completed for {final_url} at {now}")
    print(f"Company info: {company}")
    return AnalyzeResponse(
        url=final_url,
        analysis_timestamp=now,
        company_info=company,
        extracted_answers=answers,
    )