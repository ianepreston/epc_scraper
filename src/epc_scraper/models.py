"""Data models for EPC registry records."""

from dataclasses import dataclass
from datetime import date

BASE_URL = "https://alberta.csaregistries.ca/GHGR_Listing"
LISTING_URL = f"{BASE_URL}/EPC_Listing.aspx"
DETAIL_URL = f"{BASE_URL}/EPC_SerialRangeDetail.aspx"


@dataclass(frozen=True, slots=True)
class EPCListingRecord:
    """A single row from the EPC listing table.

    Args:
        serial_id: Unique identifier parsed from the detail page link.
        serial_start: Start of the serial number range.
        serial_end: End of the serial number range.
        vintage_year: The vintage year of the credit.
        current_owner: Current owner as shown on the listing page.
        status: Credit status (e.g. Active, Pending Retirement).
        quantity: Number of credits in this serial range.
    """

    serial_id: int
    serial_start: str
    serial_end: str
    vintage_year: int
    current_owner: str
    status: str
    quantity: int

    @property
    def detail_url(self) -> str:
        """Construct the URL for the detail page of this record."""
        return f"{DETAIL_URL}?SerialId={self.serial_id}"


@dataclass(frozen=True, slots=True)
class EPCCredit:
    """Enriched EPC credit combining listing and detail page data.

    Args:
        serial_id: Unique identifier for this serial range.
        serial_start: Start of the serial number range.
        serial_end: End of the serial number range.
        vintage_year: The vintage year of the credit.
        quantity: Number of credits in this serial range.
        current_owner: Current owner of the credits.
        current_facility: Facility associated with the current owner.
        originating_owner: Original owner who generated the credits.
        originating_facility: Facility associated with the originating owner.
        status: Credit status (e.g. Active, Pending Retirement).
        expiry_date: Date when the credits expire.
        transaction_id: Registry transaction identifier.
        province: Province where the credits originate.
        country: Country where the credits originate.
        credit_retirement_reason: Reason for retirement, if applicable.
    """

    serial_id: int
    serial_start: str
    serial_end: str
    vintage_year: int
    quantity: int
    current_owner: str
    current_facility: str
    originating_owner: str
    originating_facility: str
    status: str
    expiry_date: date
    transaction_id: str
    province: str
    country: str
    credit_retirement_reason: str | None = None
