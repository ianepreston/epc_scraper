"""Tests for EPC detail page scraper."""

from datetime import date

import httpx
import pytest
import respx

from epc_scraper.detail import parse_detail_html, scrape_detail
from epc_scraper.models import DETAIL_URL


class TestParseDetailHtml:
    """Tests for parse_detail_html."""

    def test_parses_all_fields(self, detail_html: str) -> None:
        credit = parse_detail_html(detail_html, serial_id=22812)

        assert credit.serial_id == 22812
        assert credit.serial_start == "1G33-24-0000000055928008"
        assert credit.serial_end == "1G33-24-0000000055937094"
        assert credit.vintage_year == 2024
        assert credit.quantity == 9087
        assert credit.current_owner == "TransCanada PipeLines Limited"
        assert credit.current_facility == "TransCanada Alberta System"
        assert credit.originating_owner == "TransAlta Renewables"
        assert credit.originating_facility == "Castle Wind Farm"
        assert credit.status == "Active"
        assert credit.expiry_date == date(2030, 7, 5)
        assert credit.transaction_id == "202602270011"
        assert credit.province == "Alberta"
        assert credit.country == "Canada"
        assert credit.credit_retirement_reason is None

    def test_parses_retirement_reason(self, detail_html_with_retirement: str) -> None:
        credit = parse_detail_html(detail_html_with_retirement, serial_id=22812)
        assert credit.credit_retirement_reason == "Compliance"

    def test_handles_no_facility(self, detail_html_no_facility: str) -> None:
        credit = parse_detail_html(detail_html_no_facility, serial_id=99)
        assert credit.current_owner == "SomeOwner"
        assert credit.current_facility == ""
        assert credit.originating_owner == "OrigOwner"
        assert credit.originating_facility == ""

    def test_raises_on_bad_serial_range(self) -> None:
        bad_html = """
        <html><body>
        <table class="ShowRecord OSFillParent">
        <tr>
            <td class="ShowRecord_Caption">EPC Serial Number:</td>
            <td class="ShowRecord_Value">INVALID</td>
        </tr>
        </table>
        </body></html>
        """
        with pytest.raises(ValueError, match="Cannot parse serial range"):
            parse_detail_html(bad_html, serial_id=1)


class TestScrapeDetail:
    """Tests for the async scrape_detail function."""

    @respx.mock
    async def test_fetches_and_parses(self, detail_html: str) -> None:
        url = f"{DETAIL_URL}?SerialId=22812"
        respx.get(url).respond(200, text=detail_html)

        async with httpx.AsyncClient() as client:
            credit = await scrape_detail(client, 22812)

        assert credit.serial_id == 22812
        assert credit.current_owner == "TransCanada PipeLines Limited"

    @respx.mock
    async def test_raises_on_http_error(self) -> None:
        url = f"{DETAIL_URL}?SerialId=99999"
        respx.get(url).respond(404)

        async with httpx.AsyncClient() as client:
            with pytest.raises(httpx.HTTPStatusError):
                await scrape_detail(client, 99999)
