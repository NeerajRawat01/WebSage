from datetime import datetime, timezone
from typing import List
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
from .schemas import AnalyzeRequest, AnalyzeResponse, CompanyInfoSchema, AnalysisSummary, ContactInfoSchema, SocialMedia, QAItem
from db.db import get_db
from app.features.analysis.models import AnalysisSession as AnalysisSessionModel, PageSnapshot as PageSnapshotModel
from app.features.company.models import CompanyInfo as CompanyInfoModel
from app.features.contact.models import ContactInfo as ContactInfoModel
from app.features.qa.models import ExtractedAnswer as ExtractedAnswerModel
import uuid


router = APIRouter(prefix="/analyze", tags=["analyze"]) 


@router.post("", response_model=AnalyzeResponse, dependencies=[Depends(verify_bearer_token)])
async def analyze_endpoint(
    payload: AnalyzeRequest,
    rate_limited: None = Depends(RateLimiter(times=10, seconds=60)),
    db: Session = Depends(get_db),
):
    # 1) SSRF guard + resolve
    normalized_url, _ = validate_url_and_resolve(str(payload.url))

    # 2) robots.txt check (fail-open policy can be tuned later)
    if not can_fetch(SCRAPER_USER_AGENT, normalized_url):
        now = datetime.now(timezone.utc)
        return AnalyzeResponse(
            id=str(uuid.uuid4()),
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
    answers = []
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

    # Persist to DB
    try:
        # Upsert session row for this URL (avoid duplicates in list)
        existing_session = (
            db.query(AnalysisSessionModel)
            .filter(AnalysisSessionModel.url == normalized_url)
            .order_by(AnalysisSessionModel.created_at.desc())
            .first()
        )

        if existing_session:
            session_row = existing_session
            session_row.status = "completed"
            session_row.ai_provider = AI_PROVIDER
            session_row.model = (
                os.getenv("OPENAI_MODEL")
                if AI_PROVIDER == "openai"
                else os.getenv("GEMINI_MODEL", "gemini-1.5-pro") if AI_PROVIDER == "gemini" else None
            )
        else:
            session_row = AnalysisSessionModel(
                url=normalized_url,
                status="completed",
                ai_provider=AI_PROVIDER,
                model=os.getenv("OPENAI_MODEL") if AI_PROVIDER == "openai" else os.getenv("GEMINI_MODEL", "gemini-1.5-pro") if AI_PROVIDER == "gemini" else None,
            )
            db.add(session_row)
            db.flush()  # get session_row.id

        # Snapshot: record latest fetch as a new row (history)
        snapshot_row = PageSnapshotModel(
            analysis_session_id=session_row.id,
            final_url=final_url,
            http_status=status_code,
            title=company.unique_selling_proposition,
            meta_description=(company.core_products_services[0] if company.core_products_services else None),
            raw_html=None,
            main_text=main_text if 'main_text' in locals() else None,
        )
        db.add(snapshot_row)

        # Company info: update existing or create
        existing_company = (
            db.query(CompanyInfoModel)
            .filter(CompanyInfoModel.analysis_session_id == session_row.id)
            .first()
        )
        if existing_company:
            existing_company.industry = company.industry
            existing_company.company_size = company.company_size
            existing_company.location = company.location
            existing_company.core_products_services = company.core_products_services
            existing_company.unique_selling_proposition = company.unique_selling_proposition
            existing_company.target_audience = company.target_audience
        else:
            company_row = CompanyInfoModel(
                analysis_session_id=session_row.id,
                industry=company.industry,
                company_size=company.company_size,
                location=company.location,
                core_products_services=company.core_products_services,
                unique_selling_proposition=company.unique_selling_proposition,
                target_audience=company.target_audience,
            )
            db.add(company_row)

        # Contact info: update if we parsed anything
        if 'emails' in locals() or 'phones' in locals() or 'socials' in locals():
            existing_contact = (
                db.query(ContactInfoModel)
                .filter(ContactInfoModel.analysis_session_id == session_row.id)
                .first()
            )
            if existing_contact:
                if 'emails' in locals():
                    existing_contact.emails = emails
                if 'phones' in locals():
                    existing_contact.phones = phones
                if 'socials' in locals():
                    existing_contact.social = socials
            else:
                contact_row = ContactInfoModel(
                    analysis_session_id=session_row.id,
                    emails=emails if 'emails' in locals() else None,
                    phones=phones if 'phones' in locals() else None,
                    social=socials if 'socials' in locals() else None,
                )
                db.add(contact_row)

        # Extracted answers: replace with latest
        if answers:
            db.query(ExtractedAnswerModel).filter(
                ExtractedAnswerModel.analysis_session_id == session_row.id
            ).delete(synchronize_session=False)
            for a in answers:
                db.add(
                    ExtractedAnswerModel(
                        analysis_session_id=session_row.id,
                        question=a.get("question"),
                        answer=a.get("answer"),
                    )
                )

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Analyze] DB persistence error: {e}")

    now = datetime.now(timezone.utc)
    print(f"Analysis completed for {final_url} at {now}")
    print(f"Company info: {company}")
    return AnalyzeResponse(
        id=str(session_row.id),
        url=final_url,
        analysis_timestamp=now,
        company_info=company,
        extracted_answers=answers,
    )


