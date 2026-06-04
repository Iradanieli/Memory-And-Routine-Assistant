from flask import Blueprint, jsonify, request

from services.assistant_service import answer_question


assistant_router = Blueprint("assistant", __name__)


@assistant_router.post("/api/ask")
def api_ask():
    payload = request.get_json(silent=True) or {}
    response, status_code = answer_question(payload)
    return jsonify(response), status_code
