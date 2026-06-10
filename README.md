# AI Resume Generator

Generate polished, professional resumes and discover matching internships — powered by [CrewAI](https://www.crewai.com/) agents and Google's Gemini models.

The app pairs a FastAPI backend with a lightweight static frontend. You fill in your details, and a crew of AI agents writes a clean Markdown resume plus tailored improvement tips. A second crew can then analyse that resume and surface relevant internship listings, using live job-board results when a Serper API key is configured.

## Features

- **AI resume generation** — turns structured input (experience, education, skills, certifications) into a polished Markdown resume with `modern`, `minimal`, or `professional` styling.
- **Improvement tips** — every resume comes with actionable suggestions and a word count.
- **Internship search** — a two-agent crew extracts your profile, builds search queries, and finds matching internships from LinkedIn, Indeed, Glassdoor, and more.
- **Live or curated results** — uses real Google Search results via [Serper](https://serper.dev) when a key is set; otherwise falls back to AI-curated suggestions.
- **Self-contained UI** — static HTML/CSS/JS frontend served directly by the backend; no separate build step.
- **Interactive API docs** — auto-generated Swagger UI at `/docs`.

## Tech stack

- **Backend:** Python, FastAPI, Uvicorn, Pydantic
- **AI:** CrewAI + CrewAI Tools, Google Gemini (`gemini/gemini-2.5-flash` by default)
- **Search:** SerperDevTool (optional)
- **Frontend:** Vanilla HTML / CSS / JavaScript

## Requirements

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) (required)
- A [Serper API key](https://serper.dev) (optional — enables live job-board search; 2,500 free searches/month)

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/R3108/Resume-Generator-.git
cd Resume-Generator-

# 2. (Recommended) create and activate a virtual environment
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env        # Windows: copy .env.example .env
# then edit .env and add your keys
```

### Environment variables

| Variable             | Required | Description                                                        |
| -------------------- | -------- | ------------------------------------------------------------------ |
| `GEMINI_API_KEY`     | Yes      | Google Gemini API key used to generate resumes and search.         |
| `SERPER_API_KEY`     | No       | Serper key for live job-board search. Falls back to AI curation.   |
| `GEMINI_MODEL_NAME`  | No       | Override the model (default: `gemini/gemini-2.5-flash`).           |
| `PORT`               | No       | Server port (default: `8000`).                                     |

## Running the app

```bash
python run.py
```

This starts the server, prints any configuration warnings, and opens your browser automatically.

Useful flags:

```bash
python run.py --port 8080          # custom port
python run.py --host 0.0.0.0       # expose on your network
python run.py --no-browser         # don't auto-open the browser
python run.py --no-reload          # disable auto-reload
```

Once running:

- **App:** http://127.0.0.1:8000
- **API docs (Swagger):** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/api/health

## API endpoints

| Method | Endpoint                    | Description                                              |
| ------ | --------------------------- | ------------------------------------------------------- |
| `GET`  | `/api/health`               | Health check.                                           |
| `POST` | `/api/generate-resume`      | Generate a resume from structured input.                |
| `POST` | `/api/search-internships`   | Find internships matching a generated resume.           |
| `GET`  | `/api/serper-status`        | Report whether a valid Serper key is configured.        |

See `/docs` for full request/response schemas.

## Project structure

```
Resume-Generator-/
├── backend/
│   ├── main.py              # FastAPI app, routes, static file serving
│   ├── crew.py              # Resume-generation CrewAI crew
│   ├── internship_crew.py   # Internship-search CrewAI crew + Serper integration
│   └── models.py            # Pydantic request/response models
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── run.py                   # Dev server launcher with env checks
├── requirements.txt
└── .env.example
```

## Notes

- Your `.env` file (with real API keys) is git-ignored and must **not** be committed.
- Without a `GEMINI_API_KEY`, resume generation and internship search return a `503`.
- Without a `SERPER_API_KEY`, internship search still works using AI-curated suggestions.

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file in this repository.
