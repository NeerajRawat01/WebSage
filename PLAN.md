## WebSage Backend — AI Website Insight Agent (Implementation Plan)

This document outlines the step-by-step plan to design and develop a high-performance FastAPI application that analyzes website homepages and provides structured business insights and conversational Q&A. We will implement it incrementally without breaking the existing structure.

### 1) Architecture Overview
- **Core services**: FastAPI backend, Postgres (existing), Redis (add) for rate limiting and optional caching.
- **Scraping**: `httpx` HTTP-first with retries/timeouts/robots.txt. Optional Playwright fallback for JS-heavy sites.
- **Parsing**: Convert HTML → cleaned main text (readability/selectolax). Extract title/meta and headings.
- **AI layer**: Provider-agnostic LLM interface (OpenAI/Anthropic/Gemini/OpenRouter). Prompt templates for extraction, summarization, QA.
- **Persistence**: Store analysis sessions, page snapshots, structured insights, and conversation history in Postgres.
- **Rate limiting**: `fastapi-limiter` backed by Redis.
- **Security**: Bearer secret key, SSRF guard, robots.txt compliance.
- **Optional RAG**: Embeddings + vector search with pgvector or Redis vectors.

### 2) Environment Variables (.env)
- `API_SECRET_KEY=your_secret_key`
- `DATABASE_URL=postgresql+psycopg2://websage_user:websage_pass@db:5432/websage_db`
- `REDIS_URL=redis://redis:6379/0`
- `AI_PROVIDER=openai` (alternatives: `anthropic`, `gemini`, `openrouter`)
- `OPENAI_API_KEY=...`
- `ANTHROPIC_API_KEY=...`
- `GEMINI_API_KEY=...`
- `OPENROUTER_API_KEY=...`
- `SCRAPER_TIMEOUT_SECONDS=15`
- `SCRAPER_MAX_REDIRECTS=5`
- `SCRAPER_USER_AGENT=WebSageBot/1.0 (+contact@example.com)`
- `PLAYWRIGHT_ENABLED=false`
- `ENABLE_EMBEDDINGS=false`
- `LOG_LEVEL=INFO`
- `ALLOWED_SCHEMES=https,http`
- `DISALLOW_PRIVATE_IPS=true`

### 3) Dependencies (backend/requirements.txt additions)
- HTTP and parsing: `httpx[http2]`, `tenacity`, `selectolax`, `lxml`, `readability-lxml`, `tldextract`, `urllib3[brotli]`, `beautifulsoup4` (optional), `trafilatura` (optional)
- Data extraction: `phonenumbers`
- Rate limiting and cache: `redis`, `fastapi-limiter`
- Config/logging: `pydantic-settings` (optional), `loguru`
- Dates/typing: `python-dateutil`, `typing-extensions`
- LLM providers: `openai` (or `anthropic`, `google-generativeai`, `openrouter`)
- Optional embeddings: `pgvector` (SQLAlchemy integration) or `redisvl`
- Optional JS rendering: `playwright`

### 4) Database Models (SQLAlchemy)
- `AnalysisSession` (uuid id, `url` normalized, `created_at`, `status`, `ai_provider`, `model`, optional `sentiment`).
- `PageSnapshot` (id, `analysis_session_id` fk, `final_url`, `http_status`, `title`, `meta_description`, `raw_html` text, `main_text` text, `fetched_at`).
- `CompanyInfo` (id, `analysis_session_id` fk, `industry`, `company_size`, `location`, `core_products_services` JSON/list, `usp`, `target_audience`).
- `ContactInfo` (id, `analysis_session_id` fk, emails JSON, phones JSON, socials JSON {linkedin, twitter, facebook, youtube, instagram, tiktok}).
- `ExtractedAnswer` (id, `analysis_session_id` fk, `question`, `answer`, `created_at`).
- `QAExchange` (id, `analysis_session_id` fk, `user_query`, `agent_response`, `context_sources` JSON, `created_at`).
- Optional RAG: `TextChunk` (id, `analysis_session_id` fk, `chunk_text`, `embedding` pgvector).

We will create Alembic migrations for these models.

