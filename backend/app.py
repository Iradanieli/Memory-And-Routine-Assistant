import csv
import os
import calendar
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from flask import Flask, jsonify, request


BASE_DIR = Path(__file__).resolve().parent
STRUCTURED_DIR = BASE_DIR / "structured"
EVENTS_FILE = STRUCTURED_DIR / "events.csv"
TODOS_FILE = STRUCTURED_DIR / "todos.csv"

AWS_REGION = os.getenv("AWS_REGION", "")
KNOWLEDGE_BASE_ID = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID", "")
BEDROCK_MODEL_ARN = os.getenv("BEDROCK_MODEL_ARN", "")
RAG_PROMPT_TEMPLATE = """
You are a calm and helpful memory assistant for a person with memory difficulties.

Use only the information in the search results to answer the user's question.

Rules:
1. Answer using only the provided search results.
2. If the search results do not contain enough information, say:
   "I do not have enough information in the memory documents."
3. Keep the answer simple, clear, and reassuring.
4. Do not invent facts.
5. If the question is about safety, confusion, appointments, family, places, or routine, answer gently and directly.

Search results:
$search_results$

Question:
$query$

Answer:
"""

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
        "selected_day": selected_day.isoformat(),
        "is_fallback_day": is_fallback_day,
        "today": date.today().isoformat(),
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


def row_by_id(path, fieldnames, key, value):
    for row in read_csv(path, fieldnames):
        if row.get(key) == value:
            return row
    return None


def ask_knowledge_base(question): 
    if not KNOWLEDGE_BASE_ID or not BEDROCK_MODEL_ARN:
        return (
            "Bedrock configuration is missing. Set BEDROCK_KNOWLEDGE_BASE_ID "
            "and BEDROCK_MODEL_ARN in the environment.",
            [],
        )

    client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
    response = client.retrieve_and_generate(  ### calls Bedrock Knowledge Base
        input={"text": question},   ### the user's question
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",   
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID, ### which knowledgebase to search
                "modelArn": BEDROCK_MODEL_ARN,
                "generationConfiguration": {
                    "promptTemplate": {
                        "textPromptTemplate": RAG_PROMPT_TEMPLATE,
                    },
                },
            },
        },
    )
    ### extracts generated answer and the source document citations
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


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/dashboard")
def api_dashboard():
    return jsonify(dashboard_data())


@app.post("/api/ask")
def api_ask():
    payload = request.get_json(silent=True) or {}
    question = payload.get("question", "").strip()

    if not question:
        return jsonify({"error": "Please type a question first."}), 400

    try:
        answer, citations = ask_knowledge_base(question) ### answer = answer of the LLM to the user question
    except NoCredentialsError:
        answer = (
            "AWS credentials were not found. On EC2, attach an IAM role with Bedrock "
            "permissions to the instance, then restart the container."
        )
        citations = []
    except (BotoCoreError, ClientError) as exc:
        answer = f"Bedrock could not answer right now: {exc}"
        citations = []

    return jsonify({"answer": answer, "citations": citations})


@app.get("/api/schedule")
def api_schedule():
    month_start = parse_month(request.args.get("month"))
    return jsonify(
        {
            "events": monthly_events(month_start),
            "month": month_start.strftime("%Y-%m"),
            "month_label": month_start.strftime("%B %Y"),
            "previous_month": add_months(month_start, -1).strftime("%Y-%m"),
            "next_month": add_months(month_start, 1).strftime("%Y-%m"),
            "today_month": date.today().strftime("%Y-%m"),
        }
    )


@app.post("/api/events")
def api_add_event():
    payload = request.get_json(silent=True) or {}
    events = read_csv(EVENTS_FILE, EVENT_FIELDS)
    event = {
        "event_id": f"E{uuid4().hex[:8].upper()}",
        "title": payload.get("title", "").strip(),
        "date": payload.get("date", "").strip(),
        "time": payload.get("time", "").strip(),
        "location": payload.get("location", "").strip(),
        "related_person": payload.get("related_person", "").strip(),
        "notes": payload.get("notes", "").strip(),
        "status": "Scheduled",
    }
    if not event["title"] or not event["date"] or not event["time"]:
        return jsonify({"error": "Title, date, and time are required."}), 400

    events.append(event)
    write_csv(EVENTS_FILE, EVENT_FIELDS, events)
    return jsonify(event), 201


@app.post("/api/tasks")
def api_add_task():
    payload = request.get_json(silent=True) or {}
    todos = read_csv(TODOS_FILE, TODO_FIELDS)
    task = {
        "task_id": f"T{uuid4().hex[:8].upper()}",
        "title": payload.get("title", "").strip(),
        "date": payload.get("date", "").strip(),
        "time": payload.get("time", "").strip(),
        "priority": payload.get("priority", "Medium"),
        "status": "Open",
    }
    if not task["title"] or not task["date"] or not task["time"]:
        return jsonify({"error": "Title, date, and time are required."}), 400

    todos.append(task)
    write_csv(TODOS_FILE, TODO_FIELDS, todos)
    return jsonify(task), 201


@app.delete("/api/events/<event_id>")
def api_delete_event(event_id):
    existing = row_by_id(EVENTS_FILE, EVENT_FIELDS, "event_id", event_id)
    if not existing:
        return jsonify({"error": "Event not found."}), 404

    events = read_csv(EVENTS_FILE, EVENT_FIELDS)
    events = [event for event in events if event.get("event_id") != event_id]
    write_csv(EVENTS_FILE, EVENT_FIELDS, events)
    return jsonify({"deleted": event_id})


@app.post("/api/tasks/<task_id>/done")
def api_mark_task_done(task_id):
    existing = row_by_id(TODOS_FILE, TODO_FIELDS, "task_id", task_id)
    if not existing:
        return jsonify({"error": "Task not found."}), 404

    todos = read_csv(TODOS_FILE, TODO_FIELDS)
    for todo in todos:
        if todo.get("task_id") == task_id:
            todo["status"] = "Closed"
            break
    write_csv(TODOS_FILE, TODO_FIELDS, todos)
    return jsonify({"task_id": task_id, "status": "Closed"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
