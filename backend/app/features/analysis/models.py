import uuid

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db.db import Base


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(1024), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(32), nullable=False, default="completed")  # planned|running|completed|failed
    ai_provider = Column(String(64), nullable=True)
    model = Column(String(128), nullable=True)
    sentiment = Column(String(64), nullable=True)


class PageSnapshot(Base):
    __tablename__ = "page_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    final_url = Column(String(1024), nullable=False)
    http_status = Column(Integer, nullable=True)
    title = Column(String(512), nullable=True)
    meta_description = Column(String(1024), nullable=True)
    raw_html = Column(Text, nullable=True)
    main_text = Column(Text, nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


