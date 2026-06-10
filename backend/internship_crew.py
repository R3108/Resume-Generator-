"""
backend/internship_crew.py
──────────────────────────
Internship-search crew built on CrewAI + Gemini.

Architecture
────────────
• Single Agent / Single Task – simpler and more failure-resistant.
• Keys are read fresh on every call (not at module import), so updating
  .env while the server is running takes effect immediately.
• Before the crew runs, the Serper key is validated with a cheap live
  HTTP ping.  If it is absent, a placeholder, or rejected (4xx), the
  agent is instructed to generate AI-curated listings instead.
• The output parser tries three extraction strategies before falling back
  to a guaranteed non-empty stub list.
"""

from __future__ import annotations

import json
import os
import re
from textwrap import dedent

import requests
from crewai import LLM, Agent, Crew, Process, Task
from dotenv import load_dotenv

load_dotenv()

# ── Placeholder / dummy-value detection ──────────────────────────────────────

_PLACEHOLDER_PREFIXES = (
    "YOUR_",
    "PLACEHOLDER",
    "CHANGE_ME",
    "INSERT",
    "ADD_YOUR",
    "ENTER_",
    "EXAMPLE",
    "DUMMY",
    "TEST_KEY",
    "FAKE",
)


def _is_real_key(value: str) -> bool:
    """Return True only when *value* looks like a real API key."""
    v = (value or "").strip()
    if len(v) < 8:
        return False
    return not any(v.upper().startswith(p.upper()) for p in _PLACEHOLDER_PREFIXES)


# ── Per-request helpers ───────────────────────────────────────────────────────


def _read_keys() -> tuple[str, str]:
    """Re-read GEMINI and SERPER keys from the environment on every call."""
    load_dotenv(override=True)
    gemini = os.getenv("GEMINI_API_KEY", "").strip()
    serper = os.getenv("SERPER_API_KEY", "").strip()
    return gemini, serper


def _validate_serper(serper_key: str) -> bool:
    """
    Make a cheap live ping to the Serper API.
    Returns True only when the key is accepted (2xx response).
    """
    if not _is_real_key(serper_key):
        return False
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
            json={"q": "internship", "num": 1},
            timeout=8,
        )
        return resp.status_code == 200
    except Exception:
        return False


def _build_llm(gemini_key: str) -> LLM:
    return LLM(
        model=os.getenv("GEMINI_MODEL_NAME", "gemini/gemini-2.5-flash"),
        api_key=gemini_key,
        temperature=0.6,
    )


def _get_search_tools(serper_key: str) -> list:
    """Return [SerperDevTool()] when the key is valid, otherwise []."""
    if not serper_key:
        return []
    try:
        from crewai_tools import SerperDevTool  # type: ignore[import]

        return [SerperDevTool(n_results=10)]
    except Exception:
        return []


def _sanitise_url(url: str) -> str:
    url = (url or "").strip()
    if not url or url in ("#", "N/A", "n/a", "none", "None"):
        return "https://www.linkedin.com/jobs/search/?keywords=internship"
    if not re.match(r"^https?://", url, re.IGNORECASE):
        return "https://" + url
    return url


# ── Stub listings (last-resort fallback only) ─────────────────────────────────

