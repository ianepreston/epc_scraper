"""Orchestrate listing and detail scraping with concurrency control."""

import asyncio
import logging

import httpx

from epc_scraper.detail import scrape_detail
from epc_scraper.listing import scrape_listing
from epc_scraper.models import EPCCredit

logger = logging.getLogger(__name__)


async def scrape_all(
    concurrency: int = 10,
    delay: float = 0.5,
) -> list[EPCCredit]:
    """Scrape all EPC credits from the registry.

    First collects all serial IDs from the paginated listing, then
    fetches each detail page concurrently with a semaphore to limit
    parallel requests.

    Args:
        concurrency: Maximum number of concurrent detail page requests.
        delay: Seconds to wait between listing page requests and
            between batches of detail requests.

    Returns:
        List of all EPCCredit records scraped from the registry.
    """
    logger.info("Starting listing scrape")
    serial_ids: list[int] = []
    async for record in scrape_listing(delay=delay):
        serial_ids.append(record.serial_id)
    logger.info(f"Collected {len(serial_ids)} serial IDs from listing")

    semaphore = asyncio.Semaphore(concurrency)
    credits: list[EPCCredit] = []
    errors: list[tuple[int, Exception]] = []

    async def _fetch_one(client: httpx.AsyncClient, sid: int) -> None:
        async with semaphore:
            try:
                credit = await scrape_detail(client, sid)
                credits.append(credit)
            except (httpx.HTTPStatusError, ValueError) as exc:
                logger.error(f"Failed to scrape SerialId={sid}: {exc}")
                errors.append((sid, exc))
            await asyncio.sleep(delay)

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        tasks = [_fetch_one(client, sid) for sid in serial_ids]
        await asyncio.gather(*tasks)

    if errors:
        logger.warning(
            f"Completed with {len(errors)} errors out of {len(serial_ids)} detail pages"
        )

    logger.info(f"Successfully scraped {len(credits)} credits")
    return credits


def scrape_all_sync(
    concurrency: int = 10,
    delay: float = 0.5,
) -> list[EPCCredit]:
    """Synchronous wrapper around scrape_all.

    Args:
        concurrency: Maximum number of concurrent detail page requests.
        delay: Seconds to wait between requests.

    Returns:
        List of all EPCCredit records scraped from the registry.
    """
    return asyncio.run(scrape_all(concurrency=concurrency, delay=delay))
