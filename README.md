# ACER CRA Tracker

A rating-intelligence app that indexes rating actions from the seven Indian credit
rating agencies (CRISIL, CARE, ICRA, India Ratings, Infomerics, Acuité, Brickwork),
parsed from each agency's published press releases. Frontend + API on Next.js;
data in Postgres; a Python pipeline ingests the agencies.

## Architecture

```
Next.js (Vercel)                Postgres (Neon/Supabase)         Python scraper (GitHub Actions)
  app/            dashboard        RatingAction / Entity            scraper/adapters/*  per-agency
  app/api/        JSON API   <-->  IngestRun (run log)     <--     scraper/run.py      orchestrator
```

- **Web:** `app/` (dashboard) + `app/api/stats/summary` + `app/api/rating-actions/page`.
- **Data model:** `prisma/schema.prisma` — one `RatingAction` row per action, mirrors
  the fields of the reference product (grade, band, amount, source PDF URL, INC flag,
  superseded flag).
- **Ingestion:** `scraper/` — see `scraper/README.md`. Runs `backfill` once (paginate
  each agency's full online history, ~3 years deep) then `incremental` daily.

## Setup

1. **Database** — create a free Postgres (Neon or Supabase). Copy its connection
   string.
2. **Env** — `cp .env.example .env` and set `DATABASE_URL`.
3. **Install + schema:**
   ```
   npm install
   npm run db:push          # creates the tables
   npm run dev              # http://localhost:3000  (shows the empty state until ingested)
   ```
4. **Ingest** (fills the DB — run from the repo root so the package imports resolve):
   ```
   pip install -r scraper/requirements.txt
   python -m scraper.run --agency CARE --mode incremental   # test one agency
   python -m scraper.run --agency CARE --mode backfill      # full history for CARE
   ```
   Only CARE is a complete adapter; the other six are stubs with recon notes in
   `scraper/adapters/` — finish each `fetch_listing` from the agency's Network tab.

## Deploy (Vercel)

1. Push this repo to GitHub.
2. Import it at vercel.com → New Project.
3. Add env var `DATABASE_URL` (same Postgres) in Project Settings.
4. Deploy. Build runs `prisma generate && next build`.
5. Add `DATABASE_URL` as a **GitHub Actions secret** too, so the daily
   `.github/workflows/ingest.yml` job can write to the same DB.

## Status

- [x] App shell, dashboard, stats + rating-actions APIs, data model
- [x] Ingestion framework, PDF parser, DB upsert, CARE reference adapter
- [ ] Six remaining agency adapters (stubs with recon notes)
- [ ] Auth / multi-tenant (the reference product has OTP + orgs; not built here yet)
- [ ] Full 3-year backfill (operator-run; respects robots.txt + rate limits)
