from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sentinel2_function
import uvicorn
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the public directory to serve static files
app.mount("/static", StaticFiles(directory="/usr/src/app", html=True), name="public")

# Include router
app.include_router(sentinel2_function.router, prefix="/sentinel2")

# Endpoint to expose APP_HOST and other environment variables
@app.get("/config")
async def get_config():
    return {
        "APP_HOST": os.getenv("APP_HOST", "0.0.0.0"),
        "APP_PORT": 8000
    }

@app.middleware("http")
async def log_requests(request, call_next):
    logger = logging.getLogger("uvicorn")
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
