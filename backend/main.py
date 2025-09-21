from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import REDIS_URL
from app.core.rate_limit import init_rate_limiter, shutdown_rate_limiter

redis_client = None


app = FastAPI()

# Optional CORS if browser hits backend directly (not needed if using Next.js proxy only)
frontend_origin = "https://web-sage-scrape.vercel.app/"  # replace after deploy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to WebSage Backend 🚀"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}


@app.on_event("startup")
async def on_startup():
    global redis_client
    redis_client = await init_rate_limiter(REDIS_URL)


@app.on_event("shutdown")
async def on_shutdown():
    global redis_client
    await shutdown_rate_limiter(redis_client)
    redis_client = None


app.include_router(api_router)

#start server
#-> docker compose up --build

#stop server
#-> docker compose down --volumes

#restart server
# Generate migration 
#-> docker compose exec backend alembic revision --autogenerate -m "create analysis_sessions"

# Apply migration
#-> docker compose exec backend alembic upgrade head


# See current revision (optional)
# docker compose exec backend alembic current

# Downgrade all the way before the first migration
# docker compose exec backend alembic downgrade base

# Re-apply the first migration only (create analysis_sessions)
# docker compose exec backend alembic upgrade d1d214908152

# Then apply the rest (or just do this to run everything)
# docker compose exec backend alembic upgrade head

# Backend Logs
# - > docker compose logs -f backend