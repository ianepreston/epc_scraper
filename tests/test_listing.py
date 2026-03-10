"""Tests for EPC listing page scraper."""

import pytest

from epc_scraper.listing import (
    _extract_ajax_target,
    _extract_osvstate,
    _parse_total_records,
    parse_listing_page,
    scrape_listing,
)
from epc_scraper.models import LISTING_URL


class TestParseListingPage:
    """Tests for parse_listing_page."""

    def test_parses_rows(self, listing_page_html: str) -> None:
        records = parse_listing_page(listing_page_html)
        assert len(records) == 2

    def test_first_record_fields(self, listing_page_html: str) -> None:
        records = parse_listing_page(listing_page_html)
        r = records[0]
        assert r.serial_id == 22812
        assert r.serial_start == "1G33-24-0000000055928008"
        assert r.serial_end == "1G33-24-0000000055937094"
        assert r.vintage_year == 2024
        assert r.current_owner == "TransCanada PipeLines Limited"
        assert r.status == "Active"
        assert r.quantity == 9087

    def test_second_record_fields(self, listing_page_html: str) -> None:
        records = parse_listing_page(listing_page_html)
        r = records[1]
        assert r.serial_id == 21448
        assert r.quantity == 34083

    def test_empty_table(self) -> None:
        html = """
        <html><body>
        <table class="TableRecords"><tbody></tbody></table>
        </body></html>
        """
        records = parse_listing_page(html)
        assert records == []

    def test_skips_rows_without_serial_link(self) -> None:
        html = """
        <html><body>
        <table class="TableRecords"><tbody>
        <tr>
            <td><div><a href="SomethingElse.aspx">No SerialId</a></div></td>
            <td>2024</td><td>Owner</td><td>Active</td><td>100</td>
        </tr>
        </tbody></table>
        </body></html>
        """
        records = parse_listing_page(html)
        assert records == []


class TestParseTotalRecords:
    """Tests for _parse_total_records."""

    def test_extracts_total(self, listing_page_html: str) -> None:
        assert _parse_total_records(listing_page_html) == 250

    def test_raises_on_missing(self) -> None:
        with pytest.raises(ValueError, match="Cannot find record count"):
            _parse_total_records("<html></html>")


class TestExtractOsvstate:
    """Tests for _extract_osvstate."""

    def test_extracts_value(self, listing_page_html: str) -> None:
        assert _extract_osvstate(listing_page_html) == "fake_state"

    def test_raises_on_missing(self) -> None:
        with pytest.raises(ValueError, match="Cannot find __OSVSTATE"):
            _extract_osvstate("<html></html>")


class TestExtractAjaxTarget:
    """Tests for _extract_ajax_target."""

    def test_extracts_next_link(self, listing_page_html: str) -> None:
        result = _extract_ajax_target(listing_page_html, "ListNavigation_Next")
        assert result is not None
        element_id, postback_name = result
        assert element_id == "next_id"
        assert postback_name == "next_name"

    def test_returns_none_for_missing_class(self, listing_page_html: str) -> None:
        result = _extract_ajax_target(listing_page_html, "NonExistent")
        assert result is None


class TestScrapeListingIntegration:
    """Integration test for scrape_listing with mocked HTTP."""

    async def test_single_page(self, listing_page_html: str) -> None:
        import respx

        single_page_html = listing_page_html.replace(
            "1 to 100 of 250 records",
            "1 to 2 of 2 records",
        )

        with respx.mock:
            respx.get(LISTING_URL).respond(200, text=single_page_html)
            records = [r async for r in scrape_listing(delay=0.0)]

        assert len(records) == 2
        assert records[0].serial_id == 22812
        assert records[1].serial_id == 21448
