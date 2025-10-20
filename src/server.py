"""FastAPI server for multi-user NATO Asset Codifier access."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from pipeline.codifier_pipeline import NATOCodifierPipeline
from utils.logger import setup_logger

# Initialize FastAPI app
app = FastAPI(
    title="NATO Asset Codifier API",
    description="Multi-user API for NATO asset classification",
    version="1.0.0"
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logger
logger = setup_logger("server")

# Initialize pipeline (singleton - loaded once)
pipeline = None


# Request/Response models
class CodifyRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class CodifyResponse(BaseModel):
    inc: Optional[int]
    name: Optional[str]
    definition: Optional[str]
    definition_ar: Optional[str]
    nsg: Optional[int]
    nsc: Optional[int]
    nsc_formatted: Optional[str]
    confidence: Optional[float]
    reasoning: Optional[str]
    reasoning_ar: Optional[str]
    error: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on server startup."""
    global pipeline
    logger.info("Starting NATO Asset Codifier API...")
    logger.info("Initializing pipeline (loading FAISS index)...")
    pipeline = NATOCodifierPipeline()
    logger.info("✓ Server ready to accept requests")

    # Mount static files for UI
    ui_path = Path(__file__).parent.parent / "ui"
    if ui_path.exists():
        app.mount("/static", StaticFiles(directory=str(ui_path / "static")), name="static")
        logger.info(f"✓ UI static files mounted from {ui_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    logger.info("Shutting down NATO Asset Codifier API...")


@app.get("/")
async def root():
    """Serve the Osool Guide UI."""
    ui_path = Path(__file__).parent.parent / "ui" / "index.html"
    if ui_path.exists():
        return FileResponse(ui_path)
    return {
        "service": "NATO Asset Codifier API",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/api")
async def api_root():
    """API health check endpoint."""
    return {
        "service": "NATO Asset Codifier API",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "pipeline_loaded": pipeline is not None,
        "faiss_items": pipeline.stage2.index.ntotal if pipeline else 0
    }


@app.post("/codify", response_model=CodifyResponse)
async def codify_item(request: CodifyRequest):
    """
    Codify a single item.

    Args:
        request: CodifyRequest with query string

    Returns:
        CodifyResponse with NATO classification codes
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Received codification request: '{request.query}'")

    try:
        # Run codification
        result = pipeline.codify(request.query)

        # Check for errors
        if "error" in result:
            logger.warning(f"Codification failed: {result['error']}")
            return CodifyResponse(error=result["error"])

        # Return successful result
        logger.info(f"Codification successful: INC {result.get('inc')}")
        return CodifyResponse(**result)

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    return {
        "total_items": pipeline.stage2.index.ntotal,
        "embedding_dimension": pipeline.stage2.index.d,
        "ollama_host": pipeline.config.ollama_host,
        "llm_model": pipeline.config.ollama_model,
        "embedding_model": pipeline.config.embedding_model
    }


def main():
    """Run the server."""
    import argparse

    parser = argparse.ArgumentParser(description="NATO Asset Codifier API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker processes")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development)")

    args = parser.parse_args()

    logger.info(f"Starting server on {args.host}:{args.port} with {args.workers} workers")

    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        workers=args.workers if not args.reload else 1,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
