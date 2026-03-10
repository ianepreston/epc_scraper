"""Shared test fixtures for EPC scraper tests."""

import pytest

DETAIL_HTML = """
<html><body>
<table class="ShowRecord OSFillParent" cellspacing="12" border="0">
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4" style="font-weight: bold;">
        <span role="heading" aria-level="1">EPC Serial Number: </span>
    </td>
    <td class="ShowRecord_Value" style="font-weight: bold;">
        1G33-24-0000000055928008 to 1G33-24-0000000055937094
    </td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">
        Current Owner (Facility):
    </td>
    <td class="ShowRecord_Value">
        <a class="underline_link"
           href="Company_ListingDetail.aspx?CompanyId=289">
            TransCanada PipeLines Limited
        </a>(TransCanada Alberta System)
    </td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">
        Originating Owner (Facility):
    </td>
    <td class="ShowRecord_Value">
        <a class="underline_link"
           href="Company_ListingDetail.aspx?CompanyId=35">
            TransAlta Renewables
        </a> (Castle Wind Farm)
    </td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Vintage Year:</td>
    <td class="ShowRecord_Value">2024</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Quantity:</td>
    <td class="ShowRecord_Value">9,087</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Current Status:</td>
    <td class="ShowRecord_Value">Active</td>
</tr>
<tr style="display:none;">
    <td class="ShowRecord_Caption ThemeGrid_Width4">
        Credit Retirement Reason:
    </td>
    <td class="ShowRecord_Value"></td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Expiry Date</td>
    <td class="ShowRecord_Value">2030-07-05</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Transaction Id</td>
    <td class="ShowRecord_Value">202602270011</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Province:</td>
    <td class="ShowRecord_Value">Alberta</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Country:</td>
    <td class="ShowRecord_Value">Canada</td>
</tr>
</table>
</body></html>
"""

DETAIL_HTML_WITH_RETIREMENT = DETAIL_HTML.replace(
    '<tr style="display:none;">\n'
    "    <td "
    'class="ShowRecord_Caption ThemeGrid_Width4">\n'
    "        Credit Retirement Reason:\n"
    "    </td>\n"
    '    <td class="ShowRecord_Value"></td>\n'
    "</tr>",
    "<tr>\n"
    '    <td class="ShowRecord_Caption ThemeGrid_Width4">'
    "Credit Retirement Reason:</td>\n"
    '    <td class="ShowRecord_Value">Compliance</td>\n'
    "</tr>",
)

DETAIL_HTML_NO_FACILITY = """
<html><body>
<table class="ShowRecord OSFillParent" cellspacing="12" border="0">
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4" style="font-weight: bold;">
        <span role="heading" aria-level="1">EPC Serial Number: </span>
    </td>
    <td class="ShowRecord_Value" style="font-weight: bold;">
        1A00-24-0000000000000001 to 1A00-24-0000000000000010
    </td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">
        Current Owner (Facility):
    </td>
    <td class="ShowRecord_Value">
        <a class="underline_link"
           href="Company_ListingDetail.aspx?CompanyId=1">
            SomeOwner
        </a>
    </td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">
        Originating Owner (Facility):
    </td>
    <td class="ShowRecord_Value">
        <a class="underline_link"
           href="Company_ListingDetail.aspx?CompanyId=2">
            OrigOwner
        </a>
    </td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Vintage Year:</td>
    <td class="ShowRecord_Value">2024</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Quantity:</td>
    <td class="ShowRecord_Value">10</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Current Status:</td>
    <td class="ShowRecord_Value">Active</td>
</tr>
<tr style="display:none;">
    <td class="ShowRecord_Caption ThemeGrid_Width4">
        Credit Retirement Reason:
    </td>
    <td class="ShowRecord_Value"></td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Expiry Date</td>
    <td class="ShowRecord_Value">2030-01-01</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Transaction Id</td>
    <td class="ShowRecord_Value">123456</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Province:</td>
    <td class="ShowRecord_Value">Alberta</td>
</tr>
<tr>
    <td class="ShowRecord_Caption ThemeGrid_Width4">Country:</td>
    <td class="ShowRecord_Value">Canada</td>
</tr>
</table>
</body></html>
"""

