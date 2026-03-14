# SYSTEM SPECIFICATION (v1.0.0)

**Last Updated:** YYYY-MM-DD
**Status:** [Draft / Active / In-Testing / Completed]
**Primary Agent Owner:** [e.g., OpenHands / gpt-engineer]

---

## 1. Core Objective
[Provide a strict 1-2 sentence description of the exact goal. No conversational fluff.]
*Example: "Build a Python CLI tool that takes a YouTube URL, downloads the audio, and transcribes it using the Whisper API."*

## 2. Technical Stack & Constraints
[Agents love to invent dependencies. Lock them down here.]
* **Language:** [e.g., Python 3.11+]
* **Core Frameworks:** [e.g., Typer, yt-dlp, OpenAI]
* **Environment:** [e.g., Must run entirely locally without cloud databases]
* **HARD CONSTRAINT:** Do not use any frameworks or libraries not explicitly listed above without Orchestrator approval.

## 3. In-Scope Features (Strict Execution)
[Be hyper-specific. If it is not on this list, it does not exist.]
1. **Feature A:** Implement a CLI command `transcribe [URL]` that validates the URL format.
2. **Feature B:** Download audio in `.mp3` format to a temporary `/tmp/audio` directory.
3. **Feature C:** Send the `.mp3` to the Whisper API and save the response as `transcript.txt` in the current working directory.

## 4. OUT OF SCOPE (Anti-Hallucination Directives)
[This is the most important section. Explicitly list what the agents should NOT build to prevent feature creep.]
* **DO NOT** build a frontend web UI, dashboard, or HTML pages.
* **DO NOT** implement user authentication or login systems.
* **DO NOT** set up a database (e.g., SQLite, Postgres) to save history.
* **DO NOT** add support for platforms other than YouTube (e.g., Vimeo, Twitch).

## 5. Required File Structure
[Dictate exactly where files must go so agents don't lose them in the shared workspace.]
```text
/project_root
├── main.py          # CLI entry point
├── downloader.py    # Logic for yt-dlp
├── transcriber.py   # API wrapper for Whisper
├── requirements.txt # Dependency list
└── tests/           # PyTest test suite
```

## 6. Acceptance Criteria (Definition of Done)
[How the QA/Spec Guardian Agent knows the task is ready for the user.]
* `pytest tests/` runs and passes with 100% success.
* Running `python main.py <invalid_url>` gracefully returns a formatted error string, not a stack trace.
* The application successfully outputs a `transcript.txt` file given a valid URL.
