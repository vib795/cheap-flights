import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app import db
from app.api.routes import router
from app.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting GeoFlight Scout API...")
    await db.init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down GeoFlight Scout API...")
    await db.cleanup_expired_cache()


# Create FastAPI app
app = FastAPI(
    title="GeoFlight Scout API",
    description="Flight search with visa/transit risk assessment (IN-first)",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Serve frontend static files
FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # Mount static assets
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/")
    async def serve_frontend():
        """Serve frontend index.html"""
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    async def serve_frontend_routes(full_path: str):
        """Serve frontend for all non-API routes"""
        # Check if file exists
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for client-side routing
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root():
        """Root endpoint (dev mode without frontend build)"""
        return {
            "name": "GeoFlight Scout API",
            "version": "0.1.0",
            "docs": "/docs",
            "note": "Frontend not built. Run 'npm run build' in frontend directory.",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