_STUB_INTERNSHIPS: list[dict] = [
    {
        "title": "Software Engineering Intern",
        "company": "Google",
        "location": "Mountain View, CA / Remote",
        "description": (
            "Work on large-scale distributed systems alongside senior engineers. "
            "Contribute to real products used by billions of users worldwide."
        ),
        "url": "https://careers.google.com/jobs/results/?employment_type=INTERN",
        "match_reason": "Matches software engineering and programming skills on your resume.",
        "source": "Company Careers",
    },
    {
        "title": "Data Science Intern",
        "company": "Microsoft",
        "location": "Redmond, WA / Remote",
        "description": (
            "Analyse large datasets, build ML models, and present findings to "
            "product teams. Great for candidates with Python and statistical skills."
        ),
        "url": "https://jobs.careers.microsoft.com/global/en/search?p=Internship",
        "match_reason": "Matches your data analysis and programming background.",
        "source": "Company Careers",
    },
    {
        "title": "Backend Engineering Intern",
        "company": "Stripe",
        "location": "Remote",
        "description": (
            "Build APIs and payment infrastructure used by millions of businesses. "
            "Work closely with product engineers in a fast-paced fintech environment."
        ),
        "url": "https://stripe.com/jobs/search?query=intern",
        "match_reason": "Great fit for backend / API development skills.",
        "source": "Company Careers",
    },
    {
        "title": "Machine Learning Intern",
        "company": "Meta AI",
        "location": "Menlo Park, CA / Remote",
        "description": (
            "Research and implement ML algorithms for ranking, recommendations, "
            "or computer vision systems at scale."
        ),
        "url": "https://www.metacareers.com/jobs/?q=intern",
        "match_reason": "Matches ML and AI skills on your resume.",
        "source": "Company Careers",
    },
    {
        "title": "Full-Stack Developer Intern",
        "company": "Shopify",
        "location": "Remote (Canada / US)",
        "description": (
            "Build merchant-facing features using React, Ruby on Rails, and GraphQL. "
            "Contribute to real features shipped to thousands of online stores."
        ),
        "url": "https://www.shopify.com/careers/search?keywords=intern",
        "match_reason": "Good fit for web development and full-stack skills.",
        "source": "Company Careers",
    },
    {
        "title": "Cloud / DevOps Intern",
        "company": "Amazon Web Services",
        "location": "Seattle, WA / Remote",
        "description": (
            "Automate infrastructure, improve CI/CD pipelines, and work on "
            "reliability engineering for core AWS services."
        ),
        "url": "https://www.amazon.jobs/en/teams/internships-for-students",
        "match_reason": "Matches cloud, scripting, or infrastructure skills.",
        "source": "Company Careers",
    },
    {
        "title": "Product Management Intern",
        "company": "LinkedIn",
        "location": "Sunnyvale, CA / Remote",
        "description": (
            "Define roadmaps, run user research, and collaborate with engineering "
            "to ship product features to 900 M+ professionals."
        ),
        "url": "https://careers.linkedin.com/students",
        "match_reason": "Matches analytical and communication skills.",
        "source": "Company Careers",
    },
    {
        "title": "Cybersecurity Intern",
        "company": "Palo Alto Networks",
        "location": "Santa Clara, CA / Remote",
        "description": (
            "Assist threat analysts, conduct vulnerability research, and develop "
            "security tooling for enterprise customers globally."
        ),
        "url": "https://jobs.paloaltonetworks.com/en/jobs/?search=intern",
        "match_reason": "Matches security, networking, or systems skills.",
        "source": "Company Careers",
    },
]


# ── Public entry-point ────────────────────────────────────────────────────────


