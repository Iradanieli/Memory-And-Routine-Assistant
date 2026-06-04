from services.db_service import execute, fetch_all, fetch_one


def format_time(value):
    if not value:
        return ""
    return value.strftime("%H:%M")


def format_date(value):
    if not value:
        return ""
    return value.isoformat()


def event_from_row(row):
    return {
        "event_id": row.get("event_id", ""),
        "title": row.get("title", ""),
        "date": format_date(row.get("date")),
        "time": format_time(row.get("time")),
        "location": row.get("location", ""),
        "related_person": row.get("related_person", ""),
        "notes": row.get("notes", ""),
        "status": row.get("status", ""),
    }


def task_from_row(row):
    return {
        "task_id": row.get("task_id", ""),
        "title": row.get("title", ""),
        "date": format_date(row.get("date")),
        "time": format_time(row.get("time")),
        "priority": row.get("priority", ""),
        "status": row.get("status", ""),
    }


def list_events():
    rows = fetch_all(
        """
        SELECT event_id, title, date, time, location, related_person, notes, status
        FROM events
        """
    )
    return [event_from_row(row) for row in rows]


def list_tasks():
    rows = fetch_all(
        """
        SELECT task_id, title, date, time, priority, status
        FROM tasks
        """
    )
    return [task_from_row(row) for row in rows]


def find_event(event_id):
    row = fetch_one(
        """
        SELECT event_id, title, date, time, location, related_person, notes, status
        FROM events
        WHERE event_id = %s
        """,
        (event_id,),
    )
    return event_from_row(row) if row else None


def find_task(task_id):
    row = fetch_one(
        """
        SELECT task_id, title, date, time, priority, status
        FROM tasks
        WHERE task_id = %s
        """,
        (task_id,),
    )
    return task_from_row(row) if row else None


def insert_event(event):
    row = execute(
        """
        INSERT INTO events (
            event_id, title, date, time, location, related_person, notes, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING event_id, title, date, time, location, related_person, notes, status
        """,
        (
            event["event_id"],
            event["title"],
            event["date"],
            event["time"],
            event["location"],
            event["related_person"],
            event["notes"],
            event["status"],
        ),
    )
    return event_from_row(row)


def insert_task(task):
    row = execute(
        """
        INSERT INTO tasks (task_id, title, date, time, priority, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING task_id, title, date, time, priority, status
        """,
        (
            task["task_id"],
            task["title"],
            task["date"],
            task["time"],
            task["priority"],
            task["status"],
        ),
    )
    return task_from_row(row)


def delete_event(event_id):
    execute("DELETE FROM events WHERE event_id = %s", (event_id,))


def close_task(task_id):
    execute("UPDATE tasks SET status = 'Closed' WHERE task_id = %s", (task_id,))
