# CLAUDE.md

## What this is

A personal movie journal: a Flask web app + Postgres database that tracks the movies the
owner (and a handful of other users) has watched, with grades, a watchlist, statistics and
recommendations. Data comes from **TMDb** (live API) and from the **open IMDb datasets**
(bulk-loaded via a weekly ETL).

It runs as a PWA on a Raspberry Pi behind a home Livebox, reachable at
`https://journal.rberly.ovh`. The app is designed mobile-first (iPhone, added to the home
screen) — every page must look right at phone width.

`README.md` has screenshots and the longer origin story; it is somewhat out of date with
regard to newer pages (Library, Recos, People, Retrospective, Settings).

## Layout

```
app/            Flask app (the web-app)
  __init__.py   app/db/login/cache-buster initialisation — imports routes & models at the end
  routes.py     every route, ~800 lines, single module (no blueprints)
  models.py     SQLAlchemy models, all in the `journal` schema (plus imdb.ratings)
  dbutils.py    upsert helpers + raw-SQL execution (sync and fire-and-forget async)
  converters.py TMDb JSON <-> DB row <-> template payload conversions
  titles.py     TitleCollector: TMDb fetch + IMDb rating lookup
  graphutils.py plotly bar charts written to PNG (statistics / retrospective)
  forms.py      only the signup form is a WTForm; every other form is raw HTML
  queries/      raw .sql files loaded at request time
  templates/    Jinja2, one file per page + templates/base/{head,menu,alert}.html
  static/       css/, js/, images/, generated/ (runtime PNGs, gitignored)
config/         *.yaml configuration + app.py (Flask Config object)
lib/            non-web code: tmdb, overseerr, etl, push (Pushover), tools
ddl/            hand-maintained CREATE TABLE / CREATE MATERIALIZED VIEW statements
tmp/            scratch: ETL downloads, backups, old experiments — gitignored
```

## Running things

```bash
python run_journal.py                 # dev server on localhost:8088, debug on
python run_imdb_etl.py -t titles      # or -a for every type in config/etl.yaml
python run_imdb_etl.py -a --use-cache # reuse already-downloaded tmp/*.tsv.gz.cache
python backup.py                      # dump journal tables to tmp/<YYYY-MM-DD>/*.csv
python update_watchlist_providers.py  # refresh streaming providers of watchlist items
python update_all_title_metadata.py   # re-pull TMDb metadata for every stored title
```

All scripts are run from the repo root — config paths (`config/…`, `tmp/…`) are relative to
the CWD, not to the script.

Python 3.12 (`.python-version` → pyenv virtualenv `journal3.12.7`). Dependencies are in
`requirements.txt`, unpinned. There is no test suite; `tmp/test_*.py` are throwaway
experiments, not tests.

In production the app is served by gunicorn under supervisor on the Pi. `deploy.sh` (run on
the Pi) stops supervisor, pulls `master`, restarts it. The ETL, the backup and the provider
refresh run from cron.

## Configuration and secrets

`config/credentials.yaml` and `config/app.py` are **gitignored** and hold real secrets (DB
password, TMDb API key, Pushover, Plex, Overseerr). Never print their contents, commit them,
or add secrets to tracked files. `config/app.py` builds the Flask `Config`; the DB URI comes
from `lib.tools.get_db_uri(**credentials['db'])`.

The other yaml files are tracked: `etl.yaml` (IMDb dataset URLs, column mappings, filters),
`providers.yaml` (supported streaming providers + country), `backup.yaml`, `search.yaml`
(legacy IMDb-scraping config, only used by the unused `bs4_helper`).

## Database

Two Postgres schemas:

- `imdb.*` — bulk-loaded copy of the open IMDb datasets. **Truncated and fully reloaded** by
  the ETL, so never store anything of your own there. Only `imdb.ratings` is read by the app.
- `journal.*` — the real data: `users`, `titles`, `persons`, `credits`, `records`,
  `watchlist`, `blacklist`, plus materialized views `top_persons`, `top_genres`, `tops`.

There are no migrations. Schema changes mean editing `ddl/` **and** `app/models.py` **and**
applying the DDL by hand on the Pi.

Every model sets `__table_args__ = {"schema": "journal"}` and carries
`insert_datetime_utc` / `update_datetime_utc`. Writes to `titles`/`persons`/`credits` go
through `app.dbutils.upsert` / `upsert_bulk` / `upsert_title_metadata`, which exclude
`insert_datetime_utc` from the update set and bump `update_datetime_utc`.

The engine runs in `AUTOCOMMIT` isolation with a small pool (see `config/app.py`); long
loops that write should `db.session.commit()` each iteration to avoid idle-in-transaction
timeouts (see `update_watchlist_providers.py`).

