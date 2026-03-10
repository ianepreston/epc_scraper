# Implementation Plan: EPC Scraper

## Overview

A Python package (`epc_scraper`) that scrapes Emissions Performance Credit data
from the Alberta CSA Registry, enriching the publicly available listing data
with originating owner information only available on individual credit detail
pages.

**Target site**: `https://alberta.csaregistries.ca/GHGR_Listing/EPC_Listing.aspx`

---

## Architecture

```
epc_scraper/
  src/
    epc_scraper/
      __init__.py          # Public API exports
      models.py            # Dataclasses for EPC data
      listing.py           # Scrape the paginated listing table
      detail.py            # Scrape individual credit detail pages
      scraper.py           # Orchestrator combining listing + detail
      export.py            # Conversion to CSV, Parquet, Polars DataFrame
  tests/
    conftest.py            # Shared fixtures (sample HTML fragments)
    test_models.py
    test_listing.py
    test_detail.py
    test_scraper.py
    test_export.py
    test_output/           # Directory for test artifacts
  pyproject.toml
  .gitignore               # (update to include test_output/)
```

---

## Data Models (`models.py`)

Two dataclasses representing the two levels of data:

### `EPCListingRecord`

Fields scraped from the listing table (one per row):

| Field            | Type            | Source                |
|------------------|-----------------|-----------------------|
| `serial_id`      | `int`           | Parsed from detail link href (`SerialId=`) |
| `serial_start`   | `str`           | Serial range text     |
| `serial_end`     | `str`           | Serial range text     |
| `vintage_year`   | `int`           | Vintage Year column   |
| `current_owner`  | `str`           | Owner column          |
| `status`         | `str`           | Status column         |
| `quantity`       | `int`           | Number of Credits column |
| `detail_url`     | `str`           | Constructed from `serial_id` |

### `EPCCredit`

The enriched record combining listing + detail page data:

| Field                    | Type              | Source       |
|--------------------------|-------------------|--------------|
| `serial_id`              | `int`             | Listing      |
| `serial_start`           | `str`             | Detail       |
| `serial_end`             | `str`             | Detail       |
| `vintage_year`           | `int`             | Detail       |
| `quantity`               | `int`             | Detail       |
| `current_owner`          | `str`             | Detail       |
| `current_facility`       | `str`             | Detail       |
| `originating_owner`      | `str`             | Detail       |
| `originating_facility`   | `str`             | Detail       |
| `status`                 | `str`             | Detail       |
| `expiry_date`            | `date`            | Detail       |
| `transaction_id`         | `str`             | Detail       |
| `province`               | `str`             | Detail       |
| `country`                | `str`             | Detail       |
| `credit_retirement_reason` | `str \| None`   | Detail       |

Both use `@dataclass(frozen=True, slots=True)` for immutability and memory
efficiency.

---

## Component Design

### 1. Listing Scraper (`listing.py`)

**Responsibility**: Navigate the paginated listing and extract all
`EPCListingRecord` objects.

**Key observations about the site**:
- ASP.NET / OutSystems framework with postback-based pagination
- Table ID contains `wtSerialTable`
- 100 records per page, ~2847 total records (29 pages)
- Each row links to `EPC_SerialRangeDetail.aspx?SerialId=[ID]`
- Pagination requires posting back ASP.NET form state (`__OSVSTATE`)

**Approach**:
- Use `httpx.AsyncClient` with a persistent session to maintain cookies/state
- `GET` the first page, parse the HTML with `selectolax` (fast HTML parser)
- Extract all rows from the table, yielding `EPCListingRecord` per row
- For pagination: parse the `__OSVSTATE` and any hidden fields from the current
  page, then `POST` back to advance to the next page
- If ASP.NET postback proves unreliable, fall back to parsing the page count
  from the "1 to 100 of N records" text and iterating via URL parameters or
  JavaScript-driven pagination replay
- Expose an async generator: `async def scrape_listing() -> AsyncIterator[EPCListingRecord]`

**Rate limiting**: Use a configurable delay between page requests (default 1s)
to be respectful to the server.

### 2. Detail Scraper (`detail.py`)

**Responsibility**: Fetch a single detail page and parse it into an `EPCCredit`.

**Approach**:
- Accept a `serial_id: int` and fetch
  `EPC_SerialRangeDetail.aspx?SerialId={serial_id}`
- Parse with `selectolax`; extract label-value pairs from the page structure
- Parse "Current Owner (Facility)" into separate `current_owner` and
  `current_facility` fields (split on parenthesized facility name)
- Same for "Originating Owner (Facility)"
- Parse date strings into `datetime.date` objects
- Parse quantity strings (remove commas) into `int`
- Return `EPCCredit`
- Expose: `async def scrape_detail(client: httpx.AsyncClient, serial_id: int) -> EPCCredit`

### 3. Orchestrator (`scraper.py`)

**Responsibility**: Coordinate listing + detail scraping with concurrency
control.

**Approach**:
- First, scrape all listing records to get the full set of `serial_id` values
- Then, scrape detail pages concurrently using `asyncio.Semaphore` to limit
  concurrency (default: 10 concurrent requests)
