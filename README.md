# Admissions Application Review Assistant

AI-powered university admissions application review tool. Combines manual reviewer assessments with Kindo AI agent analysis to provide thorough, consistent applicant evaluations.

## Features

- **Applicant Management** — add, view, and track applicants through the review pipeline
- **AI-Powered Reviews** — automated holistic evaluation via the Kindo agent platform
- **Manual Reviews** — structured scoring forms for human reviewers
- **Dashboard** — pipeline overview with status breakdowns
- **Light/Dark Theme** — toggle between light and dark modes
- **Context Help** — per-page help panels accessible from the ? button

## Quick Start

```bash
# Clone and start
docker compose up --build

# Open in browser
open http://localhost:8000
```

Default credentials: `admin` / `admin`

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing key (auto-generated if unset) |
| `KINDO_API_KEY` | Kindo platform API key for AI reviews |
| `KINDO_REVIEW_AGENT_ID` | Agent ID for the application review agent |

## Kindo Agent

See `agent/agent-config.yaml` for the agent index and `agent/agents/application-review-agent.yaml` for the full agent configuration including system prompt and I/O schemas.

## Tech Stack

- **Backend:** Python / Flask
- **Database:** SQLite (WAL mode)
- **Server:** Gunicorn with preloaded app
- **AI:** Kindo Agent API
- **Deployment:** Docker
