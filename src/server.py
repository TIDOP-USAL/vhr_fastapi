from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sentinel2_function
import uvicorn
import os
from dotenv import load_dotenv

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

# Static files
app.mount("/public", StaticFiles(directory="public"), name="public")

# Include router
app.include_router(sentinel2_function.router, prefix="/sentinel2")

# Endpoint to expose APP_HOST and other environment variables
@app.get("/config")
async def get_config():
    return {
        "APP_HOST": os.getenv("APP_HOST", "127.0.0.1")
    }

# Run the app
if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    uvicorn.run("server:app", host=host, port=8000, loop="asyncio", reload=True)
