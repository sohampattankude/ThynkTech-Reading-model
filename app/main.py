"""
Reading Evaluation Module - Main Application Entry Point
=========================================================
ThynkChat INDIA V2 - Internship Assignment

This module initializes the FastAPI application and includes all routes
for the reading evaluation service.

Author: Intern
Date: January 2026
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Reading Evaluation Module",
    description="""
    A simplified Reading Evaluation Module that evaluates a student's 
    reading performance by comparing spoken audio with reference textbook content.
    
    ## Features
    - Speech-to-Text conversion using OpenAI Whisper
    - Text normalization and comparison
    - Reading performance metrics (Accuracy, Completeness, Fluency)
    - Suspicious reading detection
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler - runs when the application starts.
    Can be used for initializing resources like database connections.
    """
    print("🚀 Reading Evaluation Module is starting up...")
    print("📚 Service ready to evaluate student readings!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler - runs when the application stops.
    Can be used for cleanup tasks.
    """
    print("👋 Reading Evaluation Module is shutting down...")


# Entry point for running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    )