@router.get("/sessions", response_model=List[AnalysisSummary], dependencies=[Depends(verify_bearer_token)])
async def list_sessions(db: Session = Depends(get_db)):
    rows = (
        db.query(AnalysisSessionModel)
        .order_by(AnalysisSessionModel.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        AnalysisSummary(
            id=str(r.id),
            url=r.url,
            created_at=r.created_at,
            ai_provider=r.ai_provider,
            model=r.model,
            status=r.status,
        )
        for r in rows
    ]


@router.get("/sessions/{id}", response_model=AnalyzeResponse, dependencies=[Depends(verify_bearer_token)])
async def get_session(id: str, db: Session = Depends(get_db)):
    # Validate id
    try:
        session_uuid = uuid.UUID(str(id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session id")

    # Load session
    session_row = db.query(AnalysisSessionModel).filter(AnalysisSessionModel.id == session_uuid).first()
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load company info
    company_row = db.query(CompanyInfoModel).filter(CompanyInfoModel.analysis_session_id == session_row.id).first()

    company = CompanyInfoSchema()
    if company_row:
        company.industry = company_row.industry
        company.company_size = company_row.company_size
        company.location = company_row.location
        company.core_products_services = company_row.core_products_services
        company.unique_selling_proposition = company_row.unique_selling_proposition
        company.target_audience = company_row.target_audience

    # Load contact info, map to schema (best-effort)
    contact_row = db.query(ContactInfoModel).filter(ContactInfoModel.analysis_session_id == session_row.id).first()
    if contact_row:
        social = None
        if contact_row.social:
            social = SocialMedia(
                linkedin=contact_row.social.get("linkedin"),
                twitter=contact_row.social.get("twitter"),
                facebook=contact_row.social.get("facebook"),
                youtube=contact_row.social.get("youtube"),
                instagram=contact_row.social.get("instagram"),
                tiktok=contact_row.social.get("tiktok"),
            )
        company.contact_info = ContactInfoSchema(
            email=(contact_row.emails[0] if contact_row.emails else None),
            phone=(contact_row.phones[0] if contact_row.phones else None),
            social_media=social,
        )

    # Load extracted answers
    answers_rows = (
        db.query(ExtractedAnswerModel)
        .filter(ExtractedAnswerModel.analysis_session_id == session_row.id)
        .all()
    )
    extracted_answers: list[QAItem] = []
    for a in answers_rows:
        if getattr(a, "question", None) and getattr(a, "answer", None):
            extracted_answers.append(QAItem(question=a.question, answer=a.answer))

    return AnalyzeResponse(
        id=str(session_row.id),
        url=session_row.url,
        analysis_timestamp=session_row.created_at,
        company_info=company,
        extracted_answers=extracted_answers,
    )