### 5) API Design
#### Endpoint 1: Analyze (POST `/analyze`)
- Auth: Bearer token required.
- Rate limit: e.g., `10/min` per API key/IP.
- Request: `{ url: string, questions?: string[] }`
- Flow:
  1. Validate and normalize URL; SSRF guard (allowed schemes, public IP).
  2. robots.txt check for user-agent; abort if disallowed.
  3. Fetch with `httpx` (HTTP/2, timeout, redirects, retries, compression).
  4. Parse title/meta and main text (readability/selectolax). Detect language if available.
  5. Extract contacts: emails, phones (E.164 with `phonenumbers`), social links (domain matching).
  6. AI extraction: industry, company size, location, USP, products/services, target audience; answer any provided questions.
  7. Persist session, snapshot, company/contact info, and extracted answers.
  8. Respond with structured JSON matching the spec.

#### Endpoint 2: Converse (POST `/converse`)
- Auth: Bearer token required.
- Rate limit: e.g., `30/min` per API key/IP.
- Request: `{ url?: string, session_id?: string, query: string, conversation_history?: QAExchangeLite[] }`
- Flow:
  1. Resolve `AnalysisSession` by `url` or `session_id`.
  2. Build context from `main_text`, `company_info`, `contact_info`, prior answers, and recent exchanges.
  3. If embeddings enabled, retrieve top-k relevant chunks.
  4. Call LLM with system prompt + context + query (+ history) to generate response.
  5. Persist `QAExchange` with `context_sources` references (snippets/sections).
  6. Respond with `{ url, user_query, agent_response, context_sources }`.

### 6) Scraper & Parser Design
- `httpx.AsyncClient` with default headers (UA, Accept, Accept-Language, Accept-Encoding) and strict timeouts.
- Retry/backoff via `tenacity` for transient errors (connect/reset/read timeouts, 5xx).
- Limit max redirects (`SCRAPER_MAX_REDIRECTS`) and bytes (cap download size, e.g., 10 MB).
- Charset detection and decompression (gzip/br); respect Content-Type.
- robots.txt using `urllib.robotparser` or `reppy` alternative.
- HTML → text: prefer `readability-lxml`, fallback `selectolax` to remove scripts/styles/nav and get main content.
- Keep `title`, `meta description`, H1/H2 as context seeds.

### 7) Contact & Social Extraction
- Emails: regex with validation and deduplication, filter obvious placeholders.
- Phones: `phonenumbers` parse across text; normalize to E.164 and dedupe.
- Socials: normalize anchor `href` domains; collect LinkedIn, Twitter/X, Facebook, YouTube, Instagram, TikTok.

### 8) AI Layer
- Provider interface: `generate_insights(context, url)`, `answer_query(context, question, history)`, optional `embed_texts(texts)`.
- Providers: start with OpenAI; add Anthropic/Gemini/OpenRouter via the same interface.
- System prompt: “You are WebSage, an AI for extracting structured business insights from website homepages. Be concise, factual, and say when information is insufficient.”
- Extraction prompt: input title/meta/main_text + heuristics; output strict JSON with required keys; allow `null`/"inferred" flags where necessary.
- QA prompt: include selected context chunks + company info + recent history; answer concisely, avoid fabrication; cite source snippets.
- Optional Sentiment: derive single-sentence tone.

### 9) Pydantic Models
- Requests: `AnalyzeRequest`, `ConverseRequest` (with `HttpUrl` fields and proper validation).
- Responses: `CompanyInfo`, `ContactInfo`, `ExtractedAnswer`, `AnalyzeResponse`, `ConverseResponse`.
- Ensure ISO8601 UTC timestamps.

### 10) Authentication & Rate Limiting
- Auth dependency: parse `Authorization: Bearer <token>` and compare with `API_SECRET_KEY`; 401 on mismatch.
- Rate limiting: initialize `fastapi-limiter` with `REDIS_URL`; decorate endpoints (keyed by API key + IP for fairness).

### 11) Security
- SSRF guard: allowed schemes only; resolve DNS and block private/reserved IP ranges.
- Respect `robots.txt` by default.
- Size limits and safe timeouts; sanitize/limit logs (no raw HTML in logs).

### 12) Persistence & Sessions
- Normalize URL (scheme+host+path trimmed) for session lookup.
- Store `PageSnapshot` (raw_html optionally, `main_text` definitely).
- Store `CompanyInfo` and `ContactInfo` in 1:1 relation with session.
- Save `ExtractedAnswer` for provided questions.
- In converses, append `QAExchange` with sources.

### 13) Optional Embeddings & RAG
- If enabled, chunk `main_text` and compute embeddings.
- Store vectors (pgvector or Redis). Retrieve top-k for QA prompt context.

