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


def _extract_form_fields(html: str) -> dict[str, str]:
    """Extract all named input/select/textarea values from the page form.

    OutSystems AJAX posts require the full form serialization.
    The __OSVSTATE hidden input contains a placeholder value that
    gets replaced by JavaScript after DOM ready, so we also extract
    the real value from the inline script.

    Args:
        html: Raw HTML of a listing page.

    Returns:
        Dictionary of field name to value for all form inputs.
    """
    tree = HTMLParser(html)
    fields: dict[str, str] = {}

    for inp in tree.css("input[name]"):
        name = inp.attributes.get("name") or ""
        input_type = (inp.attributes.get("type") or "text").lower()
        if input_type in ("checkbox", "radio"):
            if inp.attributes.get("checked") is not None:
                fields[name] = inp.attributes.get("value") or "on"
        elif input_type != "submit":
            fields[name] = inp.attributes.get("value") or ""

    for sel in tree.css("select[name]"):
        name = sel.attributes.get("name") or ""
        selected = sel.css_first("option[selected]")
        fields[name] = (selected.attributes.get("value") or "") if selected else ""

    for ta in tree.css("textarea[name]"):
        name = ta.attributes.get("name") or ""
        fields[name] = ta.text() or ""

    js_osvstate = re.search(r"\('input\[name=__OSVSTATE\]'\)\.val\('([^']+)'\)", html)
    if js_osvstate:
        fields["__OSVSTATE"] = js_osvstate.group(1)

    return fields


def _extract_osvstate(html: str) -> str:
    """Extract the __OSVSTATE value from the page.

    OutSystems replaces the hidden input value via JavaScript after
    DOM ready, so prefer the JS-set value over the input attribute.

    Args:
        html: Raw HTML of a listing page.

    Returns:
        The OSVSTATE value string.

    Raises:
        ValueError: If the OSVSTATE field cannot be found.
    """
    js_match = re.search(r"\('input\[name=__OSVSTATE\]'\)\.val\('([^']+)'\)", html)
    if js_match:
        return js_match.group(1)

    tree = HTMLParser(html)
    field = tree.css_first("input[name='__OSVSTATE']")
    if field is None:
        raise ValueError("Cannot find __OSVSTATE in page")
    return field.attributes.get("value") or ""


async def scrape_listing(
    delay: float = 1.0,
) -> AsyncIterator[EPCListingRecord]:
    """Scrape all pages of the EPC listing table.

    Navigates through all pages using OutSystems AJAX postbacks,
    serializing the full form state for each page transition.

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

            next_target = _extract_ajax_target(page_html, "ListNavigation_Next")
            if next_target is None:
                logger.warning(
                    f"No 'next' link found on page {page_num - 1}, stopping pagination"
                )
                break

            _element_id, postback_name = next_target
            fields = _extract_form_fields(page_html)

            form_data = {
                "__OSVSTATE": fields["__OSVSTATE"],
                "__VIEWSTATE": "",
                "__VIEWSTATEGENERATOR": fields.get("__VIEWSTATEGENERATOR", ""),
                "__EVENTTARGET": postback_name,
                "__EVENTARGUMENT": "",
            }

            response = await client.post(LISTING_URL, data=form_data)
            response.raise_for_status()
            page_html = response.text

            records = parse_listing_page(page_html)
            logger.info(f"Page {page_num}/{pages}: {len(records)} records")
            for record in records:
                yield record
