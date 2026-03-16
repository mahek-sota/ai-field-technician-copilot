from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import machines, diagnosis
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered field technician assistant for industrial machine diagnostics",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(machines.router, prefix="/machines", tags=["machines"])
app.include_router(diagnosis.router, tags=["diagnosis"])


@app.get("/")
def root():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/health")
def health():
    return {"status": "healthy"}