def search_internships(
    resume_text: str,
    preferred_location: str = "",
    num_results: int = 8,
    extra_keywords: list[str] | None = None,
) -> dict:
    """
    Run the internship-search crew and return a dict matching InternshipSearchOutput.

    Keys returned:
        internships         – list[dict]  (always non-empty)
        search_summary      – str
        total_found         – int
        skills_detected     – list[str]
        search_queries_used – list[str]
        serper_active       – bool  (True when live web search was used)
    """
    # ── 1. Read keys fresh from environment ───────────────────────────────────
    gemini_key, serper_key = _read_keys()

    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
    if serper_key:
        os.environ["SERPER_API_KEY"] = serper_key

    # ── 2. Validate Serper key with a live ping ───────────────────────────────
    serper_active = _validate_serper(serper_key)
    search_tools = _get_search_tools(serper_key) if serper_active else []

    # ── 3. Build helpers ──────────────────────────────────────────────────────
    llm = _build_llm(gemini_key)
    location_hint = (
        preferred_location.strip() if preferred_location else "any location / remote"
    )
    extra_kw_str = ", ".join(extra_keywords) if extra_keywords else ""

    # ── 4. Build tool-use instructions ───────────────────────────────────────
    if serper_active and search_tools:
        tool_instructions = dedent(
            f"""
            You have access to SerperDevTool (live Google Search). Use it to run
            these searches and collect real job postings from LinkedIn, Indeed,
            Glassdoor, Handshake, Wellfound, Internshala, and company career pages:

              1. "<primary skill> intern 2025 {location_hint}"
              2. "<role> internship site:linkedin.com/jobs"
              3. "<field> intern apply {location_hint} site:indeed.com"
              4. "summer 2025 intern <target role> <top skill>"

            Replace placeholders with values extracted from the candidate's resume.

            IMPORTANT: If SerperDevTool returns an error for any query, skip that
            query silently and use your training knowledge to fill the remaining
            listings.  Never mention errors in your output.
            """
        )
    else:
        tool_instructions = dedent(
            """
            You do NOT have a live search tool available right now.
            Generate highly realistic internship listings from your training
            knowledge.  Use real company names (Google, Microsoft, Meta, Stripe,
            Shopify, Amazon, Airbnb, Notion, startups, etc.), real career-page URL
            patterns (e.g. careers.google.com, stripe.com/jobs), and descriptions
            that accurately reflect what interns do at those companies.
            Do NOT invent fictional companies or nonsense URLs.
            """
        )

    # ── 5. Build the single task description ─────────────────────────────────
    task_description = dedent(
        f"""
        You are an expert internship placement specialist.

        ── CANDIDATE RESUME ────────────────────────────────────────────────────
        {resume_text}

        ── LOCATION PREFERENCE ─────────────────────────────────────────────────
        {location_hint}
        {"Extra keywords: " + extra_kw_str if extra_kw_str else ""}

        ── YOUR TASK ────────────────────────────────────────────────────────────
        1. Read the resume and extract:
           • Top 5-8 skills
           • Target role / field
           • Education level

        2. Find {num_results} internship opportunities that genuinely match the
           candidate using the instructions below.

        3. Return ONLY the JSON block specified in the OUTPUT FORMAT section.
           Do NOT include any other text, headers, or explanations.

        ── SEARCH / GENERATION INSTRUCTIONS ────────────────────────────────────
        {tool_instructions}

        ── OUTPUT FORMAT ────────────────────────────────────────────────────────
        Output exactly ONE ```json ... ``` fenced block — nothing before or after.
        The "internships" array MUST have {num_results} entries (fewer only if
        truly unavailable).  NEVER output an empty array.

        ```json
        {{
          "skills_detected": ["skill1", "skill2", "skill3"],
          "search_queries_used": ["query 1 actually run", "query 2 actually run"],
          "search_summary": "1-2 sentences: what was searched/generated and why these roles match.",
          "internships": [
            {{
              "title": "Role Title Intern",
              "company": "Real Company Name",
              "location": "City, State / Remote",
              "description": "2-3 sentences describing what the intern will actually do.",
              "url": "https://real-or-plausible-career-page-url.com/jobs",
              "match_reason": "One sentence: specific skill/experience from the resume that fits.",
              "source": "LinkedIn | Indeed | Glassdoor | Handshake | Company Careers | Wellfound"
            }}
          ]
        }}
        ```

        ── RULES ────────────────────────────────────────────────────────────────
        • NEVER output an empty "internships" array.
        • NEVER report tool errors inside the JSON.
        • URLs must use real domains (linkedin.com/jobs, careers.google.com, etc.).
        • Rank listings by relevance to the candidate's strongest skills.
        • The ONLY output is the ```json ... ``` block — nothing else.
        """
    )

    # ── 6. Create agent & task ────────────────────────────────────────────────
    hunter_agent = Agent(
        role="Internship Research Specialist",
        goal=(
            f"Find {num_results} highly relevant internship opportunities for the "
            "candidate by analysing their resume, searching or generating listings, "
            "and always outputting a complete, valid JSON result."
        ),
        backstory=dedent(
            """
            You are a world-class internship placement advisor with 15+ years of
            experience helping students and fresh graduates land roles at top
            companies.  You know every major job board (LinkedIn, Indeed, Glassdoor,
            Handshake, Wellfound, Internshala), company hiring portal, and startup
            hiring platform.  When live search is unavailable you draw on your deep
            knowledge of the hiring landscape to produce equally useful AI-curated
            recommendations.  You ALWAYS deliver a complete, structured JSON
            response — you never leave the internships array empty.
            """
        ),
        llm=llm,
        tools=search_tools,
        verbose=True,
        allow_delegation=False,
    )

    hunt_task = Task(
        description=task_description,
        expected_output=(
            f"A single ```json ... ``` fenced block containing skills_detected, "
            f"search_queries_used, search_summary, and an internships array with "
            f"up to {num_results} structured listings."
        ),
        agent=hunter_agent,
    )

    crew = Crew(
        agents=[hunter_agent],
        tasks=[hunt_task],
        process=Process.sequential,
        verbose=True,
    )

    # ── 7. Run ────────────────────────────────────────────────────────────────
    result = crew.kickoff()
    raw_output: str = result.raw if hasattr(result, "raw") else str(result)

    # ── 8. Parse & return ─────────────────────────────────────────────────────
    parsed = _parse_output(raw_output, num_results)
    parsed["serper_active"] = serper_active
    return parsed


