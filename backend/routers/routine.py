from flask import Blueprint, jsonify, request

from services.routine_service import (
    create_event,
    create_task,
    dashboard_data,
    remove_event,
    schedule_data,
    set_task_done,
)


routine_router = Blueprint("routine", __name__)


@routine_router.get("/api/dashboard")
def api_dashboard():
    return jsonify(dashboard_data())


@routine_router.get("/api/schedule")
def api_schedule():
    return jsonify(schedule_data(request.args.get("month")))


@routine_router.post("/api/events")
def api_add_event():
    payload = request.get_json(silent=True) or {}
    response, status_code = create_event(payload)
    return jsonify(response), status_code


@routine_router.post("/api/tasks")
def api_add_task():
    payload = request.get_json(silent=True) or {}
    response, status_code = create_task(payload)
    return jsonify(response), status_code


@routine_router.delete("/api/events/<event_id>")
def api_delete_event(event_id):
    response, status_code = remove_event(event_id)
    return jsonify(response), status_code


@routine_router.post("/api/tasks/<task_id>/done")
def api_mark_task_done(task_id):
    response, status_code = set_task_done(task_id)
    return jsonify(response), status_code