### 14) Logging & Observability
- Use `loguru` for structured logs: request_id, url, timings, status codes, sizes, ai_provider/model.
- Global exception handlers returning consistent error JSON (correlation id).
- Optional Prometheus metrics via `prometheus-fastapi-instrumentator`.

### 15) Testing Plan
- Unit: URL validation/SSRF guard, robots, parser, contact/social extraction, auth, rate limiting stubs.
- Integration: `/analyze` end-to-end with fixture HTML; `/converse` with stored session.
- Load: k6/Locust for 10–50 RPS; watch p95, error rate, Redis behavior.

### 16) Docker/Compose Plan
- Add `redis` service to `docker-compose.yml` and healthcheck.
- Backend: add required OS libs for lxml/readability; if Playwright enabled, install browsers (`playwright install --with-deps chromium`).
- Ensure `.env` mounted and used by backend (already in compose).

### 17) Step-by-Step Execution (Milestones)
1. Add Redis service and wire `fastapi-limiter`.
2. Implement Bearer auth dependency and apply to both endpoints.
3. Implement scraper (httpx + robots + retries) and parser utilities.
4. Implement contact/social extraction utilities.
5. Define Pydantic request/response models.
6. Add SQLAlchemy models + Alembic migrations for sessions/insights.
7. Implement `/analyze` pipeline and persistence; return structured response.
8. Implement `/converse` using stored session and history.
9. Add AI provider abstraction and integrate OpenAI; extend to others.
10. (Optional) Add embeddings and retrieval.
11. Add logging, error handlers, and tests.
12. Update Dockerfiles (system deps, optional Playwright) and compose.

### 18) Example Response Specs
Analyze Response:
```json
{
  "url": "https://example.com",
  "analysis_timestamp": "2025-06-06T21:10:40Z",
  "company_info": {
    "industry": "Software Development",
    "company_size": "Medium (50-200 employees)",
    "location": "San Francisco, CA, USA",
    "core_products_services": ["Cloud CRM", "Customer Support Software"],
    "unique_selling_proposition": "AI-powered CRM that predicts customer churn.",
    "target_audience": "Small to Medium Businesses (SMBs)",
    "contact_info": {
      "email": "info@example.com",
      "phone": "+1-555-123-4567",
      "social_media": {
        "linkedin": "https://linkedin.com/company/example",
        "twitter": "https://twitter.com/example"
      }
    }
  },
  "extracted_answers": [
    { "question": "What is their primary business model?", "answer": "SaaS subscription model." }
  ]
}
```

Converse Response:
```json
{
  "url": "https://example.com",
  "user_query": "What are the key features of their CRM?",
  "agent_response": "The key features of their CRM include AI-powered churn prediction, automated customer support ticketing, and comprehensive sales pipeline management.",
  "context_sources": ["paragraph about CRM features", "product page description"]
}
```

### 19) Risks & Mitigations
- **JS-heavy pages**: Use Playwright fallback behind a feature flag and higher timeouts.
- **LLM hallucinations**: Strict prompts and allow “insufficient evidence”; include context sources in responses.
- **Rate limiting dependencies**: If Redis is down, return 503 with `Retry-After` or degrade gracefully.
- **Compliance**: Default to respecting robots.txt; document behavior.

### 20) Acceptance Criteria
- Two secured endpoints (`/analyze`, `/converse`) with Redis-backed rate limits.
- Accurate structured extraction for common marketing sites.
- Conversational answers grounded in scraped content; includes context sources.
- Clean logs, robust error handling, and basic tests passing.


### 21) Feature-based App Structure (backend/app/)
We will organize code by feature with local `models.py`, `schemas.py`, and optional `api.py` per feature.