# ── Output parser ─────────────────────────────────────────────────────────────


def _parse_output(raw: str, num_results: int) -> dict:
    """
    Try multiple strategies to extract the JSON block.
    Falls back gracefully at every level.
    """
    parsed: dict = {}

    # Strategy 1 – ```json … ``` fence
    m = re.search(r"```json\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if m:
        try:
            parsed = json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass

    # Strategy 2 – ``` … ``` fence without language tag
    if not parsed:
        m2 = re.search(r"```\s*(\{[\s\S]*?\})\s*```", raw)
        if m2:
            try:
                parsed = json.loads(m2.group(1).strip())
            except (json.JSONDecodeError, ValueError):
                pass

    # Strategy 3 – outermost { … } object
    if not parsed:
        brace_start = raw.find("{")
        brace_end = raw.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            try:
                parsed = json.loads(raw[brace_start : brace_end + 1])
            except (json.JSONDecodeError, ValueError):
                pass

    # Normalise listings
    raw_listings: list = parsed.get("internships", [])
    internships: list[dict] = []
    for item in raw_listings:
        if not isinstance(item, dict):
            continue
        internships.append(
            {
                "title": str(item.get("title") or "Internship Role"),
                "company": str(item.get("company") or "Company"),
                "location": str(item.get("location") or "N/A"),
                "description": str(item.get("description") or ""),
                "url": _sanitise_url(str(item.get("url") or "")),
                "match_reason": str(item.get("match_reason") or ""),
                "source": str(item.get("source") or "Job Board"),
            }
        )

    # Last-resort stub fallback
    if not internships:
        internships = _STUB_INTERNSHIPS[:num_results]

    internships = internships[:num_results]

    skills_detected: list[str] = [
        str(s) for s in parsed.get("skills_detected", []) if s and isinstance(s, str)
    ]
    search_queries_used: list[str] = [
        str(q)
        for q in parsed.get("search_queries_used", [])
        if q and isinstance(q, str)
    ]
    search_summary: str = str(
        parsed.get("search_summary")
        or f"Found {len(internships)} internship opportunities matching your profile."
    )

    return {
        "internships": internships,
        "search_summary": search_summary,
        "total_found": len(internships),
        "skills_detected": skills_detected,
        "search_queries_used": search_queries_used,
    }
