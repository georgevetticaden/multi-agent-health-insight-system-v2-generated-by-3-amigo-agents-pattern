import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path to enable evaluation module imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables before any other imports
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from api.chat import router as chat_router
from api.tracing import router as tracing_router
from api.qe_chat import router as qe_chat_router
from api.evaluation import router as evaluation_router
from api.test_case import router as test_case_router
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
app.include_router(qe_chat_router)
app.include_router(evaluation_router)
app.include_router(test_case_router)

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
            {"id": "nutrition", "name": "Dr. Nutrition", "specialty": "Nutrition", "icon": "🥗"}
        ]
    }

# Mount static files for test case management app
# This will serve the frontend for /test-case-management/* routes
frontend_dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist_path):
    app.mount("/test-case-management", StaticFiles(directory=frontend_dist_path, html=True), name="test-case-management")

if __name__ == "__main__":
    import uvicorn
    # Set reload=False to avoid warnings about venv file changes
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_excludes=["venv/**"])