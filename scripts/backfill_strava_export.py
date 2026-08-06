#!/usr/bin/env python3
"""Backfill data/activities.json from a Strava bulk export.

Get your export: Strava > Settings > My Account > Download or Delete Your
Account > Download Request. Unzip it and point this script at activities.csv:

    python3 scripts/backfill_strava_export.py ~/Downloads/export_12345/activities.csv

Merges by activity id (existing entries win), so it is safe to re-run.
"""
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "data" / "activities.json"

TYPE_MAP = {"Run": "run", "Ride": "ride", "Weight Training": "strength", "Workout": "strength"}


def parse_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main(csv_path):
    store = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {"activities": []}
    existing = {a["id"] for a in store["activities"]}
    added = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            aid = f"strava-{row.get('Activity ID', '').strip()}"
            if not row.get("Activity ID") or aid in existing:
                continue
            sport = TYPE_MAP.get(row.get("Activity Type", ""), "cross")
            dist_raw = parse_float(row.get("Distance"))  # km in most exports
            distance_km = round(dist_raw, 2) if dist_raw else 0
            moving = parse_float(row.get("Moving Time")) or 0  # seconds
            # Date like "Aug 4, 2026, 5:14:33 PM" -> ISO date
            from datetime import datetime
            date = ""
            for fmt in ("%b %d, %Y, %I:%M:%S %p", "%Y-%m-%d %H:%M:%S"):
                try:
                    date = datetime.strptime(row.get("Activity Date", ""), fmt).strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            item = {
                "id": aid,
                "date": date,
                "name": row.get("Activity Name", "Activity"),
                "type": sport,
                "distanceKm": distance_km,
                "movingTimeS": int(moving),
                "avgHr": int(h) if (h := parse_float(row.get("Average Heart Rate"))) else None,
                "ascentM": int(e) if (e := parse_float(row.get("Elevation Gain"))) else None,
                "source": "strava-export",
            }
            if sport == "run" and distance_km > 0 and moving > 0:
                item["paceSecPerKm"] = round(moving / distance_km)
            store["activities"].append(item)
            existing.add(aid)
            added += 1

    store["activities"].sort(key=lambda a: a.get("date", ""))
    DATA_FILE.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n")
    print(f"Added {added} activities from export.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
