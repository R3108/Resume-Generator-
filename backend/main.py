import os
import traceback
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .crew import generate_resume
from .internship_crew import _is_real_key, _validate_serper, search_internships
from .models import (
    InternshipSearchInput,
    InternshipSearchOutput,
    ResumeInput,
    ResumeOutput,
)

load_dotenv()

app = FastAPI(
    title="AI Resume Generator",
    description="Generate professional resumes using CrewAI agents",
    version="1.0.0",
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# ── API Routes ────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check() -> dict:
    """Health-check endpoint."""
    return {"status": "ok", "message": "Resume Generator API is running"}


@app.post("/api/generate-resume", response_model=ResumeOutput)
async def create_resume(resume_input: ResumeInput) -> ResumeOutput:
    """
    Generate a professional resume using CrewAI agents.
    Accepts structured user data and returns a polished Markdown resume + tips.
    """
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key.startswith("YOUR_"):
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY in your .env file.",
        )

    try:
        result = generate_resume(resume_input.model_dump())
        return ResumeOutput(**result)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Resume generation failed: {str(exc)}",
        ) from exc


@app.get("/api/serper-status")
async def serper_status() -> dict:
    """
    Check whether a valid, working SERPER_API_KEY is configured.
    Returns:
        { "active": bool, "message": str }
    """
    from dotenv import load_dotenv

    load_dotenv(override=True)

    key = os.getenv("SERPER_API_KEY", "").strip()

    if not key or not _is_real_key(key):
        return {
            "active": False,
            "message": "SERPER_API_KEY is not set or is a placeholder. AI-curated results will be used.",
        }

    ok = _validate_serper(key)
    if ok:
        return {
            "active": True,
            "message": "Serper API key is valid. Live job-board search is enabled.",
        }
    else:
        return {
            "active": False,
            "message": "SERPER_API_KEY is set but was rejected by Serper (check the key at serper.dev). AI-curated results will be used.",
        }


@app.post("/api/search-internships", response_model=InternshipSearchOutput)
async def find_internships(
    search_input: InternshipSearchInput,
) -> InternshipSearchOutput:
    """
    Analyse the generated resume and search for matching internship opportunities.
    Uses a two-agent CrewAI crew: one extracts the candidate profile and builds
    search queries, the other hunts for real listings via SerperDevTool (when a
    SERPER_API_KEY is configured) or produces AI-curated suggestions as a fallback.
    """
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key.startswith("YOUR_"):
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY in your .env file.",
        )

    try:
        result = search_internships(
            resume_text=search_input.resume_text,
            preferred_location=search_input.preferred_location or "",
            num_results=search_input.num_results,
            extra_keywords=list(search_input.extra_keywords or []),
        )
        return InternshipSearchOutput(**result)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internship search failed: {str(exc)}",
        ) from exc


# ── Serve static frontend ──────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

if FRONTEND_DIR.is_dir():

    @app.get("/", include_in_schema=False)
    async def root() -> FileResponse:
        """Serve the main HTML file."""
        html_file = FRONTEND_DIR / "index.html"
        return FileResponse(str(html_file))

    # Mount static files last so API routes take priority
    app.mount(
        "/static", StaticFiles(directory=str(FRONTEND_DIR), html=False), name="static"
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
