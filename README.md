# PromptLab Studios — Memes & Vedic Engine

A browser-only prompt engineering studio for AI-assisted content generation, deployed as a static site with one small scheduled job for live Panchang data. No app server, no database — just static files plus a daily GitHub Action.

It has two independent tools:

- **Memes** — pulls live Karnataka/India political headlines and turns them into meme image prompts + captions.
- **Vedic Engine** — uses live Hindu Panchang data (Tithi, Nakshatra, day, festival/observance) and turns it into devotional image and video prompts for Instagram, with two agents:
  - **Vedic Image Agent** — 3 prompts for a single event: two devotional "event details" info cards (event name/day/date, then significance/rituals) plus one cinematic devotional scene, all for a 1:1 Instagram post.
  - **Vedic Video Agent** — 3 prompts for a single event told as Hook → Value → CTA (9:16, 10 seconds each): the Hook and Value beats are animated info cards, and the CTA beat is a cinematic devotional scene.

Both tools are "research-then-generate": the app uses Google's Gemini API (with optional Google Search grounding) to research real, current facts before writing prompts, so output is grounded rather than invented.

## How it works

The app itself (`index.html` / `PromptLab_Instagram.html`) is a static HTML file — open it in a browser and it runs, no build step. Your Gemini API key and preferences are saved in your own browser's `localStorage` and never leave your device except in the direct calls you make to Gemini.

**This app must be served over `http://` or `https://`** — it will **not** work if you double-click the file and open it as `file://`. Browsers block requests to external APIs from local files for security reasons. The app detects this automatically and shows a warning + disables the Run buttons if opened as a local file. GitHub Pages (see below) solves this automatically, since it always serves over `https://`.

### Why there's a GitHub Action in this repo

The Vedic Engine wants live Hindu Panchang data (Bengaluru, Karnataka), sourced from the Prokerala Astrology API. Prokerala's API has no CORS support for direct browser calls — by design, it's meant to be called from a server, not from JavaScript running on someone's phone or laptop. That means the browser can never call Prokerala directly, regardless of what domain this app is hosted on.

To work around that without standing up a separate backend, this repo includes a small **GitHub Action** (`.github/workflows/update-panchang.yml`) that runs once a day, calls Prokerala server-side (where CORS doesn't apply), and commits the result to `panchang.json` at the repo root. The deployed app then just does a same-origin `fetch('./panchang.json')` — reading a file from its own site, which every browser allows freely. If that file is ever missing, stale, or empty (e.g. the Action hasn't been set up yet), the Vedic Engine falls back automatically to Gemini's own Google Search grounding to research the Panchang instead.

## Deploying to GitHub Pages

1. Push this repository to GitHub (or fork/upload it into your own repo) — make sure `panchang.json`, the `.github/workflows/` folder, and the `scripts/` folder all come along, not just the HTML files.
2. In the repo, go to **Settings → Pages**.
3. Under "Build and deployment", set **Source** to `Deploy from a branch`.
4. Choose your branch (e.g. `main`) and folder `/ (root)`, then **Save**.
5. GitHub will publish the site at `https://<your-username>.github.io/<repo-name>/` within a minute or two — it serves `index.html` automatically at that root URL.
6. Open that URL on any device (desktop or mobile) and use the app from there.

The repo also includes `PromptLab_Instagram.html` with identical content, in case you want a direct link to that specific filename instead of the root URL.

## Setting up live Panchang data (optional, but recommended)

The Vedic Engine works fine without this step — it just relies on Gemini's own research instead of the daily Prokerala feed. To enable the live feed:

1. Create a free account at [api.prokerala.com](https://api.prokerala.com/) and create a client to get a **Client ID** and **Client Secret**.
2. In your GitHub repo, go to **Settings → Secrets and variables → Actions**.
3. Add two repository secrets:
   - `PROKERALA_CLIENT_ID`
   - `PROKERALA_CLIENT_SECRET`
4. That's it — the **Update Panchang data** workflow runs automatically every day at 06:00 IST (00:30 UTC) and commits a fresh `panchang.json`. You can also trigger it manually any time from the repo's **Actions** tab → **Update Panchang data** → **Run workflow**, which is the fastest way to confirm it's working after adding the secrets.

These two secrets are only ever used inside the GitHub Action's server-side run — they're never included in the deployed site, never visible to site visitors, and never appear in `panchang.json` itself.

## First-time setup (in the app)

Open the **Settings** drawer (gear icon) and fill in:

- **Gemini API key** — required for both Memes and Vedic Engine. Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
- **Live search toggle** — keep this on so Gemini grounds its research in real, current information (news for Memes, festival/event significance for the Vedic Engine) rather than relying only on its training data.
- **Event lookahead** (Vedic Engine only) — choose whether the engine looks for the top event in the next 72 hours or widens to the next 7 days. `panchang.json` carries 7 days of data, so either setting is covered.

Settings are saved per-browser via `localStorage`, so you'll need to re-enter your Gemini key if you switch browsers or devices.

## Security note

Your Gemini API key is typed into the Settings drawer, saved only in your own browser's `localStorage`, and sent directly from your browser to Google's servers when you click a Run button — it's never sent to GitHub, never committed to this repository, and never passes through any server of ours.

That also means anyone with access to your browser (or who opens DevTools on a device where you've entered your key) could view it in `localStorage`. Don't enter a real API key on a shared or public computer.

The Prokerala credentials are handled completely differently and more safely: they live only as GitHub repository secrets, used exclusively inside the server-side Action run, and are never present in the deployed site's code or in `panchang.json`'s contents.

## Project structure

```
.
├── index.html                          # The app (served at the Pages root URL)
├── PromptLab_Instagram.html            # Identical copy, original filename
├── panchang.json                       # Daily Panchang data (auto-updated by the Action below)
├── scripts/
│   └── fetch_panchang.py               # Server-side script the Action runs to refresh panchang.json
├── .github/workflows/
│   └── update-panchang.yml             # Scheduled GitHub Action — runs fetch_panchang.py daily
└── README.md                           # This file
```

## Notes

- Free tiers apply for both Gemini and Prokerala — check each provider's current limits if you hit rate errors.
- The Memes tab and Vedic Engine tab are fully independent; the Prokerala setup above only affects the Vedic Engine.
- `panchang.json` is committed to the repo and updates automatically — you don't need to touch it directly. If you ever want to force a refresh outside the daily schedule, use the manual "Run workflow" button described above.
- No data is persisted server-side beyond `panchang.json` itself; clearing your browser's site data for this page will reset your Gemini key, preferences, and any generated results currently on screen.
