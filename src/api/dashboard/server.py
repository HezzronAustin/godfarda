"""
FastAPI server for the monitoring dashboard.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.api.dashboard.routes import router as dashboard_router

app = FastAPI(title="Event Monitor Dashboard")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the absolute path to the UI directory
ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ui", "dashboard")

# Include API routes
app.include_router(dashboard_router, prefix="/api/dashboard")

# Mount static files (dashboard UI)
app.mount("/static", StaticFiles(directory=ui_dir), name="static")

@app.get("/")
async def read_root():
    """Serve the main dashboard page."""
    index_path = os.path.join(ui_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "Index file not found"}, status_code=404)

@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    """Debug middleware to log requests."""
    print(f"Request path: {request.url.path}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

def start_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Start the dashboard server."""
    print(f"Starting server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
