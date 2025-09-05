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


def save_calendar_state(output_file: str | None = None) -> None:
    """
    Save calendar state to specified CSV file.

    Args:
        output_file: Optional output filename for calendar data
    """
    # Create context directory if it doesn't exist
    context_dir = Path("context")
    context_dir.mkdir(exist_ok=True)

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Get current date in UTC and format for gcalcli
    gcal_start = datetime.now(UTC).strftime("%Y-%m-%d")
    gcal_end = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%d")

    # Determine output file
    if output_file:
        # If specific file provided, use it with timestamp
        base_name = Path(output_file).stem
        output_path = context_dir / f"{base_name}_{timestamp}.csv"
    else:
        # Default to after_timestamp.csv
        output_path = context_dir / f"after_{timestamp}.csv"

    logger.info(
        "Starting calendar state save",
        output_file=str(output_path),
        date_range_start=gcal_start,
        date_range_end=gcal_end,
    )

    try:
        # Fetch calendar data and save to specified CSV file with all details
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

        logger.debug("gcalcli command completed successfully", stdout_length=len(result.stdout))

        # Write to output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)

        # Get file info
        file_size = output_path.stat().st_size

        # Count lines (events)
        with open(output_path, encoding="utf-8") as f:
            line_count = sum(1 for _ in f)

        event_count = line_count - 1  # Subtract header line

        logger.info(
            "Calendar state saved successfully",
            output_file=str(output_path),
            file_size_bytes=file_size,
            event_count=event_count,
        )

    except subprocess.CalledProcessError as e:
        logger.error(
            "Failed to save calendar state - gcalcli error", error=str(e), returncode=e.returncode, stderr=e.stderr
        )
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error("gcalcli command not found", error=str(e))
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error during calendar state save", error=str(e), error_type=type(e).__name__)
        sys.exit(1)


if __name__ == "__main__":
    output_filename = sys.argv[1] if len(sys.argv) > 1 else None
    save_calendar_state(output_filename)