LISTING_PAGE_HTML = """
<html><body>
<form method="post" action="EPC_Listing.aspx" id="WebForm1">
<input type="hidden" name="__OSVSTATE" id="__OSVSTATE" value="fake_state" />
<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="" />
<input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR"
       value="CAC16F6E" />
<div class="Counter_Message">1 to 100 of 250 records</div>
<nav class="ListNavigation_Wrapper" aria-label="Pagination Navigation">
    <span class="ListNavigation_DisabledPrevious">previous</span>
    <span id="PageNav">
        <span class="ListNavigation_CurrentPageNumber">1</span>
        <a class="ListNavigation_PageNumber"
           onclick="OsAjax(arguments[0],'pg2_id','pg2_name','','__OSVSTATE,','');"
           href="#">2</a>
        <a class="ListNavigation_PageNumber"
           onclick="OsAjax(arguments[0],'pg3_id','pg3_name','','__OSVSTATE,','');"
           href="#">3</a>
    </span>
    <a class="ListNavigation_Next"
       onclick="OsAjax(arguments[0],'next_id','next_name','','__OSVSTATE,','');"
       href="#">next</a>
</nav>
<div id="ListContainer">
<table class="TableRecords" id="wtSerialTable">
<thead><tr>
    <th class="TableRecords_Header">Serial Ranges</th>
    <th class="TableRecords_Header">Vintage Year</th>
    <th class="TableRecords_Header">Owner</th>
    <th class="TableRecords_Header">Status</th>
    <th class="TableRecords_Header">Number of Credits</th>
</tr></thead>
<tbody>
<tr>
    <td class="TableRecords_OddLine">
        <div class="text-nowrap">
            <a class="underline_link"
               href="EPC_SerialRangeDetail.aspx?SerialId=22812">
                1G33-24-0000000055928008 to <br>1G33-24-0000000055937094
            </a>
        </div>
    </td>
    <td class="TableRecords_OddLine"><div align="left">2024</div></td>
    <td class="TableRecords_OddLine">
        <a class="underline_link" href="#">TransCanada PipeLines Limited</a>
        <div><div class="text-neutral-7">(TransCanada Alberta System)</div></div>
    </td>
    <td class="TableRecords_OddLine">Active<div></div></td>
    <td class="TableRecords_OddLine"><div align="right">9,087</div></td>
</tr>
<tr>
    <td class="TableRecords_EvenLine">
        <div class="text-nowrap">
            <a class="underline_link"
               href="EPC_SerialRangeDetail.aspx?SerialId=21448">
                1M23-24-0000000055401404 to <br>1M23-24-0000000055435486
            </a>
        </div>
    </td>
    <td class="TableRecords_EvenLine"><div align="left">2024</div></td>
    <td class="TableRecords_EvenLine">
        <a class="underline_link" href="#">TransCanada PipeLines Limited</a>
        <div><div class="text-neutral-7">(TransCanada Alberta System)</div></div>
    </td>
    <td class="TableRecords_EvenLine">Active<div></div></td>
    <td class="TableRecords_EvenLine"><div align="right">34,083</div></td>
</tr>
</tbody>
</table>
</div>
</form>
</body></html>
"""


@pytest.fixture
def detail_html() -> str:
    """Sample detail page HTML."""
    return DETAIL_HTML


@pytest.fixture
def detail_html_with_retirement() -> str:
    """Detail page HTML with a retirement reason populated."""
    return DETAIL_HTML_WITH_RETIREMENT


@pytest.fixture
def detail_html_no_facility() -> str:
    """Detail page HTML with no facility in parentheses."""
    return DETAIL_HTML_NO_FACILITY


@pytest.fixture
def listing_page_html() -> str:
    """Sample listing page HTML with 2 rows."""
    return LISTING_PAGE_HTML
