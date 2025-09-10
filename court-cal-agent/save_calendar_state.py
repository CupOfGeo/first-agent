#!/usr/bin/env python3
"""
Save calendar state to CSV file using gcalcli.
Converted from save_calendar_state.sh
"""

import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)


def save_calendar_state(state_type: str = "after", save_file: bool = True) -> tuple:
    """
    Get calendar state and optionally save to CSV file.

    Args:
        state_type: Type of state being saved ("before" or "after")
        save_file: Whether to save to file (default True)

    Returns:
        Tuple of (calendar_data, timestamp)
    """
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Get current date in UTC and format for gcalcli
    gcal_start = datetime.now(UTC).strftime("%Y-%m-%d")
    gcal_end = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%d")

    logger.info(
        "Getting calendar state",
        state_type=state_type,
        date_range_start=gcal_start,
        date_range_end=gcal_end,
    )

    try:
        # Fetch calendar data
        logger.debug(
            "Executing gcalcli command",
            command=["gcalcli", "agenda", "--tsv", "--details", "all", gcal_start, gcal_end],
        )

        result = subprocess.run(
            ["gcalcli", "agenda", "--tsv", "--details", "all", gcal_start, gcal_end],
            capture_output=True,
            text=True,
            check=True,
        )

        calendar_data = result.stdout
        logger.debug("gcalcli command completed successfully", stdout_length=len(calendar_data))

        # Save to file if requested
        if save_file:
            context_dir = Path("context")
            context_dir.mkdir(exist_ok=True)
            output_path = context_dir / f"{state_type}_{timestamp}.csv"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(calendar_data)

            # Count lines (events)
            line_count = len(calendar_data.strip().split("\n"))
            event_count = line_count - 1 if line_count > 0 else 0

            logger.info(
                "Calendar state saved successfully",
                output_file=str(output_path),
                event_count=event_count,
            )

        return calendar_data, timestamp

    except subprocess.CalledProcessError as e:
        logger.error(
            "Failed to get calendar state - gcalcli error", error=str(e), returncode=e.returncode, stderr=e.stderr
        )
        return None, timestamp
    except FileNotFoundError as e:
        logger.error("gcalcli command not found", error=str(e))
        return None, timestamp
    except OSError as e:
        logger.error("File system error during calendar state retrieval", error=str(e))
        return None, timestamp


if __name__ == "__main__":
    output_filename = sys.argv[1] if len(sys.argv) > 1 else None
    save_calendar_state(output_filename or "after")
