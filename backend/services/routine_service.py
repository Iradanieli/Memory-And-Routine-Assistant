import calendar
from collections import Counter
from datetime import date
from pathlib import Path
from uuid import uuid4

from services.utils_service import (
    add_months,
    parse_date,
    parse_month,
    read_csv,
    row_by_id,
    sorted_by_date_time,
    write_csv,
)


BASE_DIR = Path(__file__).resolve().parent.parent
STRUCTURED_DIR = BASE_DIR / "structured"
EVENTS_FILE = STRUCTURED_DIR / "events.csv"
TODOS_FILE = STRUCTURED_DIR / "todos.csv"

EVENT_FIELDS = [
    "event_id",
    "title",
    "date",
    "time",
    "location",
    "related_person",
    "notes",
    "status",
]
TODO_FIELDS = ["task_id", "title", "date", "time", "priority", "status"]


def select_dashboard_day(events, todos):
    today = date.today()
    dated_rows = []
    for row in [*events, *todos]:
        row_date = parse_date(row.get("date"))
        if row_date:
            dated_rows.append(row_date)

    if today in dated_rows:
        return today, False

    future_dates = sorted(row_date for row_date in dated_rows if row_date > today)
    if future_dates:
        return future_dates[0], True

    if dated_rows:
        counts = Counter(dated_rows)
        return sorted(counts, key=lambda row_date: (-counts[row_date], row_date))[0], True

    return today, False


def dashboard_data():
    events = read_csv(EVENTS_FILE, EVENT_FIELDS)
    todos = read_csv(TODOS_FILE, TODO_FIELDS)
    selected_day, is_fallback_day = select_dashboard_day(events, todos)

    selected_events = [
        event
        for event in events
        if parse_date(event.get("date")) == selected_day
        and event.get("status", "").lower() != "cancelled"
    ]
    selected_todos = [
        todo
        for todo in todos
        if parse_date(todo.get("date")) == selected_day
        and todo.get("status", "").lower() not in {"done", "closed"}
    ]

    return {
        "events": sorted_by_date_time(selected_events),
        "todos": sorted_by_date_time(selected_todos),
        "all_events": sorted_by_date_time(events),
        "all_todos": sorted_by_date_time(todos),
        "selected_day": selected_day.isoformat(),
        "is_fallback_day": is_fallback_day,
        "today": date.today().isoformat(),
    }


def monthly_events(month_start):
    _, last_day = calendar.monthrange(month_start.year, month_start.month)
    month_end = month_start.replace(day=last_day)
    events = read_csv(EVENTS_FILE, EVENT_FIELDS)

    return sorted_by_date_time(
        [
            event
            for event in events
            if parse_date(event.get("date"))
            and month_start <= parse_date(event.get("date")) <= month_end
        ]
    )


def schedule_data(month):
    month_start = parse_month(month)
    return {
        "events": monthly_events(month_start),
        "month": month_start.strftime("%Y-%m"),
        "month_label": month_start.strftime("%B %Y"),
        "previous_month": add_months(month_start, -1).strftime("%Y-%m"),
        "next_month": add_months(month_start, 1).strftime("%Y-%m"),
        "today_month": date.today().strftime("%Y-%m"),
    }


def build_event(payload):
    return {
        "event_id": f"E{uuid4().hex[:8].upper()}",
        "title": payload.get("title", "").strip(),
        "date": payload.get("date", "").strip(),
        "time": payload.get("time", "").strip(),
        "location": payload.get("location", "").strip(),
        "related_person": payload.get("related_person", "").strip(),
        "notes": payload.get("notes", "").strip(),
        "status": "Scheduled",
    }


def create_event(payload):
    events = read_csv(EVENTS_FILE, EVENT_FIELDS)
    event = build_event(payload)
    if not event["title"] or not event["date"] or not event["time"]:
        return {"error": "Title, date, and time are required."}, 400

    events.append(event)
    write_csv(EVENTS_FILE, EVENT_FIELDS, events, STRUCTURED_DIR)
    return event, 201


def build_task(payload):
    return {
        "task_id": f"T{uuid4().hex[:8].upper()}",
        "title": payload.get("title", "").strip(),
        "date": payload.get("date", "").strip(),
        "time": payload.get("time", "").strip(),
        "priority": payload.get("priority", "Medium"),
        "status": "Open",
    }


def create_task(payload):
    todos = read_csv(TODOS_FILE, TODO_FIELDS)
    task = build_task(payload)
    if not task["title"] or not task["date"] or not task["time"]:
        return {"error": "Title, date, and time are required."}, 400

    todos.append(task)
    write_csv(TODOS_FILE, TODO_FIELDS, todos, STRUCTURED_DIR)
    return task, 201


def remove_event(event_id):
    existing = row_by_id(EVENTS_FILE, EVENT_FIELDS, "event_id", event_id)
    if not existing:
        return {"error": "Event not found."}, 404

    events = read_csv(EVENTS_FILE, EVENT_FIELDS)
    events = [event for event in events if event.get("event_id") != event_id]
    write_csv(EVENTS_FILE, EVENT_FIELDS, events, STRUCTURED_DIR)
    return {"deleted": event_id}, 200


def set_task_done(task_id):
    existing = row_by_id(TODOS_FILE, TODO_FIELDS, "task_id", task_id)
    if not existing:
        return {"error": "Task not found."}, 404

    todos = read_csv(TODOS_FILE, TODO_FIELDS)
    for todo in todos:
        if todo.get("task_id") == task_id:
            todo["status"] = "Closed"
            break
    write_csv(TODOS_FILE, TODO_FIELDS, todos, STRUCTURED_DIR)
    return {"task_id": task_id, "status": "Closed"}, 200
