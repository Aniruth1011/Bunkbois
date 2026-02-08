"""
Healthcare Agent API - Minimal Single File Version
Just drop this file into your FINAL/ directory and run it!

Requirements: pip install fastapi uvicorn
Usage: python api_gateway_simple.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime
import uuid

# Import your existing healthcare agent
from enhanced_healthcare_agent2 import run_query

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Agent API",
    description="Query endpoint for healthcare data",
    version="1.0.0"
)

# Configure CORS - allow your frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class HealthcareQuery(BaseModel):
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "How many hospitals are in California?"
            }
        }

# Response model
class HealthcareResponse(BaseModel):
    query_id: str
    query: str
    answer: str
    timestamp: str
    processing_time_ms: Optional[float] = None


# ==================== MAIN ENDPOINT ====================

@app.post("/api/v1/query", response_model=HealthcareResponse)
async def query_healthcare(request: HealthcareQuery):
    """
    Main endpoint - your frontend sends queries here
    """
    try:
        query_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Run the query through your existing agent system
        result = run_query(request.query)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return HealthcareResponse(
            query_id=query_id,
            query=request.query,
            answer=str(result),
            timestamp=start_time.isoformat(),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Healthcare Agent API",
        "endpoint": "POST /api/v1/query",
        "docs": "/docs",
        "example": {
            "url": "http://localhost:8000/api/v1/query",
            "method": "POST",
            "body": {"query": "How many hospitals in California?"}
        }
    }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Healthcare Agent API")
    print("="*60)
    print("\nAPI running at: http://localhost:8000")
    print("Documentation: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    print("\nFrontend endpoint: POST http://localhost:8000/api/v1/query")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
