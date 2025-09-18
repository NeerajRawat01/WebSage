import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from db.db import Base


class ExtractedAnswer(Base):
    __tablename__ = "extracted_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question = Column(String(1024), nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class QAExchange(Base):
    __tablename__ = "qa_exchanges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_query = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    context_sources = Column(JSONB, nullable=True)  # list[str] or structured refs
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


