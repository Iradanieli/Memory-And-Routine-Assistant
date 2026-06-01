import csv
import os
import calendar
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from flask import Flask, flash, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
STRUCTURED_DIR = BASE_DIR / "structured"
EVENTS_FILE = STRUCTURED_DIR / "events.csv"
TODOS_FILE = STRUCTURED_DIR / "todos.csv"

AWS_REGION = os.getenv("AWS_REGION", "")
KNOWLEDGE_BASE_ID = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID", "")
BEDROCK_MODEL_ARN = os.getenv("BEDROCK_MODEL_ARN", "")

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

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-memory-assistant-secret")


def read_csv(path, fieldnames):
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [{field: row.get(field, "") for field in fieldnames} for row in reader]


def write_csv(path, fieldnames, rows):
    STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def parse_time(value):
    try:
        return datetime.strptime(value or "23:59", "%H:%M").time()
    except ValueError:
        return datetime.strptime("23:59", "%H:%M").time()


def sorted_by_date_time(rows):
    return sorted(
        rows,
        key=lambda row: (
            parse_date(row.get("date")) or date.max,
            parse_time(row.get("time")),
            row.get("title", ""),
        ),
    )


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
        "selected_day": selected_day,
        "is_fallback_day": is_fallback_day,
        "today": date.today(),
    }


def parse_month(value):
    try:
        return datetime.strptime(value, "%Y-%m").date().replace(day=1)
    except (TypeError, ValueError):
        return date.today().replace(day=1)


def add_months(month_start, offset):
    month_index = month_start.month - 1 + offset
    year = month_start.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


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


def ask_knowledge_base(question):
    if not KNOWLEDGE_BASE_ID or not BEDROCK_MODEL_ARN:
        return (
            "Bedrock configuration is missing. Set BEDROCK_KNOWLEDGE_BASE_ID "
            "and BEDROCK_MODEL_ARN in the environment.",
            [],
        )

    client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
    response = client.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": BEDROCK_MODEL_ARN,
            },
        },
    )

    answer = response.get("output", {}).get("text", "")
    citations = []
    for citation in response.get("citations", []):
        for reference in citation.get("retrievedReferences", []):
            location = reference.get("location", {})
            s3_location = location.get("s3Location", {})
            uri = s3_location.get("uri")
            if uri:
                citations.append(uri)

    return answer or "I could not find an answer in the memory documents.", citations


@app.get("/")
def home():
    data = dashboard_data()
    return render_template("index.html", **data, question="", answer=None, citations=[])


@app.post("/ask")
def ask():
    question = request.form.get("question", "").strip()
    data = dashboard_data()

    if not question:
        flash("Please type a question first.")
        return render_template("index.html", **data, question="", answer=None, citations=[])

    try:
        answer, citations = ask_knowledge_base(question)
    except NoCredentialsError:
        answer = (
            "AWS credentials were not found. On EC2, attach an IAM role with Bedrock "
            "permissions to the instance, then restart the container."
        )
        citations = []
    except (BotoCoreError, ClientError) as exc:
        answer = f"Bedrock could not answer right now: {exc}"
        citations = []

    return render_template(
        "index.html", **data, question=question, answer=answer, citations=citations
    )


@app.get("/caregiver")
def caregiver():
    return render_template("caregiver.html", today=date.today())


@app.get("/schedule")
def schedule():
    month_start = parse_month(request.args.get("month"))
    return render_template(
        "schedule.html",
        events=monthly_events(month_start),
        month_start=month_start,
        previous_month=add_months(month_start, -1),
        next_month=add_months(month_start, 1),
        today=date.today(),
    )


@app.post("/caregiver/event")
def add_event():
    events = read_csv(EVENTS_FILE, EVENT_FIELDS)
    events.append(
        {
            "event_id": f"E{uuid4().hex[:8].upper()}",
            "title": request.form.get("title", "").strip(),
            "date": request.form.get("date", "").strip(),
            "time": request.form.get("time", "").strip(),
            "location": request.form.get("location", "").strip(),
            "related_person": request.form.get("related_person", "").strip(),
            "notes": request.form.get("notes", "").strip(),
            "status": "Scheduled",
        }
    )
    write_csv(EVENTS_FILE, EVENT_FIELDS, events)
    flash("Event added to the routine.")
    return redirect(url_for("caregiver"))


@app.post("/caregiver/task")
def add_task():
    todos = read_csv(TODOS_FILE, TODO_FIELDS)
    todos.append(
        {
            "task_id": f"T{uuid4().hex[:8].upper()}",
            "title": request.form.get("title", "").strip(),
            "date": request.form.get("date", "").strip(),
            "time": request.form.get("time", "").strip(),
            "priority": request.form.get("priority", "Medium"),
            "status": "Open",
        }
    )
    write_csv(TODOS_FILE, TODO_FIELDS, todos)
    flash("Task added to the routine.")
    return redirect(url_for("caregiver"))


@app.post("/event/<event_id>/delete")
def delete_event(event_id):
    events = read_csv(EVENTS_FILE, EVENT_FIELDS)
    events = [event for event in events if event.get("event_id") != event_id]
    write_csv(EVENTS_FILE, EVENT_FIELDS, events)

    month = request.form.get("month")
    if month:
        return redirect(url_for("schedule", month=month))
    return redirect(url_for("schedule"))


@app.post("/task/<task_id>/done")
def mark_task_done(task_id):
    todos = read_csv(TODOS_FILE, TODO_FIELDS)
    for todo in todos:
        if todo.get("task_id") == task_id:
            todo["status"] = "Closed"
            break
    write_csv(TODOS_FILE, TODO_FIELDS, todos)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
