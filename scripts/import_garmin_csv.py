#!/usr/bin/env python3
"""Import a Garmin Connect "Export CSV" file into data/activities.json.

The 100% free, no-Strava, no-API path:
1. In Garmin Connect web, open Activities (https://connect.garmin.com/app/activities)
2. Click "Export CSV" (top right) - downloads Activities.csv
3. Upload that file to this repo as  data/garmin_export.csv
   (GitHub web: data folder -> Add file -> Upload files)
4. The garmin-csv-import GitHub Action converts and merges it automatically.

Or run locally:  python3 scripts/import_garmin_csv.py data/garmin_export.csv

Safe to re-run: existing entries (same date + distance) are never duplicated.
"""
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "data" / "activities.json"

RUN_TYPES = ("running", "trail running", "street running", "track running", "treadmill running", "indoor running", "virtual running")
RIDE_TYPES = ("cycling", "road cycling", "mountain biking", "gravel", "ebiking", "indoor cycling", "virtual cycling")
STRENGTH_TYPES = ("strength training", "gym & fitness equipment", "gym and fitness equipment")


def to_seconds(t):
    """'01:28:15' or '36:24' or '9:00' -> seconds"""
    if not t:
        return 0
    parts = [p for p in re.split(r"[:.]", t.strip()) if p != ""]
    try:
        nums = [int(float(p)) for p in parts]
    except ValueError:
        return 0
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    return nums[0] if nums else 0


def to_float(v):
    if v in (None, "", "--"):
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def parse_date(v):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M", "%b %d, %Y %I:%M %p"):
        try:
            return datetime.strptime(v.strip(), fmt).strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            continue
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(v))
    return m.group(1) if m else ""


def classify(activity_type):
    t = (activity_type or "").strip().lower()
    if any(k in t for k in RUN_TYPES):
        return "run"
    if any(k in t for k in RIDE_TYPES):
        return "ride"
    if any(k in t for k in STRENGTH_TYPES):
        return "strength"
    return "cross"


def main(csv_path):
    store = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {"activities": []}
    seen_sig = {(a.get("date"), round(a.get("distanceKm") or 0, 1)) for a in store["activities"]}
    added = 0

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f)):
            get = lambda *names: next((row[n] for n in names if n in row and row[n] not in (None, "")), "")
            date = parse_date(get("Date", "Activity Date", "Start Time"))
            if not date:
                continue
            sport = classify(get("Activity Type", "Type"))
            dist = to_float(get("Distance", "Distance (km)")) or 0
            moving = to_seconds(get("Moving Time", "Time", "Elapsed Time", "Duration"))
            sig = (date, round(dist, 1))
            if sig in seen_sig:
                continue
            item = {
                "id": f"garmin-csv-{date}-{i}",
                "date": date,
                "name": get("Title", "Activity Name", "Name") or "Activity",
                "type": sport,
                "distanceKm": round(dist, 2),
                "movingTimeS": moving,
                "avgHr": int(h) if (h := to_float(get("Avg HR", "Average Heart Rate"))) else None,
                "maxHr": int(h) if (h := to_float(get("Max HR", "Maximum Heart Rate"))) else None,
                "ascentM": int(e) if (e := to_float(get("Total Ascent", "Elevation Gain"))) else None,
                "source": "garmin-csv",
            }
            if sport == "run" and dist > 0 and moving > 0:
                item["paceSecPerKm"] = round(moving / dist)
            if sport == "ride" and moving > 0 and dist > 0:
                item["avgSpeedKph"] = round(dist / (moving / 3600), 1)
            store["activities"].append(item)
            seen_sig.add(sig)
            added += 1

    store["activities"].sort(key=lambda a: a.get("date", ""))
    DATA_FILE.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n")
    print(f"Imported {added} new activities from {csv_path}.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(REPO_ROOT / "data" / "garmin_export.csv"))
