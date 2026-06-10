import os
import json
from textwrap import dedent
from dotenv import load_dotenv 
from crewai import Agent, Task, Crew, Process, LLM  

load_dotenv()

GEMINI_MODEL: str = os.getenv("GEMINI_MODEL_NAME", "gemini/gemini-2.5-flash")

# LiteLLM (used internally by CrewAI) reads GEMINI_API_KEY from the environment
_key: str = os.getenv("GEMINI_API_KEY", "")
if _key:
    os.environ["GEMINI_API_KEY"] = _key


def _build_llm() -> "LLM":
    return LLM(
        model=GEMINI_MODEL,
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.7,
    )


def format_resume_data(data: dict) -> str:
    """Convert the resume input dict into a readable prompt-friendly string."""
    lines = []
    lines.append(f"Full Name: {data['full_name']}")
    lines.append(f"Email: {data['email']}")
    lines.append(f"Phone: {data['phone']}")
    lines.append(f"Location: {data['location']}")

    if data.get("linkedin"):
        lines.append(f"LinkedIn: {data['linkedin']}")
    if data.get("portfolio"):
        lines.append(f"Portfolio/Website: {data['portfolio']}")

    lines.append(f"\nCareer Objective / Summary:\n{data['objective']}")

    if data.get("experiences"):
        lines.append("\nWork Experience:")
        for exp in data["experiences"]:
            lines.append(f"  - {exp['role']} at {exp['company']} ({exp['duration']})")
            lines.append(f"    {exp['description']}")

    if data.get("education"):
        lines.append("\nEducation:")
        for edu in data["education"]:
            gpa = f", GPA: {edu['gpa']}" if edu.get("gpa") else ""
            lines.append(
                f"  - {edu['degree']} — {edu['institution']} ({edu['year']}{gpa})"
            )

    if data.get("skills"):
        lines.append(f"\nSkills: {', '.join(data['skills'])}")

    if data.get("certifications"):
        lines.append(f"\nCertifications: {', '.join(data['certifications'])}")

    lines.append(f"\nPreferred Resume Style: {data.get('template_style', 'modern')}")
    return "\n".join(lines)


def generate_resume(resume_data: dict) -> dict:
    """
    Run the CrewAI crew for resume generation.
    Returns a dict with keys: generated_resume (str), tips (list[str]), word_count (int)
    """
    llm = _build_llm()
    formatted_input = format_resume_data(resume_data)

    # ── Agent 1: Resume Writer ────────────────────────────────────────────────
    writer_agent = Agent(
        role="Expert Resume Writer",
        goal=(
            "Craft a compelling, ATS-optimized resume that highlights the candidate's "
            "strengths, quantifies achievements, and is tailored to modern hiring standards."
        ),
        backstory=dedent(
            """
            You are a senior resume writer with 15+ years of experience helping
            professionals land interviews at top companies. You understand ATS systems,
            keyword optimization, and how to present experience in a way that grabs
            attention in under 10 seconds.
            """
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ── Agent 2: Resume Critic & Formatter ───────────────────────────────────
    formatter_agent = Agent(
        role="Resume Critic and Professional Formatter",
        goal=(
            "Review the drafted resume, improve clarity, fix any weaknesses, ensure "
            "consistent formatting in clean Markdown, and provide 3-5 actionable tips."
        ),
        backstory=dedent(
            """
            You are a meticulous resume coach and former HR director who has reviewed
            over 10,000 resumes. You have a sharp eye for vague language, missing
            metrics, and formatting inconsistencies. You always output resumes in
            professional, clean Markdown.
            """
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ── Task 1: Write Resume ──────────────────────────────────────────────────
    write_task = Task(
        description=dedent(
            f"""
            Using the candidate information below, draft a complete, professional resume.

            CANDIDATE DATA:
            {formatted_input}

            Requirements:
            - Use clean Markdown formatting with clear sections
            - Start with a strong header (name, contact info)
            - Write a punchy professional summary (3-4 sentences)
            - For each work experience, write 3-5 bullet points using action verbs and
              quantified results where possible
            - Include an Education section
            - List skills grouped by category if there are many
            - Adapt tone to the preferred style: {resume_data.get("template_style", "modern")}
            - Aim for 400-600 words
            """
        ),
        expected_output=(
            "A complete, well-structured resume in Markdown format covering all sections: "
            "Header, Summary, Experience, Education, Skills, and optional Certifications."
        ),
        agent=writer_agent,
    )

    # ── Task 2: Review & Format ───────────────────────────────────────────────
    format_task = Task(
        description=dedent(
            """
            Review the resume draft produced by the Resume Writer.

            Your job:
            1. Fix any weak or vague language - make every bullet point impactful
            2. Ensure consistent Markdown formatting throughout
            3. Check that sections are in the correct professional order
            4. Improve the professional summary if needed
            5. Provide 3-5 concrete improvement tips AS A SEPARATE JSON BLOCK at the
               very end of your response, in this exact format:

            ```json
            {
              "tips": [
                "tip 1",
                "tip 2",
                "tip 3"
              ]
            }
            ```

            Output the final polished resume in full Markdown BEFORE the JSON block.
            """
        ),
        expected_output=(
            "A polished, final Markdown resume followed by a JSON block containing "
            "a 'tips' array with 3-5 actionable improvement suggestions."
        ),
        agent=formatter_agent,
        context=[write_task],
    )

    # ── Crew ─────────────────────────────────────────────────────────────────
    crew = Crew(
        agents=[writer_agent, formatter_agent],
        tasks=[write_task, format_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    # CrewOutput.raw holds the plain-text string from the last task
    raw_output: str = result.raw if hasattr(result, "raw") else str(result)

    # Parse the tips JSON block from the end of the formatter output
    tips = []
    resume_text: str = raw_output
    try:
        json_start: int = raw_output.rfind("```json")
        json_end: int = raw_output.rfind("```", json_start + 1)
        if json_start != -1 and json_end != -1:
            # Use substring extraction to avoid Pyre2 slice complaints
            after_marker: str = raw_output[json_start + 7:]
            json_str: str = after_marker[: json_end - json_start - 7].strip()
            parsed = json.loads(json_str)
            tips = parsed.get("tips", [])
            resume_text = raw_output[:json_start].strip()
    except (json.JSONDecodeError, ValueError, KeyError):
        tips = [
            "Quantify achievements with numbers and percentages.",
            "Tailor your resume for each job application.",
            "Keep your resume to one or two pages maximum.",
        ]

    word_count: int = len(resume_text.split())

    return {
        "generated_resume": resume_text,
        "tips": tips,
        "word_count": word_count,
    }
