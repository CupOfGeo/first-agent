#!/usr/bin/env python3
"""
Fetch court data from Travis County API and save to JSON file.
Converted from fetch_court_data.sh
"""

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)


def get_court_data(attorney_last_name: str, timestamp: str, save_files: bool = True) -> dict | None:
    """
    Fetch court data from Travis County API.

    Args:
        attorney_last_name: Last name of attorney to search for
        timestamp: Timestamp string for file naming
        save_files: Whether to save data to files

    Returns:
        Court data dict or None if failed
    """
    # Get current date in UTC and format it
    start_date = datetime.now(UTC).strftime("%Y-%m-%dT05:00:00.000Z")
    end_date = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%dT05:00:00.000Z")

    # API URL
    url = "https://publiccourts.traviscountytx.gov/DSA/api/dockets/settings"

    # Parameters
    params = {
        "criteriaId": "attorney",
        "start": start_date,
        "end": end_date,
        "courtCode": "",
        "causeNumber": "",
        "defendantLastName": "",
        "defendantFirstName": "",
        "attorneyLastName": attorney_last_name,
        "attorneyFirstName": "",
        "Mni": "",
    }

    # Headers
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Referer": "https://publiccourts.traviscountytx.gov/DSA",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        ),
        "sec-ch-ua": '"Not;A=Brand";v="99", "Brave";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }

    try:
        logger.debug("Making API request to Travis County court system", url=url, params=params)

        # Make the request
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        logger.debug("API request successful", status_code=response.status_code, content_length=len(response.content))

        # Parse response
        court_data = response.json()

        # Save to JSON file if requested
        if save_files:
            context_dir = Path("context")
            context_dir.mkdir(exist_ok=True)
            court_data_file = context_dir / f"court_data_{timestamp}.json"
            with open(court_data_file, "w", encoding="utf-8") as f:
                json.dump(court_data, f, indent=2)

            logger.info(
                "Court data saved successfully",
                output_file=str(court_data_file),
                record_count=len(court_data) if isinstance(court_data, list) else "unknown",
            )

        return court_data

    except requests.RequestException as e:
        logger.error("Error fetching court data from API", error=str(e), error_type=type(e).__name__, url=url)
        return None
    except json.JSONDecodeError as e:
        logger.error("Error parsing JSON response", error=str(e))
        return None


def get_calendar_state(timestamp: str, save_files: bool = True) -> str | None:
    """
    Fetch current calendar state using gcalcli.

    Args:
        timestamp: Timestamp string for file naming
        save_files: Whether to save data to files

    Returns:
        Calendar data string or None if failed
    """
    # Format dates for gcalcli (YYYY-MM-DD format)
    gcal_start = datetime.now(UTC).strftime("%Y-%m-%d")
    gcal_end = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        logger.debug("Executing gcalcli command to get calendar state")
        result = subprocess.run(
            ["gcalcli", "agenda", "--tsv", "--details", "all", gcal_start, gcal_end],
            capture_output=True,
            text=True,
            check=True,
        )
        calendar_data = result.stdout

        if save_files:
            context_dir = Path("context")
            context_dir.mkdir(exist_ok=True)
            before_file = context_dir / f"before_{timestamp}.csv"
            with open(before_file, "w", encoding="utf-8") as f:
                f.write(calendar_data)
            logger.debug("Saved calendar before state", filename=str(before_file))

        return calendar_data

    except subprocess.CalledProcessError as e:
        logger.error("Error running gcalcli", error=str(e), returncode=e.returncode)
        return None


def fetch_court_data(attorney_last_name: str = "Pesantes", save_files: bool = True) -> tuple:
    """
    Fetch court data and calendar state for specified attorney.

    Args:
        attorney_last_name: Last name of attorney to search for
        save_files: Whether to save data to files (default True)

    Returns:
        Tuple of (court_data, calendar_before, timestamp)
    """
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    logger.info("Starting court data and calendar fetch", attorney_last_name=attorney_last_name, timestamp=timestamp)

    # Fetch calendar state first
    calendar_before = get_calendar_state(timestamp, save_files)
    if calendar_before is None:
        return None, None, timestamp

    # Fetch court data
    court_data = get_court_data(attorney_last_name, timestamp, save_files)
    if court_data is None:
        return None, calendar_before, timestamp

    return court_data, calendar_before, timestamp


if __name__ == "__main__":
    attorney_name = sys.argv[1] if len(sys.argv) > 1 else "Pesantes"
    fetched_court_data, fetched_calendar_before, fetched_timestamp = fetch_court_data(attorney_name)
    # Print for backwards compatibility when run as script
    if fetched_court_data:
        print(json.dumps(fetched_court_data, indent=2))
