#!/usr/bin/env python3
"""One-time helper: exchange a Strava authorization code for a refresh token.

Steps (also in README):
1. Create an API app at https://www.strava.com/settings/api
   (set "Authorization Callback Domain" to: localhost)
2. Open this URL in your browser (replace YOUR_CLIENT_ID):

   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost/exchange&approval_prompt=force&scope=activity:read_all

3. Click "Authorize". You land on a localhost error page - that's fine.
   Copy the `code=...` value from the address bar.
4. Run:  python3 scripts/strava_auth.py CLIENT_ID CLIENT_SECRET CODE
5. Save the printed refresh_token as the STRAVA_REFRESH_TOKEN repo secret.
"""
import json
import sys
import urllib.parse
import urllib.request

if len(sys.argv) != 4:
    print(__doc__)
    sys.exit(1)

client_id, client_secret, code = sys.argv[1:4]
body = urllib.parse.urlencode({
    "client_id": client_id,
    "client_secret": client_secret,
    "code": code,
    "grant_type": "authorization_code",
}).encode()
req = urllib.request.Request("https://www.strava.com/oauth/token", data=body, method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    tok = json.load(r)

print("\nSuccess! Add these as GitHub repo secrets:")
print(f"  STRAVA_CLIENT_ID:     {client_id}")
print(f"  STRAVA_CLIENT_SECRET: {client_secret}")
print(f"  STRAVA_REFRESH_TOKEN: {tok['refresh_token']}")
