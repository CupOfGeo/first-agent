"""
Court Calendar Agent
This agent manages syncing court appearances with a Google Calendar.
It fetches court data, compares it with calendar events, and updates the calendar accordingly.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from fetch_court_data import fetch_court_data, get_calendar_state
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
        # Call the fetch_court_data function directly
        court_data, calendar_before, timestamp = fetch_court_data(
            attorney_last_name=last_name or "Pesantes", save_files=True
        )

        if court_data is None:
            raise RuntimeError("Failed to fetch court data")

        print("Court data fetched successfully")

        # Find the saved files to get their names for display
        court_data_file = f"court_data_{timestamp}.json"
        before_file = f"before_{timestamp}.csv"

        return court_data, calendar_before, court_data_file, before_file

    except (FileNotFoundError, OSError, json.JSONDecodeError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)


def save_calendar_after_state():
    """Save the calendar state after agent completes its work."""
    print("Saving calendar after state...")

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Use the get_calendar_state function directly
        calendar_data = get_calendar_state(timestamp, save_files=True)

        if calendar_data is None:
            print("Error saving calendar after state")
        else:
            print("Calendar after state saved successfully")
            print(f"After state saved to: after_{timestamp}.csv")

    except (FileNotFoundError, OSError) as e:
        print(f"Error: {e}")


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

1. Use gcalcli directly to check the {calendar_name} calendar for the same time period
   Available gcalcli commands:
   - gcalcli list                         list available calendars
   - gcalcli agenda [start_date] [end_date]  get an agenda for a time period
   - gcalcli calm [month] [year]          get a month agenda in calendar format
   - gcalcli quick "event description"    quick-add an event to a calendar
   - gcalcli add                          add a detailed event to the calendar
   - gcalcli edit [event_id]              edit calendar events
   - gcalcli delete [event_id]            delete calendar events

   Use --calendar="calendar_name" to specify which calendar to work with.
   Use --tsv for tab-separated output that's easier to parse.

2. Compare the court appearances (shown above) with current calendar events:
   - Identify any missing events that need to be added
   - Identify any events that have changed (time, location, etc.)
   - Identify any events in calendar that are not in court data

3. Sync the calendar:
   - Add any missing court appearances to the calendar
   - Update any changed events
   - Each calendar entry should include: case number, defendant name, court room, charge, and appearance requirement

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
        servers=["cli"],
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
