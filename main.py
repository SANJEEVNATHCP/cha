"""Main FastAPI application factory."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.config.database import init_db
from app.routes import auth_routes, chat_routes


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize database
    init_db()
    
    # Include routers
    app.include_router(auth_routes.router)
    app.include_router(chat_routes.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    @app.get("/")
    async def root():
        return {
            "message": "ChatGPT-like Gen AI API",
            "docs": "/docs",
            "openapi_schema": "/openapi.json"
        }
    
    return app


app = create_app()
