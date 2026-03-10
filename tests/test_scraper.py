"""Tests for the EPC scraper orchestrator."""

import respx

from epc_scraper.models import DETAIL_URL, LISTING_URL
from epc_scraper.scraper import scrape_all
from tests.conftest import DETAIL_HTML, LISTING_PAGE_HTML


class TestScrapeAll:
    """Tests for the scrape_all orchestrator."""

    @respx.mock
    async def test_full_pipeline(self) -> None:
        single_page_html = LISTING_PAGE_HTML.replace(
            "1 to 100 of 250 records",
            "1 to 2 of 2 records",
        )
        respx.get(LISTING_URL).respond(200, text=single_page_html)

        respx.get(f"{DETAIL_URL}?SerialId=22812").respond(200, text=DETAIL_HTML)
        detail_21448 = DETAIL_HTML.replace(
            "1G33-24-0000000055928008 to 1G33-24-0000000055937094",
            "1M23-24-0000000055401404 to 1M23-24-0000000055435486",
        ).replace("9,087", "34,083")
        respx.get(f"{DETAIL_URL}?SerialId=21448").respond(200, text=detail_21448)

        credits = await scrape_all(concurrency=2, delay=0.0)

        assert len(credits) == 2
        serial_ids = {c.serial_id for c in credits}
        assert serial_ids == {22812, 21448}

    @respx.mock
    async def test_handles_detail_errors(self) -> None:
        single_page_html = LISTING_PAGE_HTML.replace(
            "1 to 100 of 250 records",
            "1 to 2 of 2 records",
        )
        respx.get(LISTING_URL).respond(200, text=single_page_html)

        respx.get(f"{DETAIL_URL}?SerialId=22812").respond(200, text=DETAIL_HTML)
        respx.get(f"{DETAIL_URL}?SerialId=21448").respond(500)

        credits = await scrape_all(concurrency=2, delay=0.0)

        assert len(credits) == 1
        assert credits[0].serial_id == 22812