Statistics come from the materialized views, so any write that changes records must call
`refresh_materialized_views()` in `routes.py` — that fires
`app/queries/refresh_materialized_views.sql` asynchronously on a separate connection.

`app.dbutils.execute_text` / `async_execute_text` escape `:` before handing the SQL to
SQLAlchemy `text()`, because the raw queries contain colons that are not bind parameters.
Raw `.sql` files under `app/queries/` are read at request time and `.format()`-ed with the
user id — keep interpolation limited to values that come from the session, never from
request arguments.

## Route conventions

`routes.py` is deliberately one flat module. Each page route follows the same shape:

1. handle the POST actions by checking for a key in `request.form`
   (`add_to_watchlist`, `remove_from_watchlist`, `move_to_top_of_watchlist`, `blacklist`,
   `remove`, `gradeRange`, …), `flash()` a message, then fall through to the GET rendering;
2. build a **`payload`** (the data) and a **`metadata`** dict (UI state: `scroll_to`,
   `show_more_button`, `sort_by`, filters, current user preferences);
3. `render_template('<page>.html', payload=payload, metadata=metadata)`.

Both `payload` and `metadata` are always passed, even when empty (`metadata={}`).

Other conventions worth keeping:

- Pagination is "show more": the page passes a bigger `nb_results` query arg and re-renders;
  `scroll_to` (set by `static/js/scroll.js`) restores the scroll position.
- All pages are `@login_required`; unauthorised access redirects to `/login`. Sessions are
  remembered for 90 days.
- A global `@app.errorhandler(Exception)` flashes "Wops, something went wrong", logs the
  traceback and redirects to the referrer. `/error` raises on purpose to test it.
- Per-user display preferences live on `User`: `language` (titles are shown in the original
  language when it matches the user's), `grade_as_int` (slider precision),
  `providers` (which streaming services to show).
- Titles reaching templates go through `TitleConverter.table_to_front` /
  `json_to_front` (via `Title.export()` / `enrich_results`), which is what produces
  `poster_url`, `duration`, `year` and the language-aware `title`.

## Frontend conventions

- No build step, no framework: plain Jinja2, one hand-written CSS file per page in
  `static/css/`, small vanilla JS helpers in `static/js/`.
- Every page starts with `{% include 'base/head.html' %}` (viewport, theme colour, PWA
  manifest, apple-touch icons, the per-device splash screens, `general.css`, `alert.css`),
  then includes `base/menu.html` and `base/alert.html`. New pages must be added to the
  sidenav in `base/menu.html`.
- `Flask-CacheBuster` hashes `.js`/`.css`/`.json` URLs, so static assets can be edited
  freely without cache headaches — but only when referenced through `url_for('static', …)`.
- The theme colour is `#6caee0`; it appears in `manifest.json`, `base/head.html` and
  `graphutils.py`. Change all three together.
- `static/js/shunt.js` must stay the first script in `<head>`: it keeps links inside the
  standalone iOS web-app instead of bouncing to Safari.
- Splash screens are per-device-size `<link rel="apple-touch-startup-image">` entries in
  `base/head.html`; a new iPhone size means a new PNG in `static/images/splashscreens/`
  and a new line there.
- `static/generated/` holds per-user PNG charts named
  `<username>_<UTC timestamp>_<kind>.png`; the timestamp defeats caching and
  `cleanup_distribution_plots` deletes the user's previous ones on each render.

## External services

- **TMDb** (`lib/tmdb.py`) — search, movie details (`append_to_response=credits`) and watch
  providers. `search`/`get` are `lru_cache`d per process; `get_bulk` fan-outs with
  `request_boost`. Careful with the cache: a cached dict is mutated by callers, hence the
  `.copy()` in `TitleCollector.collect`.
- **Overseerr** (`lib/overseerr.py`) — used to request movies on the household Plex. It may
  be unreachable; the client sets `is_available = False` instead of raising, and every call
  site must check it.
- **Pushover** (`lib/push.py`) — alerts from the cron scripts on failure.
- **IMDb datasets** — downloaded by `lib/etl.py`, which truncates the target `imdb.*` table
  and re-inserts in batches of 1000 with generated INSERT statements. It is written to run
  with very little memory, so keep it streaming: no `read_csv` of the whole file.

## Style

Follow the surrounding code: 4-space indent, single quotes, f-strings, short comments in the
imperative above each block, type hints in `lib/` and helper functions but not in routes.
Keep new page logic in `routes.py` next to its siblings rather than starting a blueprint,
unless the change is big enough to justify the refactor.
