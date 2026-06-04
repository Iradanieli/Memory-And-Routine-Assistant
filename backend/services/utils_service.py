from datetime import date, datetime


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
