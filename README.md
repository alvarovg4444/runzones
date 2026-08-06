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

## 2. Connect Strava (10 min, one time)

Prerequisite: your Garmin is already linked to Strava (Strava app →
Settings → Applications → Connect Garmin), so every run lands on Strava.

1. Create an API app at <https://www.strava.com/settings/api>.
   - Website: your Pages URL. Authorization Callback Domain: `localhost`.
   - Note the **Client ID** and **Client Secret**.
2. In your browser, open (replace YOUR_CLIENT_ID):

   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost/exchange&approval_prompt=force&scope=activity:read_all
   ```

   Click **Authorize**. The localhost error page is expected — copy the
   `code=...` value from the address bar.
3. Run the helper (any machine with Python 3):

   ```
   python3 scripts/strava_auth.py CLIENT_ID CLIENT_SECRET CODE
   ```

4. In the repo: **Settings → Secrets and variables → Actions → New repository
   secret**, add the three values it prints:
   `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`.
5. **Actions** tab → "Strava sync" → **Run workflow** to test. It then runs
   every 6 hours by itself and commits new runs to `data/activities.json`.

## 3. Backfill history (optional)

The repo ships seeded with your recent Garmin activities. For a full history:
Strava → Settings → My Account → *Download or Delete Your Account* →
Download Request. Unzip, then:

```
python3 scripts/backfill_strava_export.py path/to/activities.csv
```

Commit and push the updated `data/activities.json`.

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
