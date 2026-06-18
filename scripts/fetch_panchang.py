#!/usr/bin/env python3
"""
Fetches 7 days of Hindu Panchang data (today + 6 future days) from the
Prokerala Astrology API for Bengaluru, Karnataka, and writes the result to
panchang.json at the repo root.

This script is meant to run server-side (GitHub Actions), NOT in a browser —
Prokerala's API has no CORS support for direct browser calls, which is the
whole reason this script exists: it does the Prokerala call once a day from
a trusted server context, and the deployed static site just reads the
resulting same-origin JSON file instead of calling Prokerala itself.

Required environment variables:
  PROKERALA_CLIENT_ID
  PROKERALA_CLIENT_SECRET

Output: panchang.json, written to the current working directory (the
workflow is expected to run this from the repo root).
"""
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta, timezone

# Bengaluru, Karnataka — fixed coordinates per the Vedic Engine's regional focus.
LAT = "12.9716"
LNG = "77.5946"
DAYS_AHEAD = 7  # today + 6 future days
IST = timezone(timedelta(hours=5, minutes=30))


def get_token(client_id, client_secret):
    url = "https://api.prokerala.com/token"
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded"
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read().decode())
    token = body.get("access_token")
    if not token:
        raise RuntimeError(f"Token response missing access_token: {body}")
    return token


def fetch_panchang_for_day(token, day_offset):
    dt = datetime.now(IST) + timedelta(days=day_offset)
    dt_iso = dt.strftime("%Y-%m-%dT%H:%M:%S+05:30")
    params = urllib.parse.urlencode({
        "ayanamsa": "1",
        "coordinates": f"{LAT},{LNG}",
        "datetime": dt_iso,
        "la": "en",
    })
    url = f"https://api.prokerala.com/v2/astrology/panchang?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read().decode())

    d = body.get("data") or {}
    tithi = d.get("tithi") or {}
    nakshatra = d.get("nakshatra") or {}
    weekday = d.get("weekday") or {}
    lunar_month = d.get("lunar_month") or {}

    # vrat/festival data is not a guaranteed field on this endpoint across all
    # Prokerala plans/response versions — include it only if present, and
    # never fail the whole run if it's missing. Gemini's own research already
    # fills in the actual event/festival name on top of this seed data.
    vrat_names = []
    for v in (d.get("vrat") or []):
        name = v.get("name") if isinstance(v, dict) else None
        if name:
            vrat_names.append(name)

    return {
        "date": dt.strftime("%Y-%m-%d"),
        "day": weekday.get("name", ""),
        "tithi": tithi.get("name", ""),
        "nakshatra": nakshatra.get("name", ""),
        "lunar_month": lunar_month.get("name", ""),
        "vrat": ", ".join(vrat_names),
    }


def main():
    client_id = os.environ.get("PROKERALA_CLIENT_ID", "").strip()
    client_secret = os.environ.get("PROKERALA_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        print("PROKERALA_CLIENT_ID / PROKERALA_CLIENT_SECRET not set — skipping fetch.", file=sys.stderr)
        sys.exit(1)

    try:
        token = get_token(client_id, client_secret)
    except urllib.error.HTTPError as e:
        print(f"Token request failed: HTTP {e.code} — {e.read().decode(errors='replace')[:300]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Token request failed: {e}", file=sys.stderr)
        sys.exit(1)

    days = []
    for i in range(DAYS_AHEAD):
        try:
            days.append(fetch_panchang_for_day(token, i))
        except urllib.error.HTTPError as e:
            print(f"Panchang fetch failed for day offset {i}: HTTP {e.code} — {e.read().decode(errors='replace')[:300]}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Panchang fetch failed for day offset {i}: {e}", file=sys.stderr)
            sys.exit(1)

    output = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": "Bengaluru, Karnataka, India",
        "coordinates": f"{LAT},{LNG}",
        "days": days,
    }

    with open("panchang.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote panchang.json with {len(days)} day(s).")


if __name__ == "__main__":
    main()
