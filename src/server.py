from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.routes import planet_function
import uvicorn

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
app.include_router(planet_function.router, prefix="/planet")

# Run the app
if __name__ == "__main__":
    uvicorn.run("src.server:app", host="127.0.0.1", port=8000, 
                    loop="asyncio", reload=True)
