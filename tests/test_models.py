"""Tests for EPC data models."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from epc_scraper.models import (
    DETAIL_URL,
    EPCCredit,
    EPCListingRecord,
)


class TestEPCListingRecord:
    """Tests for EPCListingRecord dataclass."""

    def test_fields(self) -> None:
        record = EPCListingRecord(
            serial_id=22812,
            serial_start="1G33-24-0000000055928008",
            serial_end="1G33-24-0000000055937094",
            vintage_year=2024,
            current_owner="TransCanada PipeLines Limited",
            status="Active",
            quantity=9087,
        )
        assert record.serial_id == 22812
        assert record.vintage_year == 2024
        assert record.quantity == 9087

    def test_detail_url(self) -> None:
        record = EPCListingRecord(
            serial_id=22812,
            serial_start="1G33-24-0000000055928008",
            serial_end="1G33-24-0000000055937094",
            vintage_year=2024,
            current_owner="TransCanada PipeLines Limited",
            status="Active",
            quantity=9087,
        )
        assert record.detail_url == f"{DETAIL_URL}?SerialId=22812"

    def test_frozen(self) -> None:
        record = EPCListingRecord(
            serial_id=1,
            serial_start="a",
            serial_end="b",
            vintage_year=2024,
            current_owner="Owner",
            status="Active",
            quantity=100,
        )
        with pytest.raises(FrozenInstanceError):
            record.serial_id = 2  # type: ignore[misc]


class TestEPCCredit:
    """Tests for EPCCredit dataclass."""

    def test_fields(self) -> None:
        credit = EPCCredit(
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
        assert credit.originating_owner == "TransAlta Renewables"
        assert credit.credit_retirement_reason is None

    def test_optional_retirement_reason(self) -> None:
        credit = EPCCredit(
            serial_id=1,
            serial_start="a",
            serial_end="b",
            vintage_year=2024,
            quantity=100,
            current_owner="Owner",
            current_facility="Facility",
            originating_owner="Orig",
            originating_facility="Orig Facility",
            status="Retired",
            expiry_date=date(2030, 1, 1),
            transaction_id="123",
            province="Alberta",
            country="Canada",
            credit_retirement_reason="Compliance",
        )
        assert credit.credit_retirement_reason == "Compliance"

    def test_frozen(self) -> None:
        credit = EPCCredit(
            serial_id=1,
            serial_start="a",
            serial_end="b",
            vintage_year=2024,
            quantity=100,
            current_owner="Owner",
            current_facility="Facility",
            originating_owner="Orig",
            originating_facility="Orig Facility",
            status="Active",
            expiry_date=date(2030, 1, 1),
            transaction_id="123",
            province="Alberta",
            country="Canada",
        )
        with pytest.raises(FrozenInstanceError):
            credit.status = "Retired"  # type: ignore[misc]
