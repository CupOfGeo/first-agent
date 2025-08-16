"""
Court Calendar Agent
This agent manages syncing court appearances with a Google Calendar.
It fetches court data, compares it with calendar events, and updates the calendar accordingly.
"""

import asyncio
import os

from dotenv import load_dotenv
from mcp_agent.core.fastagent import FastAgent

load_dotenv()
last_name = os.getenv("LAST_NAME")
calendar_name = os.getenv("CALENDAR_NAME")


# Create the application
fast = FastAgent("Agent Chaining")


instruction = f"""
You are the calendar manager responsible for syncing court appearances with Google Calendar.

Your task is to ensure the {calendar_name} calendar is in sync with court appointments.

Steps to complete:
1. Run the shell script at /workspaces/first-agent/court-cal-agent/fetch_court_data.sh with the attorney last name "{last_name}" as an argument
   - This script automatically uses today as start date and one month from today as end date
   - Example: /workspaces/first-agent/court-cal-agent/fetch_court_data.sh "{last_name}"

2. Parse the JSON response to extract all court appearances with:
   - Defendant name
   - Cause number
   - Date and time
   - Court room
   - Charge
   - Appearance requirement (Must/May/No)
   - Type description

3. Use gcalcli to check the {calendar_name} calendar for the same time period
   Available gcalcli commands:
   - list                list available calendars
   - agenda              get an agenda for a time period
   - calm                get a month agenda in calendar format
   - quick               quick-add an event to a calendar
   - add                 add a detailed event to the calendar
   - edit                edit calendar events
   - delete              delete calendar events

4. Compare court appearances with calendar events:
   - Identify any missing events that need to be added
   - Identify any events that have changed (time, location, etc.)
   - Identify any events in calendar that are not in court data

5. Sync the calendar:
   - Add any missing court appearances to the calendar
   - Update any changed events
   - Each calendar entry should include: case number, defendant name, court room, charge, and appearance requirement

The calendar should exactly reflect all court appointments returned by the API for the requested time period.
"""


@fast.agent(
    "cal_manager",
    instruction=instruction,
    servers=["fetch", "cli"],
    model="sonnet",
)
async def main() -> None:
    async with fast.run() as agent:
        await agent.cal_manager.send("hello can you do your task please?")


if __name__ == "__main__":
    asyncio.run(main())
