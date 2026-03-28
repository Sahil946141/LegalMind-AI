#!/usr/bin/env python3
"""
Startup script for the Legal Analyzer application
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting Legal Analyzer Application...")
    print("Server will be available at: http://localhost:8000")
    print("API docs available at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        # Increase limits for file uploads
        limit_max_requests=1000,
        limit_concurrency=100,
        timeout_keep_alive=30
    )