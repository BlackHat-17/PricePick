"""
PricePick Backend - Main Application Entry Point
Inspired by iShopBot architecture for price tracking and monitoring
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import List

from app.routes import products, prices, users, monitoring, search
from app.database import init_db, get_db_session
from app.services.price_monitor import PriceMonitorService
from app.tasks.scheduler import TaskScheduler
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting PricePick backend...")
    await init_db()
    
    # Initialize price monitoring service (it will get its own db sessions when needed)
    # Create a db session for initialization - the service manages its own sessions for operations
    db = get_db_session()
    try:
        price_monitor = PriceMonitorService(db)
        app.state.price_monitor = price_monitor
    except Exception as e:
        logger.error(f"Failed to initialize price monitor service: {e}")
        db.close()
        raise
    
    # Start background task scheduler
    scheduler = TaskScheduler()
    app.state.scheduler = scheduler
    await scheduler.start()
    
    logger.info("PricePick backend started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PricePick backend...")
    await scheduler.stop()
    logger.info("PricePick backend shutdown complete!")


# Create FastAPI application
app = FastAPI(
    title="PricePick API",
    description="A comprehensive price tracking and monitoring system inspired by iShopBot",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(prices.router, prefix="/api/v1/prices", tags=["prices"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])


@app.get("/")
async def root():
    """
    Root endpoint for health check
    """
    return {
        "message": "PricePick API is running!",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint
    """
    try:
        # Check database connection
        from app.database import get_db
        db = next(get_db())
        
        return {
            "status": "healthy",
            "database": "connected",
            "services": {
                "price_monitor": "active",
                "scheduler": "running"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
