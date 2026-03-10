"""Scrape individual EPC credit detail pages."""

import logging
import re
from datetime import date

import httpx
from selectolax.parser import HTMLParser

from epc_scraper.models import DETAIL_URL, EPCCredit

logger = logging.getLogger(__name__)

_OWNER_FACILITY_RE = re.compile(r"^(.+?)\s*\((.+?)\)\s*$")


def _parse_owner_facility(cell_html: str) -> tuple[str, str]:
    """Parse owner name and facility from a detail page cell.

    The cell contains an <a> tag with the owner name, followed by
    the facility name in parentheses as plain text.

    Args:
        cell_html: Raw inner HTML of the ShowRecord_Value td.

    Returns:
        Tuple of (owner_name, facility_name).
    """
    fragment = HTMLParser(cell_html)
    link = fragment.css_first("a")
    owner = link.text(strip=True) if link else ""

    full_text = fragment.body.text(strip=True) if fragment.body else ""
    if not owner:
        match = _OWNER_FACILITY_RE.match(full_text)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return full_text, ""

    remainder = full_text.replace(owner, "", 1).strip()
    match = re.match(r"\((.+?)\)", remainder)
    facility = match.group(1).strip() if match else ""
    return owner, facility


def parse_detail_html(html: str, serial_id: int) -> EPCCredit:
    """Parse a detail page HTML into an EPCCredit.

    Args:
        html: Raw HTML of the detail page.
        serial_id: The serial ID used to fetch this page.

    Returns:
        Parsed EPCCredit instance.

    Raises:
        ValueError: If required fields are missing from the page.
    """
    tree = HTMLParser(html)
    rows = tree.css("table.ShowRecord tr")

    fields: dict[str, str] = {}
    raw_html: dict[str, str] = {}
    for row in rows:
        cells = row.css("td")
        if len(cells) < 2:
            continue
        label = cells[0].text(strip=True).rstrip(":")
        fields[label] = cells[1].text(strip=True)
        raw_html[label] = cells[1].html or ""

    serial_text = fields.get("EPC Serial Number", "")
    parts = [p.strip() for p in serial_text.split(" to ")]
    if len(parts) != 2:
        raise ValueError(
            f"Cannot parse serial range from '{serial_text}' (SerialId={serial_id})"
        )

    current_owner, current_facility = _parse_owner_facility(
        raw_html.get("Current Owner (Facility)", "")
    )
    originating_owner, originating_facility = _parse_owner_facility(
        raw_html.get("Originating Owner (Facility)", "")
    )

    quantity_str = fields.get("Quantity", "0").replace(",", "")
    expiry_str = fields.get("Expiry Date", "")
    retirement_reason = fields.get("Credit Retirement Reason") or None

    return EPCCredit(
        serial_id=serial_id,
        serial_start=parts[0],
        serial_end=parts[1],
        vintage_year=int(fields.get("Vintage Year", "0")),
        quantity=int(quantity_str),
        current_owner=current_owner,
        current_facility=current_facility,
        originating_owner=originating_owner,
        originating_facility=originating_facility,
        status=fields.get("Current Status", ""),
        expiry_date=date.fromisoformat(expiry_str),
        transaction_id=fields.get("Transaction Id", ""),
        province=fields.get("Province", ""),
        country=fields.get("Country", ""),
        credit_retirement_reason=retirement_reason,
    )


async def scrape_detail(client: httpx.AsyncClient, serial_id: int) -> EPCCredit:
    """Fetch and parse a single EPC credit detail page.

    Args:
        client: Async HTTP client to use for the request.
        serial_id: The serial range ID to look up.

    Returns:
        Parsed EPCCredit instance.

    Raises:
        httpx.HTTPStatusError: If the HTTP request fails.
        ValueError: If the page cannot be parsed.
    """
    url = f"{DETAIL_URL}?SerialId={serial_id}"
    response = await client.get(url)
    response.raise_for_status()
    return parse_detail_html(response.text, serial_id)
