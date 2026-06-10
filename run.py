"""
run.py  —  Start the AI Resume Generator server
Usage:   python run.py
         python run.py --port 8080
         python run.py --host 0.0.0.0 --port 8000
"""

import argparse
import os
import sys
import webbrowser
from pathlib import Path


def check_env() -> list[str]:
    """Return a list of warning strings for missing / placeholder keys."""
    warnings = []
    env_file = Path(__file__).parent / ".env"

    if not env_file.exists():
        warnings.append(
            ".env file not found.  Copy .env.example → .env and fill in your keys."
        )
        return warnings

    from dotenv import load_dotenv

    load_dotenv(override=True)

    gemini = os.getenv("GEMINI_API_KEY", "")
    if not gemini or gemini.startswith("YOUR_"):
        warnings.append("GEMINI_API_KEY is not set.  Resume generation will not work.")

    serper = os.getenv("SERPER_API_KEY", "")
    if not serper or serper.startswith("YOUR_"):
        warnings.append(
            "SERPER_API_KEY is not set.  Internship search will use AI-curated "
            "suggestions instead of live job-board results.  "
            "Get a free key at https://serper.dev"
        )

    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Resume Generator — dev server")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Bind port (default: 8000)",
    )
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument(
        "--no-browser", action="store_true", help="Do not open browser automatically"
    )
    args = parser.parse_args()

    # ── Banner ────────────────────────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║        AI Resume Generator  ·  powered by CrewAI     ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    # ── Env checks ───────────────────────────────────────────────────────────
    warnings = check_env()
    if warnings:
        print("⚠  Configuration warnings:")
        for w in warnings:
            print(f"   • {w}")
        print()
    else:
        print("✓  Environment looks good.")
        print()

    url = f"http://{args.host}:{args.port}"
    print(f"▶  Starting server at  {url}")
    print(f"   API docs           {url}/docs")
    print(f"   Health check       {url}/api/health")
    print()
    print("   Press  Ctrl+C  to stop.")
    print()

    # ── Open browser after a short delay ─────────────────────────────────────
    if not args.no_browser:
        import threading
        import time

        def _open():
            time.sleep(1.5)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()

    # ── Launch uvicorn ────────────────────────────────────────────────────────
    try:
        import uvicorn
    except ImportError:
        print("ERROR: uvicorn is not installed.  Run:  pip install uvicorn[standard]")
        sys.exit(1)

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        reload_dirs=["backend", "frontend"],
        log_level="info",
    )


if __name__ == "__main__":
    main()