- Use `httpx.AsyncClient` connection pooling for efficiency
- Configurable delay between requests to avoid overwhelming the server
- Log progress using `logging` module
- Expose:
  ```python
  async def scrape_all(
      concurrency: int = 10,
      delay: float = 0.5,
  ) -> list[EPCCredit]
  ```
- Also expose a convenience sync wrapper:
  ```python
  def scrape_all_sync(
      concurrency: int = 10,
      delay: float = 0.5,
  ) -> list[EPCCredit]
  ```

### 4. Export (`export.py`)

**Responsibility**: Convert `list[EPCCredit]` to various output formats.

**Functions**:
- `to_polars(credits: list[EPCCredit]) -> polars.DataFrame`
- `to_csv(credits: list[EPCCredit], path: str | Path) -> None`
- `to_parquet(credits: list[EPCCredit], path: str | Path) -> None`

Polars is the canonical intermediate; CSV/Parquet write through Polars for
consistency and performance. Polars is listed as an optional dependency so the
core scraper works without it.

### 5. Public API (`__init__.py`)

Re-export the key symbols:
- `EPCCredit`, `EPCListingRecord`
- `scrape_all`, `scrape_all_sync`
- `to_polars`, `to_csv`, `to_parquet`

---

## Dependencies

### Required (core)

| Package      | Purpose                              |
|--------------|--------------------------------------|
| `httpx`      | Async HTTP client with connection pooling |
| `selectolax` | Fast HTML parsing (lxml alternative) |

### Optional (export)

| Package   | Purpose                    |
|-----------|----------------------------|
| `polars`  | DataFrame + Parquet/CSV export |

### Dev

| Package     | Purpose          |
|-------------|------------------|
| `pytest`    | Testing          |
| `pytest-asyncio` | Async test support |
| `respx`    | Mock httpx requests in tests |
| `mypy`     | Type checking    |
| `ruff`     | Linting/formatting |

---

## `pyproject.toml` Configuration

```toml
[project]
name = "epc-scraper"
version = "0.1.0"
description = "Scraper for Alberta Emissions Performance Credit registry data"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "selectolax>=0.3",
]

[project.optional-dependencies]
export = ["polars>=1.0"]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "respx>=0.22",
    "mypy>=1.10",
    "ruff>=0.6",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/epc_scraper"]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
strict = true
python_version = "3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## Testing Strategy

All tests mock HTTP responses using `respx`. No live network calls in tests.

### `test_listing.py`
- Mock the listing page HTML; verify correct extraction of all
  `EPCListingRecord` fields from a single page
- Mock multi-page navigation; verify all pages are traversed
- Test edge cases: empty table, malformed rows, missing links

### `test_detail.py`
- Mock a detail page; verify all `EPCCredit` fields are correctly parsed
- Test owner/facility splitting: `"Foo Corp (Bar Plant)"` -> owner=`"Foo Corp"`,
  facility=`"Bar Plant"`
- Test missing optional fields (e.g., no `credit_retirement_reason`)
- Test date and quantity parsing

### `test_models.py`
- Verify dataclass immutability (frozen)
- Verify field types

### `test_scraper.py`
- Mock listing + detail endpoints; verify full orchestration
- Verify concurrency semaphore limits parallel requests
- Verify progress logging

### `test_export.py`
- Verify `to_polars` produces correct schema and values
- Verify `to_csv` / `to_parquet` write valid files (write to `tests/test_output/`)

---

## Implementation Order

1. **`pyproject.toml`** + project scaffold (`src/`, `tests/`, `__init__.py` stubs)
2. **`models.py`** -- dataclasses are dependency-free
3. **`detail.py`** + `test_detail.py` -- simplest scraping target (single page, no pagination)
4. **`listing.py`** + `test_listing.py` -- pagination logic is the trickiest part
5. **`scraper.py`** + `test_scraper.py` -- orchestration
6. **`export.py`** + `test_export.py` -- output formats
7. **`__init__.py`** -- wire up public API
8. **Ruff + mypy pass** -- ensure all checks pass
9. **Manual integration test** against live site (not automated)

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| ASP.NET postback pagination is fragile | Parse page count from header text; if postback fails, try alternative approaches (e.g., direct URL manipulation, full form replay) |
| Site structure changes break parsing | Parsing functions are isolated in `listing.py` / `detail.py`; easy to update selectors without touching orchestration |
| Rate limiting / IP blocking | Configurable delay + concurrency limit; respectful defaults (0.5s delay, 10 concurrent) |
| Large number of detail pages (~2847) | Async concurrency keeps total time reasonable (~3-5 min at 10 concurrent with 0.5s delay) |
| OutSystems generates dynamic element IDs | Use text-based selectors and structural patterns rather than brittle element IDs |

---

## Usage Example

```python
from epc_scraper import scrape_all_sync, to_polars, to_csv

# Scrape all credits (takes a few minutes)
credits = scrape_all_sync(concurrency=10, delay=0.5)

# Convert to Polars DataFrame
df = to_polars(credits)
print(df)

# Export to files
to_csv(credits, "epc_credits.csv")
to_parquet(credits, "epc_credits.parquet")
```
