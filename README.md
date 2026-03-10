# epc-scraper

A Python library for scraping Emissions Performance Credit (EPC) data from the
[Alberta CSA Registry](https://alberta.csaregistries.ca/GHGR_Listing/EPC_Listing.aspx).

The registry's main listing page and CSV export omit a critical field:
**originating owner**. This makes it impossible to determine whether a credit
has been transferred between parties. `epc-scraper` solves this by
automatically fetching each credit's detail page, extracting the originating
owner and facility, and combining everything into a single enriched dataset.

## Installation

Requires Python 3.11+.

```bash
pip install git+https://github.com/ianepreston/epc_scraper.git
```

To include export support (CSV, Parquet, Polars DataFrames):

```bash
pip install "epc-scraper[export] @ git+https://github.com/ianepreston/epc_scraper.git"
```

## Quick start

```python
from epc_scraper import scrape_all_sync, to_polars

credits = scrape_all_sync()
df = to_polars(credits)
print(df)
```

`scrape_all_sync` navigates all pages of the registry listing, then fetches
each credit's detail page concurrently. With default settings (~2,800 credits,
10 concurrent requests, 0.5s delay) this takes a few minutes.

## API reference

### Scraping

**`scrape_all_sync(concurrency=10, delay=0.5)`** -- Scrape all credits and
return a `list[EPCCredit]`. This is a synchronous wrapper suitable for scripts
and notebooks.

**`await scrape_all(concurrency=10, delay=0.5)`** -- Async version for use in
async contexts.

Parameters:

- `concurrency` -- Maximum number of parallel detail page requests.
- `delay` -- Seconds to wait between requests. Increase if you experience
  rate limiting.

### Export

All export functions require the `export` extra (`polars`).

- **`to_polars(credits)`** -- Returns a `polars.DataFrame`.
- **`to_csv(credits, path)`** -- Writes a CSV file.
- **`to_parquet(credits, path)`** -- Writes a Parquet file.

### Data model

Each `EPCCredit` record contains:

| Field                      | Type         | Description                                |
|----------------------------|--------------|--------------------------------------------|
| `serial_id`                | `int`        | Registry identifier for this serial range  |
| `serial_start`             | `str`        | Start of the EPC serial number range       |
| `serial_end`               | `str`        | End of the EPC serial number range         |
| `vintage_year`             | `int`        | Year the credits were generated            |
| `quantity`                 | `int`        | Number of credits in the range             |
| `current_owner`            | `str`        | Current holder of the credits              |
| `current_facility`         | `str`        | Facility associated with current owner     |
| `originating_owner`        | `str`        | Original generator of the credits          |
| `originating_facility`     | `str`        | Facility associated with originating owner |
| `status`                   | `str`        | Credit status (Active, Retired, etc.)      |
| `expiry_date`              | `date`       | Expiration date of the credits             |
| `transaction_id`           | `str`        | Registry transaction identifier            |
| `province`                 | `str`        | Province of origin                         |
| `country`                  | `str`        | Country of origin                          |
| `credit_retirement_reason` | `str | None` | Retirement reason, if applicable           |

## Usage in a Databricks notebook

Install the library and export a CSV to the same workspace folder as the
running notebook:

```python
# Cell 1 - Install
%pip install "epc-scraper[export] @ git+https://github.com/ianepreston/epc_scraper.git"
dbutils.library.restartPython()
```

```python
# Cell 2 - Scrape and export
import os
from epc_scraper import scrape_all_sync, to_csv

credits = scrape_all_sync()

notebook_path = dbutils.notebook.entry_point.getDbutils() \
    .notebook().getContext().notebookPath().get()
workspace_dir = os.path.dirname(notebook_path)
output_path = os.path.join("/Workspace", workspace_dir, "epc_credits.csv")

to_csv(credits, output_path)
print(f"Wrote {len(credits)} credits to {output_path}")
```

## Development

```bash
git clone https://github.com/ianepreston/epc_scraper.git
cd epc_scraper
uv sync --all-extras
uv run pytest
uv run mypy src/
uv run ruff check src/ tests/
```

## License

See [LICENSE](LICENSE) for details.
