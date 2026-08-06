# RunZones (personal)

A personal, RunZones-style marathon training app. Static app on GitHub Pages;
your training data lives as JSON **in this repo** (every sync is a commit, so
your training history is versioned forever). A GitHub Action pulls new runs
from Strava automatically — Garmin watch → Garmin Connect → Strava → here.

**Features:** dashboard (readiness, weekly volume, predicted marathon time),
8-system fitness profile, per-run session execution scoring, adaptive week-by-week
plan to race day, race recipe with goal splits, pace + HR zones.

Currently configured for: **Marathon on 2027-04-18, goal sub-4:00** (edit
`data/settings.json` to change anything — zones, race date, plan volumes).

## 1. Put it on GitHub (5 min)

1. Create a new repo (public is simplest for Pages), e.g. `runzones`.
2. Push these files, or upload them via the GitHub web UI.
3. Repo **Settings → Pages** → Source: "Deploy from a branch" → `main`, `/ (root)`.
4. Your app is live at `https://<username>.github.io/runzones/`.

> No GitHub? The app also works by just double-clicking `index.html` —
> it uses the embedded copy of your data. But then nothing syncs.

## 2. Getting your runs in — three options (everything on GitHub is free)

GitHub costs nothing here: public repos get **free unlimited Actions minutes**
and **free Pages hosting**. The only paid thing in the original design was
Strava's API (since June 2026 it requires an active Strava subscription), so
options A and B avoid Strava entirely.

### Option A — Garmin CSV, weekly, zero accounts (recommended to start)

1. Open <https://connect.garmin.com/app/activities> → **Export CSV** (top right).
2. In this repo: open the `data/` folder → **Add file → Upload files** →
   drop the CSV, rename it to `garmin_export.csv` if needed → Commit.
3. The **Garmin CSV import** Action converts it, merges only new activities
   into `data/activities.json`, and deletes the CSV. ~1 min of clicking per week.

### Option B — intervals.icu, automatic, free

[intervals.icu](https://intervals.icu) is free, syncs automatically from
Garmin Connect, and gives every user a personal API key.

1. Create an account at intervals.icu and connect Garmin in its settings.
2. In intervals.icu **Settings → Developer**: copy your **Athlete ID** (i123456)
   and **API key**.
3. Repo **Settings → Secrets and variables → Actions**: add
   `INTERVALS_ATHLETE_ID` and `INTERVALS_API_KEY`.
4. Done — the **Intervals.icu sync** Action pulls new activities every 6 hours.

### Option C — Strava (only if you already pay for Strava)

Requires an active Strava subscription for API access. See
`scripts/strava_auth.py` for the one-time token setup; secrets:
`STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`.

## 3. Backfill history (optional)

Option A also works for history: Garmin's CSV export includes everything shown
in the activities list. For a Strava bulk export instead, use
`python3 scripts/backfill_strava_export.py path/to/activities.csv`.

## How it works

```
Garmin watch ─▶ Garmin Connect ─▶ Strava ─▶ GitHub Action (every 6 h)
                                                 │  commits JSON
                                                 ▼
                        data/activities.json  ◀─ your repo = your database
                                                 │  fetched at load
                                                 ▼
                              index.html on GitHub Pages = the app
```

- `index.html` — the whole app (no build step, no dependencies).
- `data/settings.json` — you, your zones, your goal, plan parameters.
- `data/activities.json` — every activity; the sync only appends.
- `scripts/strava_sync.py` — used by the Action; also runs locally.
- `scripts/backfill_strava_export.py` — one-time history import.
- `scripts/strava_auth.py` — one-time token helper.

All scores/plans are computed client-side with transparent formulas in
`index.html` — tune them as your marathon knowledge grows. That's the point.
