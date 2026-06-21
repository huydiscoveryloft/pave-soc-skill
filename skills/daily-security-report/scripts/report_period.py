#!/usr/bin/env python3
"""Compute the reporting window in UTC+7.

Usage: python report_period.py [YYYY-MM-DD]
- With a date argument: the window is that calendar day, 00:00-24:00 UTC+7.
- Without an argument: defaults to yesterday (UTC+7).

Prints JSON: date, start, end, report_id.
- start/end are ISO timestamps with +07:00 offset (use directly in OpenSearch range filters).
- The range is [start, end): the chosen day 00:00:00 up to (not including) the next day 00:00:00.
On a malformed date it prints {"error": ...} and exits non-zero.
"""
import json, sys, datetime as dt

TZ = dt.timezone(dt.timedelta(hours=7))

arg = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() else None
if arg:
    try:
        d = dt.datetime.strptime(arg, "%Y-%m-%d").date()
    except ValueError:
        print(json.dumps({"error": f"invalid date '{arg}', expected YYYY-MM-DD"}))
        sys.exit(1)
    start = dt.datetime(d.year, d.month, d.day, tzinfo=TZ)
else:
    today_mid = dt.datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    start = today_mid - dt.timedelta(days=1)

end = start + dt.timedelta(days=1)
print(json.dumps({
    "date": start.strftime("%Y-%m-%d"),
    "start": start.isoformat(),
    "end": end.isoformat(),
    "report_id": "DLSR-" + start.strftime("%Y%m%d"),
}, ensure_ascii=False))
