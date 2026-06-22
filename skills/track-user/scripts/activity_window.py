#!/usr/bin/env python3
"""Compute the activity-tracking window in UTC+7.

The window feeds the CloudWatch Logs Insights `start_time` / `end_time` (and is echoed in the
timeline log header). All timestamps are ISO-8601 with a `+07:00` offset and can be passed
straight to `execute_log_insights_query`.

Usage:
  python activity_window.py                       -> rolling last 7 days (default)
  python activity_window.py 14                     -> rolling last 14 days
  python activity_window.py 30d                     -> rolling last 30 days ('d' suffix allowed)
  python activity_window.py 2026-06-01 2026-06-22  -> explicit calendar range, inclusive of
                                                       both dates (start day 00:00 .. end day 24:00)

Rolling windows end at "now" (UTC+7); explicit ranges are whole calendar days.
Prints JSON: start, end, days, label, window_id.
On bad input prints {"error": ...} and exits non-zero.
"""
import json, sys, datetime as dt

TZ = dt.timezone(dt.timedelta(hours=7))
args = [a.strip() for a in sys.argv[1:] if a.strip()]


def emit(start, end, label):
    days = round((end - start).total_seconds() / 86400, 2)
    print(json.dumps({
        "start": start.isoformat(),
        "end": end.isoformat(),
        "days": days,
        "label": label,
        "window_id": "UA-" + start.strftime("%Y%m%d") + "-" + end.strftime("%Y%m%d"),
    }, ensure_ascii=False))


if len(args) >= 2:
    # explicit calendar range: start-date end-date (inclusive of both days)
    try:
        d0 = dt.datetime.strptime(args[0], "%Y-%m-%d").date()
        d1 = dt.datetime.strptime(args[1], "%Y-%m-%d").date()
    except ValueError:
        print(json.dumps({"error": f"invalid date in '{args[0]} {args[1]}', expected YYYY-MM-DD YYYY-MM-DD"}))
        sys.exit(1)
    if d1 < d0:
        print(json.dumps({"error": f"end date {args[1]} is before start date {args[0]}"}))
        sys.exit(1)
    start = dt.datetime(d0.year, d0.month, d0.day, tzinfo=TZ)
    end = dt.datetime(d1.year, d1.month, d1.day, tzinfo=TZ) + dt.timedelta(days=1)
    emit(start, end, f"{args[0]} to {args[1]} (UTC+7)")
elif len(args) == 1:
    # rolling last N days
    raw = args[0][:-1] if args[0].lower().endswith("d") else args[0]
    try:
        n = int(raw)
    except ValueError:
        print(json.dumps({"error": f"invalid window '{args[0]}', expected an integer day count (e.g. 7 or 7d) or two YYYY-MM-DD dates"}))
        sys.exit(1)
    if n <= 0:
        print(json.dumps({"error": f"window must be a positive number of days, got {n}"}))
        sys.exit(1)
    end = dt.datetime.now(TZ)
    start = end - dt.timedelta(days=n)
    emit(start, end, f"last {n} day{'s' if n != 1 else ''} (UTC+7)")
else:
    # default: rolling last 7 days
    end = dt.datetime.now(TZ)
    start = end - dt.timedelta(days=7)
    emit(start, end, "last 7 days (UTC+7)")
