import time
import json
import os
from pathlib import Path
from contextlib import contextmanager

METRICS_DIR = os.environ.get("METRICS_DIR", "metrics")
_metrics_log = []


def _ensure_dir():
    Path(METRICS_DIR).mkdir(parents=True, exist_ok=True)


@contextmanager
def track(name):
    start = time.perf_counter()
    error = None
    try:
        yield
    except Exception as e:
        error = e
        raise
    finally:
        duration = (time.perf_counter() - start) * 1000
        entry = {
            "name": name,
            "duration_ms": round(duration, 2),
            "timestamp": time.time(),
            "error": str(error) if error else None
        }
        _metrics_log.append(entry)
        _persist(entry)


def _persist(entry):
    _ensure_dir()
    filepath = os.path.join(METRICS_DIR, "metrics.jsonl")
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_stats():
    if not _metrics_log:
        return {}
    by_name = {}
    for entry in _metrics_log:
        name = entry["name"]
        if name not in by_name:
            by_name[name] = {"count": 0, "total_ms": 0, "errors": 0, "durations": []}
        by_name[name]["count"] += 1
        by_name[name]["total_ms"] += entry["duration_ms"]
        by_name[name]["durations"].append(entry["duration_ms"])
        if entry["error"]:
            by_name[name]["errors"] += 1

    stats = {}
    for name, data in by_name.items():
        durations = sorted(data["durations"])
        stats[name] = {
            "count": data["count"],
            "avg_ms": round(data["total_ms"] / data["count"], 2),
            "p50_ms": round(durations[len(durations) // 2], 2),
            "p95_ms": round(durations[int(len(durations) * 0.95)], 2) if len(durations) > 1 else durations[0],
            "errors": data["errors"],
            "error_rate": round(data["errors"] / data["count"] * 100, 1)
        }
    return stats
