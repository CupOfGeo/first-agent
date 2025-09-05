"""
Court Calendar Agent
This agent manages syncing court appearances with a Google Calendar.
It fetches court data, compares it with calendar events, and updates the calendar accordingly.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp_agent.core.fastagent import FastAgent

load_dotenv()
last_name = os.getenv("LAST_NAME")
calendar_name = os.getenv("CALENDAR_NAME")


# Create the application
fast = FastAgent("Agent Chaining")


def fetch_court_data_and_calendar():
    """Fetch court data and current calendar state before starting the agent."""
    print("Fetching court data and current calendar state...")

    try:
        # Run fetch_court_data.py script
        subprocess.run(
            [sys.executable, "scripts/fetch_court_data.py", last_name or "Pesantes"],
            cwd="/workspaces/first-agent/court-cal-agent",
            capture_output=True,
            text=True,
            check=True,
        )
        print("✓ Court data fetched successfully")

        # Find the most recent context files
        context_dir = Path("/workspaces/first-agent/court-cal-agent/context")

        # Get most recent files
        court_data_files = list(context_dir.glob("court_data_*.json"))
        before_files = list(context_dir.glob("before_*.csv"))

        if not court_data_files or not before_files:
            raise FileNotFoundError("Could not find recent context files")

        # Get the most recent files
        latest_court_data = max(court_data_files, key=lambda f: f.stat().st_mtime)
        latest_before = max(before_files, key=lambda f: f.stat().st_mtime)

        # Load court data
        with open(latest_court_data, encoding="utf-8") as f:
            court_data = json.load(f)

        # Load calendar before state
        with open(latest_before, encoding="utf-8") as f:
            calendar_before = f.read()

        return court_data, calendar_before, latest_court_data.name, latest_before.name

    except subprocess.CalledProcessError as e:
        print(f"✗ Error fetching court data: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def save_calendar_after_state():
    """Save the calendar state after agent completes its work."""
    print("\nSaving calendar after state...")

    try:
        subprocess.run(
            [sys.executable, "scripts/save_calendar_state.py"],
            cwd="/workspaces/first-agent/court-cal-agent",
            capture_output=True,
            text=True,
            check=True,
        )
        print("✓ Calendar after state saved successfully")

        # Find the most recent after file and show summary
        context_dir = Path("/workspaces/first-agent/court-cal-agent/context")
        after_files = list(context_dir.glob("after_*.csv"))
        if after_files:
            latest_after = max(after_files, key=lambda f: f.stat().st_mtime)
            print(f"✓ After state saved to: {latest_after.name}")

    except subprocess.CalledProcessError as e:
        print(f"✗ Error saving calendar after state: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
    except (FileNotFoundError, OSError) as e:
        print(f"✗ Error: {e}")


def build_instruction_with_context(court_data, calendar_before, court_file, before_file):
    """Build agent instruction with the fetched context data."""

    # Format court data for display
    court_summary = []
    for item in court_data:
        defendant = item.get("defendant", {})
        summary = {
            "case": item.get("cause", ""),
            "defendant": defendant.get("fullName", ""),
            "datetime": item.get("timestampString", ""),
            "court": item.get("court", ""),
            "charge": item.get("charge", ""),
            "appear": item.get("appear", {}).get("message", ""),
            "type": item.get("typeDesc", "").strip() if item.get("typeDesc") else "",
        }
        court_summary.append(summary)

    instruction = f"""
You are the calendar manager responsible for syncing court appearances with Google Calendar.

Your task is to ensure the {calendar_name} calendar is in sync with court appointments.

CONTEXT DATA ALREADY FETCHED:
====================

Court Data (from {court_file}):
{json.dumps(court_summary, indent=2)}

Current Calendar State (from {before_file}):
{calendar_before[:1000]}{"..." if len(calendar_before) > 1000 else ""}

TASKS TO COMPLETE:
==================

1. Use the audited gcalcli wrapper to check the {calendar_name} calendar for the same time period
   Use: python3 /workspaces/first-agent/court-cal-agent/gcalcli_wrapper.py [gcalcli_args]
   Available gcalcli commands:
   - list                list available calendars
   - agenda              get an agenda for a time period
   - calm                get a month agenda in calendar format
   - quick               quick-add an event to a calendar
   - add                 add a detailed event to the calendar
   - edit                edit calendar events
   - delete              delete calendar events

   All calendar operations are automatically logged to SQLite audit database.

2. Compare the court appearances (shown above) with current calendar events:
   - Identify any missing events that need to be added
   - Identify any events that have changed (time, location, etc.)
   - Identify any events in calendar that are not in court data

3. Sync the calendar:
   - Add any missing court appearances to the calendar
   - Update any changed events
   - Each calendar entry should include: case number, defendant name, court room, charge, and appearance requirement

4. Save the updated calendar state:
   - After making all changes, run: python3 /workspaces/first-agent/court-cal-agent/scripts/save_calendar_state.py
   - This will save the current calendar state with a timestamp for audit purposes
   - IMPORTANT: You MUST run this script at the end to capture the final state

The calendar should exactly reflect all {len(court_data)} court appointments shown in the context data above.

REMINDER: Always end by running the save_calendar_state.py script to create the "after" snapshot.
"""

    return instruction


async def main() -> None:
    """Main function to run the calendar manager agent."""
    # First, fetch the court data and calendar state
    court_data, calendar_before, court_file, before_file = fetch_court_data_and_calendar()

    # Build instruction with the context
    instruction = build_instruction_with_context(court_data, calendar_before, court_file, before_file)

    # Create agent with the context-rich instruction
    @fast.agent(
        "cal_manager",
        instruction=instruction,
        servers=["fetch", "cli"],
        model="sonnet",
    )
    async def cal_manager_agent():
        pass

    # Run the agent
    async with fast.run() as agent:
        await agent.cal_manager.send(
            "Please analyze the court data and calendar state provided in your instructions, "
            "then sync the calendar as needed."
        )

    # Save the calendar after state
    save_calendar_after_state()


if __name__ == "__main__":
    asyncio.run(main())
