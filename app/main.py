from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import endpoints
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PageRAG AI Platform")

app.include_router(endpoints.router, prefix="/api")

# Mount static files for the frontend
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
