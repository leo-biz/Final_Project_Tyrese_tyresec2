# ScrapHounds Handoff

## Project

- Local repo: `/Users/sir/Workspaces/TyPro`
- Live URL: <https://scraphounds.onrender.com>
- Render service name: `scraphounds`
- Database: Supabase Postgres
- Render-connected git remote: `fork`
- Fork remote URL: <https://github.com/leo-biz/Final_Project_Tyrese_tyresec2.git>
- Original remote URL: <https://github.com/tairesu/Final_Project_Tyrese_tyresec2.git>
- Latest pushed commit at handoff: `53cbe59 Add Joliet browser scraper fallback`

## Current Status

The app is live on Render and reads from Supabase. Search and quick-search result pages are working.

Current Supabase inventory counts after the latest refresh:

- Total vehicles: `5575`
- Joliet U-Pull It: `1442`
- Pick n Pull - Summit: `1131`
- Pick Your Part - Blue Island: `1794`
- Pick Your Part - Chicago South: `1208`

## Major Fixes Completed

- Added Render deployment files and production settings support.
- Connected the app to Supabase Postgres through `DATABASE_URL`.
- Fixed static asset problems that caused missing files in production.
- Fixed quick-search/result page `500` errors.
- Fixed the LKQ/Pick Your Part parser for the current site markup.
- Hardened `refresh_inventories` so existing rows update mutable fields such as row, space, color, VIN, and available date.
- Hardened `seed_junkyards` so yards are updated by stable address instead of duplicated when metadata changes.
- Added Joliet browser fallback scraping with Playwright because normal Python HTTP scraping is blocked.

## Joliet Scraper Notes

Joliet does not appear to expose a separate inventory API. The inventory rows are present in the HTML document at:

```text
https://www.jolietupullit.com/inventory/?make=&model=
```

Normal Python `requests` gets `403 Forbidden`, even with a browser-looking user agent. Playwright/Chromium receives `200 OK` and can read the `#cars-table` inventory table.

The coded fix in `yardsearcher/utils/jup.py` now:

1. Tries the existing lightweight HTTP fetch.
2. Falls back to Playwright/Chromium if the table is missing.
3. Parses the same `#cars-table` rows through the existing scraper structure.

Render build now installs Playwright Chromium in `build.sh`:

```bash
python -m playwright install chromium
```

If Render free tier has browser dependency problems, keep the app live and move the inventory refresh to GitHub Actions or another worker that can run Playwright.

## Useful Commands

Run Django checks:

```bash
SECRET_KEY="local-command-only-secret-value-not-used-for-deploy" \
DJANGO_SETTINGS_MODULE=scraphounds.settings.production \
./venv/bin/python manage.py check
```

Seed known junkyards:

```bash
DATABASE_URL="$(pbpaste)" \
SECRET_KEY="local-command-only-secret-value-not-used-for-deploy" \
DJANGO_SETTINGS_MODULE=scraphounds.settings.production \
./venv/bin/python manage.py seed_junkyards
```

Refresh all inventories:

```bash
DATABASE_URL="$(pbpaste)" \
SECRET_KEY="local-command-only-secret-value-not-used-for-deploy" \
DJANGO_SETTINGS_MODULE=scraphounds.settings.production \
./venv/bin/python manage.py refresh_inventories
```

Check production home page:

```bash
curl -sS -I -L --max-time 45 https://scraphounds.onrender.com/
```

Check a production search page:

```bash
curl -sS -L --max-time 45 "https://scraphounds.onrender.com/results/?q=2016-2026%20ford"
```

## Recommended Next Step

Add an admin-only inventory refresh workflow.

Do not run the full refresh inside a normal public web request. The scraper can take several minutes, and browser-backed Joliet scraping makes that even more likely to time out on Render free.

Preferred implementation:

1. Admin clicks a protected "Refresh Inventory" action.
2. The action triggers a background workflow.
3. The workflow runs `seed_junkyards` and `refresh_inventories`.
4. The site stores and displays per-yard status, counts, last run time, and errors.

Best hosting option for that workflow is likely GitHub Actions:

- It supports a manual "Run workflow" button.
- It can run on a schedule.
- It can install Playwright/Chromium reliably.
- It can write directly to Supabase using a GitHub secret for `DATABASE_URL`.

## Known Caveats

- `DATABASE_URL` is sensitive and should remain in Render/Supabase/GitHub secrets, not committed to the repo.
- The local commands above assume the production database URL is available in the clipboard.
- Render free web shell is not available for this service.
- Existing untracked/generated local folders such as `venv/`, `staticfiles/`, and `junkyardFinder/static/` should not be committed unless intentionally needed.
