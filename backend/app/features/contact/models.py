import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from db.db import Base


class ContactInfo(Base):
    __tablename__ = "contact_info"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    emails = Column(JSONB, nullable=True)  # list[str]
    phones = Column(JSONB, nullable=True)  # list[str] E.164
    social = Column(JSONB, nullable=True)  # {linkedin, twitter, facebook, youtube, instagram, tiktok}