```
backend/
  app/
    __init__.py
    core/
      __init__.py
      config.py            # settings (env)
      security.py          # bearer auth dependency
      rate_limit.py        # fastapi-limiter setup
      logging.py           # logger setup
    services/
      scraper/
        __init__.py
        fetcher.py         # httpx client + retries/timeouts
        robots.py          # robots.txt checks
        parser.py          # readability/selectolax content extraction
        extract_contact.py # emails/phones/social heuristics
      ai/
        __init__.py
        provider.py        # abstraction interface
        openai_provider.py # first concrete provider
        prompts.py         # prompt templates
        embeddings.py      # optional embeddings/RAG
    features/
      analysis/
        __init__.py
        models.py          # AnalysisSession, PageSnapshot
        schemas.py         # Pydantic request/response for analyze
        api.py             # /analyze route (router)
      company/
        __init__.py
        models.py          # CompanyInfo
        schemas.py
      contact/
        __init__.py
        models.py          # ContactInfo
        schemas.py
      qa/
        __init__.py
        models.py          # ExtractedAnswer, QAExchange
        schemas.py
      embeddings/          # optional
        __init__.py
        models.py          # TextChunk (pgvector/redis)
        schemas.py
    api/
      __init__.py
      router.py            # compose feature routers: analyze, converse
```

Main application will `include_router` from `app/api/router.py`. Alembic will import `app.features.*.models` to register metadata.

### 22) SQLAlchemy Model Specifications
Below are precise fields and types for initial implementation.

```python
# app/features/analysis/models.py
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
    analysis_session_id = Column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    final_url = Column(String(1024), nullable=False)
    http_status = Column(Integer, nullable=True)
    title = Column(String(512), nullable=True)
    meta_description = Column(String(1024), nullable=True)
    raw_html = Column(Text, nullable=True)
    main_text = Column(Text, nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

```python
# app/features/company/models.py
import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from db.db import Base

class CompanyInfo(Base):
    __tablename__ = "company_info"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    industry = Column(String(256), nullable=True)
    company_size = Column(String(128), nullable=True)
    location = Column(String(256), nullable=True)
    core_products_services = Column(JSONB, nullable=True)  # list[str]
    unique_selling_proposition = Column(String(1024), nullable=True)
    target_audience = Column(String(512), nullable=True)
```

```python
# app/features/contact/models.py
import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from db.db import Base

class ContactInfo(Base):
    __tablename__ = "contact_info"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    emails = Column(JSONB, nullable=True)    # list[str]
    phones = Column(JSONB, nullable=True)    # list[str] E.164
    social = Column(JSONB, nullable=True)    # {linkedin, twitter, facebook, youtube, instagram, tiktok}
```

```python
# app/features/qa/models.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from db.db import Base

class ExtractedAnswer(Base):
    __tablename__ = "extracted_answers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(String(1024), nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class QAExchange(Base):
    __tablename__ = "qa_exchanges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_query = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    context_sources = Column(JSONB, nullable=True)  # list[str] or structured refs
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

```python
# app/features/embeddings/models.py (optional)
import uuid
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from db.db import Base
from sqlalchemy_utils import ScalarListType  # or pgvector integration

# If using pgvector, use appropriate type; placeholder here for planning.
class TextChunk(Base):
    __tablename__ = "text_chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_session_id = Column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    # embedding = Column(Vector(1536))  # with pgvector extension
```

### 23) Pydantic Schemas Specifications

```python
# app/features/analysis/schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict
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
```

```python
# app/features/qa/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class QAExchangeLite(BaseModel):
    user_query: str
    agent_response: str

class ConverseRequest(BaseModel):
    url: Optional[HttpUrl] = None
    session_id: Optional[str] = None
    query: str
    conversation_history: Optional[List[QAExchangeLite]] = None

class ConverseResponse(BaseModel):
    url: HttpUrl
    user_query: str
    agent_response: str
    context_sources: List[str]
```

### 24) Alembic Integration Notes
- Ensure Alembic imports all feature models so `Base.metadata` includes them during autogenerate:
  - Update `backend/migrations/env.py` to import:
    - `from app.features.analysis.models import AnalysisSession, PageSnapshot`
    - `from app.features.company.models import CompanyInfo`
    - `from app.features.contact.models import ContactInfo`
    - `from app.features.qa.models import ExtractedAnswer, QAExchange`
    - (optional) embeddings models
- Add `backend/app` to Python path for Alembic (adjust `sys.path` logic if needed).
- Create first migration: `alembic revision --autogenerate -m "init analysis models"` then `alembic upgrade head`.

### 25) Conventions
- Table names: snake_case plural (`analysis_sessions`, `page_snapshots`, ...).
- String length caps: 256/512/1024 depending on field.
- Use UUIDs for primary keys; store timestamps as timezone-aware.
- JSONB for lists/maps (Postgres). If SQLite in dev, use `JSON` and adapt.
- Pydantic models mirror API spec; internal ORM models can be richer but response models stay stable.


