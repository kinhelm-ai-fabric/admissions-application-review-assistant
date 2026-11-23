"""Kindo AI agent integration for application reviews."""

import json
import logging
import os

import requests

logger = logging.getLogger(__name__)

KINDO_API_URL = "https://api.kindo.ai/v1/chat/completions"

_SYSTEM_PROMPT = """You are an expert university admissions reviewer. You evaluate applicant profiles holistically and provide structured, fair assessments.

You will receive a JSON request with applicant data. Evaluate the applicant based on:
1. Academic strength (GPA, test scores relative to intended major competitiveness)
2. Essay quality (clarity, authenticity, insight, writing skill)
3. Extracurricular involvement (leadership, depth, alignment with goals)
4. Overall fit (potential contribution, growth trajectory)

Score each category from 1-10. Provide a clear recommendation.

Return ONLY valid JSON with this exact schema:
{
  "academic_score": <integer 1-10>,
  "essay_score": <integer 1-10>,
  "extracurricular_score": <integer 1-10>,
  "overall_score": <integer 1-10>,
  "recommendation": "<admit|waitlist|deny>",
  "strengths": "<2-3 sentence summary of key strengths>",
  "concerns": "<2-3 sentence summary of concerns or areas for improvement>",
  "notes": "<1-2 sentence overall assessment>"
}

Guidelines:
- Be fair and consistent. Do not penalize for factors outside the applicant's control.
- A 3.5+ GPA is strong; a 3.8+ is exceptional. Adjust for intended major difficulty.
- Value essay authenticity over polish. Look for self-awareness and genuine reflection.
- Depth in fewer activities is better than surface-level participation in many.
- Consider the whole applicant. A lower GPA can be offset by exceptional essays or activities.
- Use "waitlist" when the applicant is competitive but not clearly above the threshold.
- When data is missing or minimal, note it in concerns rather than penalizing scores heavily.

Return ONLY valid JSON. No markdown fences, no prose outside the JSON object."""


def review_applicant(applicant):
    """Send applicant data to the Kindo review agent and return structured scores.

    Returns a dict with scores and recommendation, or None on failure.
    Falls back to a mock review when KINDO_API_KEY is not configured.
    """
    api_key = os.environ.get("KINDO_API_KEY", "")
    agent_id = os.environ.get("KINDO_REVIEW_AGENT_ID", "")

    request_payload = json.dumps({
        "first_name": applicant.get("first_name", ""),
        "last_name": applicant.get("last_name", ""),
        "email": applicant.get("email", ""),
        "gpa": applicant.get("gpa"),
        "test_score": applicant.get("test_score"),
        "intended_major": applicant.get("intended_major", ""),
        "essay": applicant.get("essay", ""),
        "extracurriculars": applicant.get("extracurriculars", ""),
    })

    if not api_key or not agent_id:
        logger.warning("Kindo API key or agent ID not configured — using mock review")
        return _mock_review(applicant)

    try:
        resp = requests.post(
            KINDO_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": agent_id,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": request_payload},
                ],
            },
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # Strip markdown fences if the model wraps them
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        content = content.strip()

        result = json.loads(content)
        return _validate_review(result)

    except Exception as exc:
        logger.exception("Kindo agent call failed — %s", exc)
        return None


def _validate_review(result):
    """Ensure the review dict has all required fields with valid values."""
    required = [
        "academic_score", "essay_score", "extracurricular_score",
        "overall_score", "recommendation", "strengths", "concerns", "notes",
    ]
    for key in required:
        if key not in result:
            return None

    for score_key in ["academic_score", "essay_score", "extracurricular_score", "overall_score"]:
        try:
            val = int(result[score_key])
            result[score_key] = max(1, min(10, val))
        except (ValueError, TypeError):
            return None

    if result["recommendation"] not in ("admit", "waitlist", "deny"):
        result["recommendation"] = "waitlist"

    return result


def _mock_review(applicant):
    """Generate a deterministic mock review for development without Kindo API."""
    gpa = applicant.get("gpa") or 0
    essay = applicant.get("essay", "")
    extras = applicant.get("extracurriculars", "")

    academic = min(10, max(1, int(gpa * 2.5))) if gpa else 5
    essay_score = min(10, max(1, len(essay) // 50 + 3)) if essay else 4
    extra_score = min(10, max(1, len(extras) // 30 + 3)) if extras else 4
    overall = round((academic + essay_score + extra_score) / 3)

    if overall >= 7:
        rec = "admit"
    elif overall >= 5:
        rec = "waitlist"
    else:
        rec = "deny"

    return {
        "academic_score": academic,
        "essay_score": essay_score,
        "extracurricular_score": extra_score,
        "overall_score": overall,
        "recommendation": rec,
        "strengths": "Mock review — configure KINDO_API_KEY and KINDO_REVIEW_AGENT_ID for AI-powered reviews.",
        "concerns": "This is a placeholder review generated without the Kindo AI agent.",
        "notes": f"Mock assessment based on GPA={gpa}. Connect the Kindo agent for real evaluations.",
    }
