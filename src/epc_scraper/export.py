"""Export EPCCredit records to various formats."""

from dataclasses import asdict
from pathlib import Path

from epc_scraper.models import EPCCredit

try:
    import polars as pl

    _HAS_POLARS = True
except ImportError:
    _HAS_POLARS = False


def _require_polars() -> None:
    """Raise ImportError if polars is not installed.

    Raises:
        ImportError: If polars is not available.
    """
    if not _HAS_POLARS:
        raise ImportError(
            "polars is required for export functions. "
            "Install with: pip install epc-scraper[export]"
        )


def to_polars(credits: list[EPCCredit]) -> "pl.DataFrame":
    """Convert a list of EPCCredit to a Polars DataFrame.

    Args:
        credits: List of EPCCredit records.

    Returns:
        Polars DataFrame with one row per credit.

    Raises:
        ImportError: If polars is not installed.
    """
    _require_polars()
    rows = [asdict(c) for c in credits]
    return pl.DataFrame(rows)


def to_csv(credits: list[EPCCredit], path: str | Path) -> None:
    """Write EPCCredit records to a CSV file.

    Args:
        credits: List of EPCCredit records.
        path: Output file path.

    Raises:
        ImportError: If polars is not installed.
    """
    df = to_polars(credits)
    df.write_csv(str(path))


def to_parquet(credits: list[EPCCredit], path: str | Path) -> None:
    """Write EPCCredit records to a Parquet file.

    Args:
        credits: List of EPCCredit records.
        path: Output file path.

    Raises:
        ImportError: If polars is not installed.
    """
    df = to_polars(credits)
    df.write_parquet(str(path))
