#!/usr/bin/env python3
"""Sync new Strava activities into data/activities.json.

Runs in GitHub Actions on a schedule. Requires three repo secrets:
  STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN

The refresh token must have `activity:read_all` scope (see README for the
one-time authorization step).
"""
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


def http_post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def http_get(url, token, params):
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{qs}")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def get_access_token():
    return http_post("https://www.strava.com/oauth/token", {
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })["access_token"]


def map_activity(a):
    distance_km = round((a.get("distance") or 0) / 1000, 2)
    moving = a.get("moving_time") or 0
    sport = TYPE_MAP.get(a.get("sport_type") or a.get("type"), "cross")
    out = {
        "id": f"strava-{a['id']}",
        "date": (a.get("start_date_local") or a.get("start_date", ""))[:10],
        "name": a.get("name", "Activity"),
        "type": sport,
        "distanceKm": distance_km,
        "movingTimeS": moving,
        "avgHr": round(a["average_heartrate"]) if a.get("average_heartrate") else None,
        "maxHr": round(a["max_heartrate"]) if a.get("max_heartrate") else None,
        "ascentM": round(a["total_elevation_gain"]) if a.get("total_elevation_gain") else None,
        "cadence": round(a["average_cadence"] * 2) if a.get("average_cadence") and sport == "run" else None,
        "source": "strava",
    }
    if sport == "run" and distance_km > 0 and moving > 0:
        out["paceSecPerKm"] = round(moving / distance_km)
    if sport == "ride" and moving > 0:
        out["avgSpeedKph"] = round(distance_km / (moving / 3600), 1)
    return out


def main():
    store = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {"activities": []}
    existing = {a["id"] for a in store["activities"]}

    # Fetch everything after the newest stored activity (minus 2 days for safety).
    dates = [a["date"] for a in store["activities"] if a.get("date")]
    after = 0
    if dates:
        newest = max(dates)
        after = int(time.mktime(time.strptime(newest, "%Y-%m-%d"))) - 2 * 86400

    token = get_access_token()
    new_items, page = [], 1
    while True:
        batch = http_get("https://www.strava.com/api/v3/athlete/activities", token,
                         {"after": after, "per_page": 200, "page": page})
        if not batch:
            break
        for a in batch:
            m = map_activity(a)
            if m["id"] not in existing:
                new_items.append(m)
        page += 1
        if page > 20:  # safety valve
            break

    if not new_items:
        print("No new activities.")
        return 0

    store["activities"].extend(new_items)
    store["activities"].sort(key=lambda a: a.get("date", ""))
    store["lastSync"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    store["source"] = "strava-sync"
    DATA_FILE.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n")
    print(f"Added {len(new_items)} new activities.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
