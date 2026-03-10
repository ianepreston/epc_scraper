"""Tests for EPC export functions."""

from datetime import date
from pathlib import Path

import polars as pl

from epc_scraper.export import to_csv, to_parquet, to_polars
from epc_scraper.models import EPCCredit

SAMPLE_CREDIT = EPCCredit(
    serial_id=22812,
    serial_start="1G33-24-0000000055928008",
    serial_end="1G33-24-0000000055937094",
    vintage_year=2024,
    quantity=9087,
    current_owner="TransCanada PipeLines Limited",
    current_facility="TransCanada Alberta System",
    originating_owner="TransAlta Renewables",
    originating_facility="Castle Wind Farm",
    status="Active",
    expiry_date=date(2030, 7, 5),
    transaction_id="202602270011",
    province="Alberta",
    country="Canada",
)


class TestToPolars:
    """Tests for to_polars."""

    def test_converts_to_dataframe(self) -> None:
        df = to_polars([SAMPLE_CREDIT])
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (1, 15)

    def test_field_values(self) -> None:
        df = to_polars([SAMPLE_CREDIT])
        assert df["serial_id"][0] == 22812
        assert df["current_owner"][0] == "TransCanada PipeLines Limited"
        assert df["originating_owner"][0] == "TransAlta Renewables"
        assert df["quantity"][0] == 9087

    def test_empty_list(self) -> None:
        df = to_polars([])
        assert df.shape[0] == 0


class TestToCsv:
    """Tests for to_csv."""

    def test_writes_csv(self, tmp_path: Path) -> None:
        out = tmp_path / "test.csv"
        to_csv([SAMPLE_CREDIT], out)
        assert out.exists()
        content = out.read_text()
        assert "TransCanada PipeLines Limited" in content
        assert "22812" in content


class TestToParquet:
    """Tests for to_parquet."""

    def test_writes_parquet(self, tmp_path: Path) -> None:
        out = tmp_path / "test.parquet"
        to_parquet([SAMPLE_CREDIT], out)
        assert out.exists()
        df = pl.read_parquet(out)
        assert df.shape == (1, 15)
        assert df["serial_id"][0] == 22812
