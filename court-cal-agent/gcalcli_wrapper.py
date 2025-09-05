#!/usr/bin/env python3
"""
Gcalcli wrapper with audit logging to SQLite database.
This script wraps gcalcli commands and logs all operations for audit purposes.
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path


class GcalcliAuditor:
    """Handles audit logging for gcalcli operations."""

    def __init__(self, db_path: str = "calendar_audit.db", session_id: str | None = None):
        """
        Initialize the auditor.

        Args:
            db_path: Path to SQLite database file
            session_id: Optional session ID for grouping operations
        """
        self.db_path = Path(db_path)
        self.session_id = session_id or str(uuid.uuid4())
        self._init_database()

    def _init_database(self):
        """Initialize the database with audit table."""
        # Run migration if database doesn't exist
        if not self.db_path.exists():
            self._run_migration()

    def _run_migration(self):
        """Run database migration to create audit table."""
        migration_file = Path(__file__).parent / "migrations" / "001_create_audit_table.sql"

        if migration_file.exists():
            with open(migration_file, encoding="utf-8") as f:
                migration_sql = f.read()

            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(migration_sql)
                print(f"Database initialized: {self.db_path}")
        else:
            # Fallback: create table inline
            self._create_audit_table_fallback()

    def _create_audit_table_fallback(self):
        """Fallback method to create audit table if migration file not found."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS calendar_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    operation VARCHAR(10) NOT NULL,
                    command TEXT NOT NULL,
                    calendar_name TEXT,
                    event_title TEXT,
                    event_date TEXT,
                    event_id TEXT,
                    case_number TEXT,
                    defendant_name TEXT,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    output TEXT,
                    session_id TEXT,
                    metadata JSON
                )
            """)

    def _parse_gcalcli_command(self, args: list[str]) -> dict:
        """
        Parse gcalcli command to extract operation details.

        Args:
            args: List of command arguments

        Returns:
            Dictionary with parsed command details
        """
        details = {
            "operation": "unknown",
            "calendar_name": None,
            "event_title": None,
            "event_date": None,
            "case_number": None,
            "defendant_name": None,
        }

        # Convert args to string for easier parsing
        cmd_str = " ".join(args)

        # Determine operation
        if "add" in args or "quick" in args:
            details["operation"] = "add"
        elif "edit" in args:
            details["operation"] = "edit"
        elif "delete" in args:
            details["operation"] = "delete"
        elif "agenda" in args or "list" in args:
            details["operation"] = "read"

        # Extract calendar name
        calendar_match = re.search(r'--calendar\s+"([^"]+)"', cmd_str)
        if calendar_match:
            details["calendar_name"] = calendar_match.group(1)

        # Extract event title
        title_match = re.search(r'--title\s+"([^"]+)"', cmd_str)
        if title_match:
            details["event_title"] = title_match.group(1)
        elif "quick" in args:
            # For quick add, the title is usually the last quoted argument
            quick_match = re.search(r'quick\s+"([^"]+)"', cmd_str)
            if quick_match:
                details["event_title"] = quick_match.group(1)

        # Extract case number from title
        if details["event_title"]:
            case_match = re.search(r"([A-Z]-\d+-[A-Z]+-\d+-\d+)", details["event_title"])
            if case_match:
                details["case_number"] = case_match.group(1)

            # Extract defendant name (usually after "Court:" and before "-")
            defendant_match = re.search(r"Court:\s*([^-]+)", details["event_title"])
            if defendant_match:
                details["defendant_name"] = defendant_match.group(1).strip()

        # Extract date/time
        when_match = re.search(r'--when\s+"([^"]+)"', cmd_str)
        if when_match:
            details["event_date"] = when_match.group(1)

        return details

    def log_command(
        self, args: list[str], success: bool, output: str, error: str | None = None, event_id: str | None = None
    ):
        """
        Log a gcalcli command execution to the audit database.

        Args:
            args: Command arguments
            success: Whether the command succeeded
            output: Command output
            error: Error message if command failed
            event_id: Calendar event ID if available
        """
        # Parse command details
        details = self._parse_gcalcli_command(args)

        # Prepare audit record
        record = {
            "timestamp": datetime.now().isoformat(),
            "operation": details["operation"],
            "command": " ".join(args),
            "calendar_name": details["calendar_name"],
            "event_title": details["event_title"],
            "event_date": details["event_date"],
            "event_id": event_id,
            "case_number": details["case_number"],
            "defendant_name": details["defendant_name"],
            "success": success,
            "error_message": error,
            "output": output,
            "session_id": self.session_id,
            "metadata": json.dumps({"args": args}),
        }

        # Insert into database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO calendar_audit (
                    timestamp, operation, command, calendar_name, event_title,
                    event_date, event_id, case_number, defendant_name, success,
                    error_message, output, session_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record["timestamp"],
                    record["operation"],
                    record["command"],
                    record["calendar_name"],
                    record["event_title"],
                    record["event_date"],
                    record["event_id"],
                    record["case_number"],
                    record["defendant_name"],
                    record["success"],
                    record["error_message"],
                    record["output"],
                    record["session_id"],
                    record["metadata"],
                ),
            )


def execute_gcalcli_with_audit(args: list[str], auditor: GcalcliAuditor) -> tuple[bool, str, str | None]:
    """
    Execute gcalcli command and log to audit database.

    Args:
        args: gcalcli command arguments
        auditor: GcalcliAuditor instance

    Returns:
        Tuple of (success, output, error)
    """
    try:
        # Execute the gcalcli command
        result = subprocess.run(["gcalcli"] + args, capture_output=True, text=True, timeout=30, check=False)

        success = result.returncode == 0
        output = result.stdout
        error = result.stderr if not success else None

        # Extract event ID from output if available
        event_id = None
        if success and ("Event created" in output or "Event added" in output):
            # Try to extract event ID from gcalcli output
            id_match = re.search(r"Event\s+(?:created|added):\s*(\S+)", output)
            if id_match:
                event_id = id_match.group(1)

        # Log to audit database
        auditor.log_command(args, success, output, error, event_id)

        return success, output, error

    except subprocess.TimeoutExpired:
        error = "Command timed out"
        auditor.log_command(args, False, "", error)
        return False, "", error
    except Exception as e:
        error = f"Execution error: {str(e)}"
        auditor.log_command(args, False, "", error)
        return False, "", error


def main():
    """Main entry point for gcalcli wrapper."""
    parser = argparse.ArgumentParser(description="Gcalcli wrapper with audit logging")
    parser.add_argument("--db-path", default="calendar_audit.db", help="SQLite database path")
    parser.add_argument("--session-id", help="Session ID for grouping operations")
    parser.add_argument("--quiet", action="store_true", help="Suppress wrapper output")
    parser.add_argument("gcalcli_args", nargs=argparse.REMAINDER, help="Arguments to pass to gcalcli")

    args = parser.parse_args()

    # Remove the first '--' if present (from argparse)
    if args.gcalcli_args and args.gcalcli_args[0] == "--":
        args.gcalcli_args = args.gcalcli_args[1:]

    if not args.gcalcli_args:
        print("Error: No gcalcli arguments provided", file=sys.stderr)
        sys.exit(1)

    # Initialize auditor
    auditor = GcalcliAuditor(args.db_path, args.session_id)

    # Execute command with audit
    success, output, error = execute_gcalcli_with_audit(args.gcalcli_args, auditor)

    # Print output (gcalcli's normal behavior)
    if output:
        print(output, end="")
    if error and not args.quiet:
        print(error, file=sys.stderr)

    if not args.quiet:
        print(f"[AUDIT] Logged to {args.db_path}", file=sys.stderr)

    # Exit with same code as gcalcli
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
