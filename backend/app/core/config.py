import os


# Secret key for API auth (Bearer token)
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

# Redis URL for rate limiting (works in Docker Compose network)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Scraper configuration
SCRAPER_TIMEOUT_SECONDS = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "15"))
SCRAPER_MAX_REDIRECTS = int(os.getenv("SCRAPER_MAX_REDIRECTS", "5"))
SCRAPER_USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
)
ALLOWED_SCHEMES = set(
    s.strip() for s in os.getenv("ALLOWED_SCHEMES", "https,http").split(",") if s.strip()
)
DISALLOW_PRIVATE_IPS = os.getenv("DISALLOW_PRIVATE_IPS", "true").lower() in {"1","true","yes"}

# JS rendering fallback
PLAYWRIGHT_ENABLED = os.getenv("PLAYWRIGHT_ENABLED", "false").lower() in {"1","true","yes"}
PLAYWRIGHT_TIMEOUT_SECONDS = int(os.getenv("PLAYWRIGHT_TIMEOUT_SECONDS", "15"))

# AI config
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


