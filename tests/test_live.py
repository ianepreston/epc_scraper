"""Live integration tests against the real EPC registry.

These tests make actual HTTP requests and are skipped by default.
Run with: uv run pytest -m live
"""

from datetime import date

import httpx
import pytest

from epc_scraper.detail import scrape_detail
from epc_scraper.listing import (
    _extract_ajax_target,
    _extract_form_fields,
    _extract_osvstate,
    _parse_total_records,
    parse_listing_page,
)
from epc_scraper.models import DETAIL_URL, LISTING_URL, EPCCredit, EPCListingRecord

pytestmark = pytest.mark.live

KNOWN_SERIAL_ID = 22812


class TestLiveListing:
    """Verify listing page scraping against the real site."""

    async def test_fetch_first_page(self) -> None:
        """First page loads and contains parseable records."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(LISTING_URL)
            response.raise_for_status()

        html = response.text
        total = _parse_total_records(html)
        assert total > 0, "Expected at least one record in the registry"

        records = parse_listing_page(html)
        assert len(records) > 0, "Expected records on the first page"
        assert len(records) <= 100, "Page should contain at most 100 records"

    async def test_listing_records_are_valid(self) -> None:
        """Each parsed record has sensible field values."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(LISTING_URL)
            response.raise_for_status()

        records = parse_listing_page(response.text)
        for record in records:
            assert isinstance(record, EPCListingRecord)
            assert record.serial_id > 0
            assert len(record.serial_start) > 0
            assert len(record.serial_end) > 0
            assert record.vintage_year >= 2000
            assert record.quantity > 0
            assert len(record.current_owner) > 0
            assert len(record.status) > 0

    async def test_pagination_state_present(self) -> None:
        """First page contains the fields needed for AJAX pagination."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(LISTING_URL)
            response.raise_for_status()

        html = response.text
        osvstate = _extract_osvstate(html)
        assert len(osvstate) > 0, "Expected __OSVSTATE to be non-empty"

        next_target = _extract_ajax_target(html, "ListNavigation_Next")
        assert next_target is not None, "Expected a 'next' pagination link"

        form_fields = _extract_form_fields(html)
        assert "__OSVSTATE" in form_fields
        assert "__VIEWSTATE" in form_fields

    async def test_second_page_loads(self) -> None:
        """Can navigate to page 2 via standard ASP.NET postback."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(LISTING_URL)
            response.raise_for_status()
            page1_html = response.text

            next_target = _extract_ajax_target(page1_html, "ListNavigation_Next")
            assert next_target is not None
            _element_id, postback_name = next_target

            fields = _extract_form_fields(page1_html)
            form_data = {
                "__OSVSTATE": fields["__OSVSTATE"],
                "__VIEWSTATE": "",
                "__VIEWSTATEGENERATOR": fields.get("__VIEWSTATEGENERATOR", ""),
                "__EVENTTARGET": postback_name,
                "__EVENTARGUMENT": "",
            }

            response = await client.post(LISTING_URL, data=form_data)
            response.raise_for_status()

        page2_records = parse_listing_page(response.text)
        assert len(page2_records) > 0, "Expected records on page 2"

        page1_records = parse_listing_page(page1_html)
        page1_ids = {r.serial_id for r in page1_records}
        page2_ids = {r.serial_id for r in page2_records}
        assert page1_ids.isdisjoint(page2_ids), (
            "Pages 1 and 2 should not share serial IDs"
        )


class TestLiveDetail:
    """Verify detail page scraping against the real site."""

    async def test_fetch_known_detail(self) -> None:
        """Fetch a known serial ID and verify it parses."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            credit = await scrape_detail(client, KNOWN_SERIAL_ID)

        assert isinstance(credit, EPCCredit)
        assert credit.serial_id == KNOWN_SERIAL_ID

    async def test_detail_fields_populated(self) -> None:
        """All required fields on the detail page are non-empty."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            credit = await scrape_detail(client, KNOWN_SERIAL_ID)

        assert len(credit.serial_start) > 0
        assert len(credit.serial_end) > 0
        assert credit.vintage_year >= 2000
        assert credit.quantity > 0
        assert len(credit.current_owner) > 0
        assert len(credit.originating_owner) > 0
        assert len(credit.status) > 0
        assert credit.expiry_date >= date(2020, 1, 1)
        assert len(credit.transaction_id) > 0
        assert len(credit.province) > 0
        assert len(credit.country) > 0

    async def test_detail_page_returns_html(self) -> None:
        """Raw HTTP response contains the expected ShowRecord table."""
        url = f"{DETAIL_URL}?SerialId={KNOWN_SERIAL_ID}"
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

        assert "ShowRecord" in response.text
        assert "EPC Serial Number" in response.text
        assert "Originating Owner" in response.text

    async def test_multiple_detail_pages(self) -> None:
        """Fetch the first few serial IDs from the listing and parse each."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(LISTING_URL)
            response.raise_for_status()
            records = parse_listing_page(response.text)

            sample = records[:3]
            for record in sample:
                credit = await scrape_detail(client, record.serial_id)
                assert credit.serial_id == record.serial_id
                assert credit.quantity > 0
                assert len(credit.originating_owner) > 0
