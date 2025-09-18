from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    questions: Optional[List[str]] = None


class SocialMedia(BaseModel):
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    facebook: Optional[str] = None
    youtube: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None


class ContactInfoSchema(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    social_media: Optional[SocialMedia] = None


class CompanyInfoSchema(BaseModel):
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    core_products_services: Optional[List[str]] = None
    unique_selling_proposition: Optional[str] = None
    target_audience: Optional[str] = None
    contact_info: Optional[ContactInfoSchema] = None


class QAItem(BaseModel):
    question: str
    answer: str


class AnalyzeResponse(BaseModel):
    url: HttpUrl
    analysis_timestamp: datetime
    company_info: CompanyInfoSchema
    extracted_answers: List[QAItem] = Field(default_factory=list)


