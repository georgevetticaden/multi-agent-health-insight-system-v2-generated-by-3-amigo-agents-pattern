import os
import logging
from dotenv import load_dotenv

# Load environment variables before any other imports
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.chat import router as chat_router
from api.tracing import router as tracing_router
from utils.logging_config import setup_backend_logging

# Configure logging with both console and file output
setup_backend_logging(service_name="fastapi")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Multi-Agent Health Insight System...")
    yield
    logger.info("Shutting down Multi-Agent Health Insight System...")

app = FastAPI(
    title="Multi-Agent Health Insight System",
    description="AI-powered health analysis using orchestrated medical specialists",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(tracing_router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Multi-Agent Health Insight System",
        "version": "1.0.0"
    }

@app.get("/api/agents/specialists")
async def get_specialists():
    return {
        "specialists": [
            {"id": "heart", "name": "Dr. Heart", "specialty": "Cardiology", "icon": "❤️"},
            {"id": "hormone", "name": "Dr. Hormone", "specialty": "Endocrinology", "icon": "🔬"},
            {"id": "lab", "name": "Dr. Lab", "specialty": "Laboratory Medicine", "icon": "🧪"},
            {"id": "analytics", "name": "Dr. Analytics", "specialty": "Data Analysis", "icon": "📊"},
            {"id": "prevention", "name": "Dr. Prevention", "specialty": "Preventive Medicine", "icon": "🛡️"},
            {"id": "pharma", "name": "Dr. Pharma", "specialty": "Pharmacy", "icon": "💊"},
            {"id": "nutrition", "name": "Dr. Nutrition", "specialty": "Nutrition", "icon": "🥗"},
            {"id": "primary", "name": "Dr. Primary", "specialty": "General Practice", "icon": "👨‍⚕️"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    # Set reload=False to avoid warnings about venv file changes
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_excludes=["venv/**"])