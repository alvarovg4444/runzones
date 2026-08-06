#!/usr/bin/env python3
"""Sync activities from intervals.icu into data/activities.json.

This is the FREE alternative to the Strava sync (Strava now requires a paid
subscription for API access). intervals.icu is free, syncs automatically from
Garmin Connect, and gives every user a personal API key.

One-time setup:
1. Create a free account at https://intervals.icu (sign in with Garmin makes
   linking trivial) and connect Garmin in Settings so activities flow in.
2. In intervals.icu Settings, scroll to "Developer" and copy your Athlete ID
   (looks like i123456) and API key.
3. Add two GitHub repo secrets:
     INTERVALS_ATHLETE_ID  (e.g. i123456)
     INTERVALS_API_KEY
"""
import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "data" / "activities.json"

TYPE_MAP = {
    "Run": "run", "TrailRun": "run", "VirtualRun": "run", "Treadmill": "run",
    "Ride": "ride", "VirtualRide": "ride", "GravelRide": "ride", "MountainBikeRide": "ride",
    "WeightTraining": "strength", "Workout": "strength", "Crossfit": "strength",
}


def http_get(url, params, api_key):
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{qs}")
    token = base64.b64encode(f"API_KEY:{api_key}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def map_activity(a):
    distance_km = round((a.get("distance") or 0) / 1000, 2)
    moving = a.get("moving_time") or a.get("elapsed_time") or 0
    sport = TYPE_MAP.get(a.get("type"), "cross")
    out = {
        "id": f"icu-{a['id']}",
        "date": (a.get("start_date_local") or "")[:10],
        "name": a.get("name") or "Activity",
        "type": sport,
        "distanceKm": distance_km,
        "movingTimeS": int(moving),
        "avgHr": round(a["average_heartrate"]) if a.get("average_heartrate") else None,
        "maxHr": round(a["max_heartrate"]) if a.get("max_heartrate") else None,
        "ascentM": round(a["total_elevation_gain"]) if a.get("total_elevation_gain") else None,
        "source": "intervals.icu",
    }
    if sport == "run" and distance_km > 0 and moving > 0:
        out["paceSecPerKm"] = round(moving / distance_km)
    if sport == "ride" and moving > 0:
        out["avgSpeedKph"] = round(distance_km / (moving / 3600), 1)
    return out


def main():
    athlete = os.environ["INTERVALS_ATHLETE_ID"]
    api_key = os.environ["INTERVALS_API_KEY"]

    store = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {"activities": []}
    existing = {a["id"] for a in store["activities"]}
    # also dedupe on (date, distance) so garmin-seeded entries aren't duplicated
    seen_sig = {(a.get("date"), round(a.get("distanceKm", 0), 1)) for a in store["activities"]}

    dates = [a["date"] for a in store["activities"] if a.get("date")]
    oldest = "2000-01-01"
    if dates:
        newest = max(dates)
        t = time.strptime(newest, "%Y-%m-%d")
        oldest = time.strftime("%Y-%m-%d", time.localtime(time.mktime(t) - 2 * 86400))

    batch = http_get(f"https://intervals.icu/api/v1/athlete/{athlete}/activities",
                     {"oldest": oldest, "newest": "2100-01-01"}, api_key)

    new_items = []
    for a in batch:
        m = map_activity(a)
        sig = (m["date"], round(m["distanceKm"], 1))
        if m["id"] in existing or sig in seen_sig:
            continue
        new_items.append(m)
        existing.add(m["id"])
        seen_sig.add(sig)

    if not new_items:
        print("No new activities.")
        return 0

    store["activities"].extend(new_items)
    store["activities"].sort(key=lambda a: a.get("date", ""))
    store["lastSync"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    store["source"] = "intervals-icu-sync"
    DATA_FILE.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n")
    print(f"Added {len(new_items)} new activities.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
