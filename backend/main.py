import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from backend.routers import chat, hr, interview


# -------------------
# 1. App
# -------------------
app = FastAPI(
    title   ="NexaraAI System",
    version ="1.0.0",
    docs_url="/docs",
)

# -------------------
# 2. Middleware
# -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins =["*"],
    allow_methods =["*"],
    allow_headers =["*"],
)

# -------------------
# 3. Routers
# -------------------
app.include_router(chat.router)
app.include_router(hr.router)
app.include_router(interview.router)

# -------------------
# 4. Static files
# -------------------
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


# -------------------
# 5. Pages
# -------------------
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")


@app.get("/hr/dashboard")
async def hr_dashboard():
    return FileResponse("frontend/hr_dashboard.html")
