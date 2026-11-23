"""API routes — health check and JSON endpoints."""

import logging

from flask import Blueprint, jsonify, request

from app.routes.auth import login_required
from app.services import applicant_service

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@api_bp.route("/applicants")
@login_required
def api_list_applicants():
    status_filter = request.args.get("status", "all")
    try:
        apps = applicant_service.list_applicants(status=status_filter)
    except Exception as exc:
        logger.exception("api_list_applicants: service error — %s", exc)
        return jsonify({"error": "Failed to load applicants", "detail": str(exc)}), 500

    if apps is None:
        apps = []
    return jsonify({"applicants": apps})


@api_bp.route("/stats")
@login_required
def api_stats():
    try:
        stats = applicant_service.get_applicant_stats()
    except Exception as exc:
        logger.exception("api_stats: service error — %s", exc)
        return jsonify({"error": "Failed to load stats", "detail": str(exc)}), 500

    return jsonify(stats)
