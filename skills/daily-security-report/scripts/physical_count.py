#!/usr/bin/env python3
"""Tally physical-access records per device.

Usage: python physical_count.py <hits.json>

<hits.json> may be:
  - a full OpenSearch response  {"hits": {"hits": [...]}}
  - a list of responses         [{"hits": {"hits": [...]}}, ...]
  - a list of hits              [{"_source": {...}}, ...]

Each hit is expected to have _source.data.device_name and
_source.data.authentication_result. Unknown devices / result types are
auto-added (mirrors the original n8n logic). Known devices are always shown
even when they have zero records.

Prints JSON: {counts, markdown_table, ascii_table}.
"""
import json, sys

KNOWN = ["Cổng trước", "Lock F2", "Lock F3", "Lock F4"]


def load_hits(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("hits", {}).get("hits", [])
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "hits" in data[0]:
            out = []
            for r in data:
                out += r.get("hits", {}).get("hits", [])
            return out
        return data
    return []


def tally(hits):
    counts = {d: {"SUCCESS": 0, "FAILED": 0, "TOTAL": 0} for d in KNOWN}
    for h in hits:
        src = h.get("_source", h)
        d = src.get("data", {})
        dev, res = d.get("device_name"), d.get("authentication_result")
        if dev is None:
            continue
        counts.setdefault(dev, {"SUCCESS": 0, "FAILED": 0, "TOTAL": 0})
        if res is not None:
            counts[dev].setdefault(res, 0)
            counts[dev][res] += 1
        counts[dev]["TOTAL"] += 1
    return counts


def columns(counts):
    cols = ["SUCCESS", "FAILED"]
    for dev in counts.values():
        for k in dev:
            if k not in cols and k != "TOTAL":
                cols.append(k)
    return cols + ["TOTAL"]


def md_table(counts, cols):
    head = "| Device | " + " | ".join(cols) + " |"
    sep = "|" + "---|" * (len(cols) + 1)
    rows = [head, sep]
    for dev, c in counts.items():
        rows.append("| " + dev + " | " + " | ".join(str(c.get(k, 0)) for k in cols) + " |")
    return "\n".join(rows)


def ascii_table(counts, cols):
    headers = ["Device"] + cols
    rows = [[dev] + [str(c.get(k, 0)) for k in cols] for dev, c in counts.items()]
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) if rows else len(headers[i])
              for i in range(len(headers))]
    def line(vals):
        return "| " + " | ".join(v.ljust(widths[i]) for i, v in enumerate(vals)) + " |"
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    out = [sep, line(headers), sep] + [line(r) for r in rows] + [sep]
    return "\n".join(out)


def main():
    hits = load_hits(sys.argv[1])
    counts = tally(hits)
    cols = columns(counts)
    print(json.dumps({
        "counts": counts,
        "markdown_table": md_table(counts, cols),
        "ascii_table": ascii_table(counts, cols),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
