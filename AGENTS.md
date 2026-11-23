# AGENTS.md — Admissions Application Review Assistant

## Repository Layout

```
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py          # SQLite schema + init
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Login, logout, register
│   │   ├── main.py              # Dashboard, applicants, reviews
│   │   └── api.py               # Health check, JSON endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── applicant_service.py # Applicant CRUD
│   │   ├── review_service.py    # Review CRUD
│   │   └── kindo_service.py     # Kindo AI agent integration
│   ├── templates/
│   │   ├── layouts/
│   │   │   └── base.html
│   │   ├── pages/
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   ├── dashboard.html
│   │   │   ├── applicants.html
│   │   │   ├── new_applicant.html
│   │   │   ├── view_applicant.html
│   │   │   └── getting_started.html
│   │   └── errors/
│   │       └── 500.html
│   └── static/
│       └── css/
│           └── style.css
├── agent/
│   ├── agent-config.yaml        # Agent index
│   └── agents/
│       └── application-review-agent.yaml
├── wsgi.py                      # WSGI entry point
├── gunicorn.conf.py             # Gunicorn config
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Kindo Agent Integration

The application integrates with one Kindo AI agent:

| Agent | Env Var | Service File | Purpose |
|---|---|---|---|
| Application Review Agent | `KINDO_REVIEW_AGENT_ID` | `app/services/kindo_service.py` | Holistic applicant evaluation with structured scoring |

The agent receives applicant data as a JSON payload and returns structured
scores (academic, essay, extracurricular, overall on a 1-10 scale) plus an
admit/waitlist/deny recommendation.

When `KINDO_API_KEY` is not configured, the service falls back to a
deterministic mock review for development purposes.

## Security Notes

- Session cookies use `SameSite=Lax` with configurable path and secure flag
- `SECRET_KEY` is generated and persisted on first boot (see `wsgi.py`)
- `gunicorn.conf.py` uses `preload_app = True` for multi-worker session stability
- No hardcoded credentials in production — default admin account is for initial setup only
