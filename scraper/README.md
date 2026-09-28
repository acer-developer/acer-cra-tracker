# CRA ingestion pipeline

Fetches published rating actions from the seven Indian CRAs and writes them into
the same Postgres the web app reads. Two modes:

- `backfill` — paginate an agency's entire online listing back to its oldest
  available entry (one-time; the sites keep roughly 2–3 years searchable).
- `incremental` — read only the newest page(s); run daily.

## Source access, per agency (from live recon)

| Agency        | Source host                              | Access method |
|---------------|------------------------------------------|---------------|
| CRISIL        | www.crisil.com                           | server-rendered rationale search, paginate HTML |
| CARE          | www.careratings.com                      | Laravel JSON search endpoint (CSRF) + PDFs under `/upload/CompanyFiles/PR/` |
| ICRA          | www.icra.in                              | Vue SPA backed by a JSON API — call the API directly |
| India Ratings | www.indiaratings.co.in                   | JS-loaded press-release list backed by a JSON API |
| Infomerics    | infomericstorage.blob.core.windows.net   | PDFs in Azure Blob; listing on infomerics.com |
| Acuité        | connect.acuite.in                        | data/connect portal |
| Brickwork     | www.brickworkratings.com                 | ASP.NET (.aspx) postback listing |

Only `care.py` is a complete reference implementation. The other six are stubs
with the recon notes above; fill each `fetch_listing` by opening the agency's
listing in a browser, watching the Network tab for the JSON call (SPAs) or the
listing HTML (server-rendered), and returning `ListingItem`s.

## Legal / responsible use

These are public regulatory disclosures, but each site has Terms of Use and may
rate-limit or block automated access. Before a full backfill: read each agency's
robots.txt and ToS, keep the request rate low (the default is 1 req / 1.5 s with
backoff), set a truthful User-Agent, and stop if a site asks you to. This is your
call to make as the operator.

## Run

    pip install -r requirements.txt
    export DATABASE_URL=postgresql://...        # same DB as the web app
    python run.py --agency CARE --mode incremental
    python run.py --agency CARE --mode backfill --max-pages 500
    python run.py --agency ALL  --mode incremental      # daily job

The GitHub Action in `.github/workflows/ingest.yml` runs `ALL / incremental`
daily; trigger a `backfill` manually from the Actions tab.
