from flask import Blueprint, jsonify


health_router = Blueprint("health", __name__)


@health_router.get("/api/health")
def health():
    return jsonify({"status": "ok"})
