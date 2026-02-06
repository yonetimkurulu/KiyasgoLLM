"""
KıyasGO AI Intelligence Service
LLM tabanlı ürün kıyaslama ve alışveriş zekası platformu.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from src.config import get_settings
from src.api import products, compare, best_for, signals, chat

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting KıyasGO AI Intelligence Service")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Cache enabled: {settings.cache_enabled}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down KıyasGO AI Intelligence Service")


# Create FastAPI app
app = FastAPI(
    title="KıyasGO AI Intelligence API",
    description="LLM tabanlı ürün kıyaslama ve alışveriş zekası platformu",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Add response timing header."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred",
        }
    )


# Include routers
app.include_router(
    products.router,
    prefix=f"/api/{settings.api_version}/ai",
    tags=["Products"]
)
app.include_router(
    compare.router,
    prefix=f"/api/{settings.api_version}/ai",
    tags=["Comparison"]
)
app.include_router(
    best_for.router,
    prefix=f"/api/{settings.api_version}/ai",
    tags=["Best-For"]
)
app.include_router(
    signals.router,
    prefix=f"/api/{settings.api_version}/ai",
    tags=["Signals"]
)
app.include_router(
    chat.router,
    prefix=f"/api/{settings.api_version}/ai",
    tags=["Chat"]
)


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm_provider": settings.llm_provider,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "KıyasGO AI Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "products": f"/api/{settings.api_version}/ai/products",
            "compare": f"/api/{settings.api_version}/ai/compare",
            "best_for": f"/api/{settings.api_version}/ai/best-for",
            "signals": f"/api/{settings.api_version}/ai/signals",
        }
    }
