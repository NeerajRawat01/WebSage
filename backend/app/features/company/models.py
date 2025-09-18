import uuid

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from db.db import Base


class CompanyInfo(Base):
    __tablename__ = "company_info"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    industry = Column(String(256), nullable=True)
    company_size = Column(String(128), nullable=True)
    location = Column(String(256), nullable=True)
    core_products_services = Column(JSONB, nullable=True)  # list[str]
    unique_selling_proposition = Column(String(1024), nullable=True)
    target_audience = Column(String(512), nullable=True)


