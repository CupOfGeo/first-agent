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


def fetch_court_data(attorney_last_name: str = "Pesantes") -> None:
    """
    Fetch court data for specified attorney.

    Args:
        attorney_last_name: Last name of attorney to search for
    """
    # Create context directory if it doesn't exist
    context_dir = Path("context")
    context_dir.mkdir(exist_ok=True)

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Get current date in UTC and format it
    start_date = datetime.now(UTC).strftime("%Y-%m-%dT05:00:00.000Z")

    # Calculate end date (1 month from now)
    end_date = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%dT05:00:00.000Z")

    # Format dates for gcalcli (YYYY-MM-DD format)
    gcal_start = datetime.now(UTC).strftime("%Y-%m-%d")
    gcal_end = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%d")

    logger.info(
        "Starting court data fetch",
        attorney_last_name=attorney_last_name,
        start_date=start_date,
        end_date=end_date,
        gcal_start=gcal_start,
        gcal_end=gcal_end,
    )

    # Fetch calendar data and save to CSV with all details
    try:
        logger.debug("Executing gcalcli command to save before state")
        result = subprocess.run(
            ["gcalcli", "agenda", "--tsv", "--details", "all", gcal_start, gcal_end],
            capture_output=True,
            text=True,
            check=True,
        )

        before_file = context_dir / f"before_{timestamp}.csv"
        with open(before_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        logger.debug("Saved calendar before state", filename=str(before_file))
    except subprocess.CalledProcessError as e:
        logger.error("Error running gcalcli", error=str(e), returncode=e.returncode)
        return

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

        # Save to JSON file
        response_data = response.json()
        court_data_file = context_dir / f"court_data_{timestamp}.json"
        with open(court_data_file, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2)

        logger.info(
            "Court data saved successfully",
            output_file=str(court_data_file),
            record_count=len(response_data) if isinstance(response_data, list) else "unknown",
        )

        # Also output to stdout for backwards compatibility
        logger.debug("Outputting court data to stdout for compatibility")
        print(json.dumps(response_data, indent=2))

    except requests.RequestException as e:
        logger.error("Error fetching court data from API", error=str(e), error_type=type(e).__name__, url=url)
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error("Error parsing JSON response", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    attorney_name = sys.argv[1] if len(sys.argv) > 1 else "Pesantes"
    fetch_court_data(attorney_name)
