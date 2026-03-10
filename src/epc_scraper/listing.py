"""Scrape the paginated EPC listing table."""

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from urllib.parse import parse_qs, urlparse

import httpx
from selectolax.parser import HTMLParser

from epc_scraper.models import LISTING_URL, EPCListingRecord

logger = logging.getLogger(__name__)

_RECORD_COUNT_RE = re.compile(r"(\d+)\s+to\s+(\d+)\s+of\s+(\d+)\s+records")


def _parse_total_records(html: str) -> int:
    """Extract total record count from the 'X to Y of Z records' text.

    Args:
        html: Raw HTML of a listing page.

    Returns:
        Total number of records across all pages.

    Raises:
        ValueError: If the record count text cannot be found.
    """
    match = _RECORD_COUNT_RE.search(html)
    if not match:
        raise ValueError("Cannot find record count in listing page")
    return int(match.group(3))


def parse_listing_page(html: str) -> list[EPCListingRecord]:
    """Parse a single listing page into EPCListingRecord objects.

    Args:
        html: Raw HTML of a listing page.

    Returns:
        List of EPCListingRecord for each row in the table.
    """
    tree = HTMLParser(html)
    rows = tree.css("table.TableRecords tbody tr")
    records: list[EPCListingRecord] = []

    for row in rows:
        cells = row.css("td")
        if len(cells) < 5:
            continue

        link = cells[0].css_first("a[href*='SerialId']")
        if link is None:
            continue

        href = link.attributes.get("href") or ""
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        serial_id = int(str(qs["SerialId"][0]))

        serial_text = link.text(strip=True)
        serial_parts = [
            p.strip() for p in re.split(r"\s+to\s*", serial_text) if p.strip()
        ]
        if len(serial_parts) != 2:
            logger.error(
                f"Cannot parse serial range: '{serial_text}' (SerialId={serial_id})"
            )
            continue

        vintage_year = int(cells[1].text(strip=True))

        owner_link = cells[2].css_first("a")
        current_owner = (
            owner_link.text(strip=True) if owner_link else cells[2].text(strip=True)
        )

        status = cells[3].text(strip=True)
        quantity = int(cells[4].text(strip=True).replace(",", ""))

        records.append(
            EPCListingRecord(
                serial_id=serial_id,
                serial_start=serial_parts[0],
                serial_end=serial_parts[1],
                vintage_year=vintage_year,
                current_owner=current_owner,
                status=status,
                quantity=quantity,
            )
        )

    return records


def _extract_ajax_target(html: str, link_class: str) -> tuple[str, str] | None:
    """Extract the AJAX postback target ID and name from a navigation link.

    Args:
        html: Raw HTML of a listing page.
        link_class: CSS class of the navigation link to find.

    Returns:
        Tuple of (element_id, postback_name) or None if not found.
    """
    tree = HTMLParser(html)
    link = tree.css_first(f"a.{link_class}")
    if link is None:
        return None

    onclick = link.attributes.get("onclick") or ""
    match = re.search(r"OsAjax\([^,]+,'([^']+)','([^']+)'", onclick)
    if not match:
        return None
    return match.group(1), match.group(2)


def _extract_osvstate(html: str) -> str:
    """Extract the __OSVSTATE hidden field value from the page.

    Args:
        html: Raw HTML of a listing page.

    Returns:
        The OSVSTATE value string.

    Raises:
        ValueError: If the OSVSTATE field cannot be found.
    """
    tree = HTMLParser(html)
    field = tree.css_first("input[name='__OSVSTATE']")
    if field is None:
        raise ValueError("Cannot find __OSVSTATE in page")
    return field.attributes.get("value") or ""


async def scrape_listing(
    delay: float = 1.0,
) -> AsyncIterator[EPCListingRecord]:
    """Scrape all pages of the EPC listing table.

    Navigates through all pages using ASP.NET AJAX postbacks and
    yields each EPCListingRecord found.

    Args:
        delay: Seconds to wait between page requests.

    Yields:
        EPCListingRecord for each row across all pages.

    Raises:
        httpx.HTTPStatusError: If any HTTP request fails.
        ValueError: If page structure cannot be parsed.
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(LISTING_URL)
        response.raise_for_status()
        page_html = response.text

        total = _parse_total_records(page_html)
        pages = (total + 99) // 100
        logger.info(f"Found {total} records across {pages} pages")

        records = parse_listing_page(page_html)
        for record in records:
            yield record

        for page_num in range(2, pages + 1):
            await asyncio.sleep(delay)

            osvstate = _extract_osvstate(page_html)
            next_target = _extract_ajax_target(page_html, "ListNavigation_Next")
            if next_target is None:
                logger.warning(
                    f"No 'next' link found on page {page_num - 1}, stopping pagination"
                )
                break

            element_id, postback_name = next_target

            form_data = {
                "__OSVSTATE": osvstate,
                "__VIEWSTATE": "",
                "__VIEWSTATEGENERATOR": "CAC16F6E",
                "__AJAX": f"{element_id},,{postback_name},,",
            }

            response = await client.post(
                LISTING_URL,
                data=form_data,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": (
                        "application/x-www-form-urlencoded; charset=UTF-8"
                    ),
                },
            )
            response.raise_for_status()
            page_html = response.text

            records = parse_listing_page(page_html)
            logger.info(f"Page {page_num}/{pages}: {len(records)} records")
            for record in records:
                yield record
