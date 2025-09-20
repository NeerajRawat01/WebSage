from datetime import datetime, timezone
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from app.core.security import verify_bearer_token
from app.core.config import (
    AI_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.scraper.guard import validate_url_and_resolve
from db.db import get_db
from app.features.analysis.models import AnalysisSession as AnalysisSessionModel, PageSnapshot as PageSnapshotModel
from app.features.company.models import CompanyInfo as CompanyInfoModel
from app.features.contact.models import ContactInfo as ContactInfoModel
from app.features.qa.models import QAExchange as QAExchangeModel
from .schemas import ConverseRequest, ConverseResponse, QAExchangeHistory


router = APIRouter(prefix="/converse", tags=["converse"]) 


def _build_context(
    snapshot: PageSnapshotModel | None,
    company: CompanyInfoModel | None,
    contact: ContactInfoModel | None,
) -> str:
    parts: List[str] = []
    if snapshot:
        if snapshot.title:
            parts.append(f"Title: {snapshot.title}")
        if snapshot.meta_description:
            parts.append(f"Meta: {snapshot.meta_description}")
        if snapshot.main_text:
            parts.append(f"Main Text: {snapshot.main_text}")
    if company:
        if company.industry:
            parts.append(f"Industry: {company.industry}")
        if company.company_size:
            parts.append(f"Company Size: {company.company_size}")
        if company.location:
            parts.append(f"Location: {company.location}")
        if company.unique_selling_proposition:
            parts.append(f"USP: {company.unique_selling_proposition}")
        if company.core_products_services:
            parts.append(f"Products/Services: {', '.join(company.core_products_services)}")
        if company.target_audience:
            parts.append(f"Target Audience: {company.target_audience}")
    if contact:
        if contact.emails:
            parts.append(f"Emails: {', '.join(contact.emails)}")
        if contact.phones:
            parts.append(f"Phones: {', '.join(contact.phones)}")
        if contact.social:
            socials = [f"{k}: {v}" for k, v in contact.social.items() if v]
            if socials:
                parts.append("Socials: " + ", ".join(socials))
    context = "\n".join(parts)
    # Truncate overly long context to keep token usage sane
    return context[:12000]


@router.post("", response_model=ConverseResponse, dependencies=[Depends(verify_bearer_token)])
async def converse_endpoint(
    payload: ConverseRequest,
    rate_limited: None = Depends(RateLimiter(times=30, seconds=60)),
    db: Session = Depends(get_db),
):
    if not payload.url and not payload.session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide either url or session_id")

    # Resolve session
    session_row: AnalysisSessionModel | None = None
    resolved_url: str | None = None
    if payload.session_id:
        try:
            sess_uuid = uuid.UUID(str(payload.session_id))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid session_id")
        session_row = db.query(AnalysisSessionModel).filter(AnalysisSessionModel.id == sess_uuid).first()
        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")
        resolved_url = session_row.url
    else:
        # Normalize URL similar to analyze
        normalized_url, _ = validate_url_and_resolve(str(payload.url))
        resolved_url = normalized_url
        session_row = (
            db.query(AnalysisSessionModel)
            .filter(AnalysisSessionModel.url == normalized_url)
            .order_by(AnalysisSessionModel.created_at.desc())
            .first()
        )
        if not session_row:
            raise HTTPException(status_code=404, detail="No analysis found for this URL")

    # Load latest snapshot and company/contact
    snapshot = (
        db.query(PageSnapshotModel)
        .filter(PageSnapshotModel.analysis_session_id == session_row.id)
        .order_by(PageSnapshotModel.fetched_at.desc())
        .first()
    )
    company = db.query(CompanyInfoModel).filter(CompanyInfoModel.analysis_session_id == session_row.id).first()
    contact = db.query(ContactInfoModel).filter(ContactInfoModel.analysis_session_id == session_row.id).first()

    context = _build_context(snapshot, company, contact)

    # Choose AI provider
    ai = None
    if AI_PROVIDER == "openai" and OPENAI_API_KEY:
        ai = OpenAIProvider(model=OPENAI_MODEL)
    elif AI_PROVIDER == "gemini" and os.getenv("GEMINI_API_KEY"):
        ai = GeminiProvider(os.getenv("GEMINI_MODEL", "gemini-1.5-pro"))

    if not ai:
        raise HTTPException(status_code=503, detail="AI provider not configured")

    # Ask the question
    try:
        answers = await ai.answer_questions(context, [payload.query])
        agent_answer = answers[0]["answer"] if answers else ""
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI error: {e}")

    # Persist QA exchange
    try:
        exchange = QAExchangeModel(
            analysis_session_id=session_row.id,
            user_query=payload.query,
            agent_response=agent_answer,
            context_sources=["snapshot.title", "snapshot.meta", "snapshot.main_text"],
        )
        db.add(exchange)
        db.commit()
    except Exception:
        db.rollback()

    return ConverseResponse(
        url=resolved_url, user_query=payload.query, agent_response=agent_answer, context_sources=["main_text", "metadata"]
    )


@router.get("/history/{session_id}", response_model=List[QAExchangeHistory], dependencies=[Depends(verify_bearer_token)])
async def get_history(session_id: str, db: Session = Depends(get_db)):
    try:
        sess_uuid = uuid.UUID(str(session_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session_id")
    rows = (
        db.query(QAExchangeModel)
        .filter(QAExchangeModel.analysis_session_id == sess_uuid)
        .order_by(QAExchangeModel.created_at.asc())
        .all()
    )
    return [
        QAExchangeHistory(
            user_query=r.user_query,
            agent_response=r.agent_response,
            created_at=r.created_at,
        )
        for r in rows
    ]