#!/usr/bin/env python3
"""
Extract commands from desktop-commander log file.
Parses the log to extract just the commands executed and their status.
"""

import argparse
import json
import re
from pathlib import Path


def parse_log_line(line: str) -> dict | None:
    """
    Parse a single log line from desktop-commander.

    Format: TIMESTAMP | COMMAND_TYPE | Arguments: {...}
    """
    # Pattern to match log lines
    pattern = r"^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s*\|\s*(\w+)\s*\|\s*Arguments:\s*(.+)$"

    match = re.match(pattern, line.strip())
    if not match:
        return None

    timestamp, command_type, args_json = match.groups()

    try:
        # Parse the arguments JSON
        args = json.loads(args_json)

        # Extract the actual command from different command types
        command = None
        if command_type == "start_process" and "command" in args:
            command = args["command"]
        elif command_type == "interact_with_process" and "input" in args:
            command = f"[Interactive] {args['input']}"
        elif command_type == "read_process_output":
            # Skip output reads as they're not commands
            return None

        if command:
            return {
                "timestamp": timestamp,
                "type": command_type,
                "command": command,
                "timeout_ms": args.get("timeout_ms"),
                "pid": args.get("pid"),
            }
    except json.JSONDecodeError:
        pass

    return None


def extract_commands_from_log(log_path: str, output_path: str | None = None) -> list[dict]:
    """
    Extract all commands from the desktop-commander log.

    Args:
        log_path: Path to claude_tool_call.log file
        output_path: Optional path to save extracted commands

    Returns:
        List of command dictionaries
    """
    log_file = Path(log_path).expanduser()
    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return []

    commands = []

    with open(log_file, encoding="utf-8") as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed:
                commands.append(parsed)

    # Save to output file if specified
    if output_path:
        save_commands_to_files(commands, output_path)

    return commands


def save_commands_to_files(commands: list[dict], output_path: str):
    """
    Save extracted commands to JSON format.
    """
    output_file = Path(output_path)

    # Save as JSON for programmatic access
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(commands, f, indent=2, default=str)


def print_command_summary(commands: list[dict]):
    """
    Print a summary of extracted commands.
    """
    if not commands:
        print("No commands found in log")
        return

    print("\nCommand Summary:")
    print(f"  Total Commands: {len(commands)}")

    # Group by command prefix
    command_groups: dict[str, int] = {}
    for cmd in commands:
        prefix = cmd["command"].split()[0] if cmd["command"] else "unknown"
        command_groups[prefix] = command_groups.get(prefix, 0) + 1

    print("\nCommands by type:")
    for prefix, count in sorted(command_groups.items(), key=lambda x: -x[1]):
        print(f"  {prefix}: {count}")

    # Show recent commands
    print("\nLast 5 commands:")
    for cmd in commands[-5:]:
        print(f"  {cmd['timestamp']}: {cmd['command'][:70]}...")


def main():
    """Main function to extract commands from desktop-commander log."""
    parser = argparse.ArgumentParser(description="Extract commands from desktop-commander log")
    parser.add_argument(
        "--log-path",
        default="/root/.claude-server-commander/claude_tool_call.log",
        help="Path to claude_tool_call.log file",
    )
    parser.add_argument("--output", default="command_audit.json", help="Output file for extracted commands")
    parser.add_argument("--summary", action="store_true", help="Print command summary")
    parser.add_argument("--filter", help="Filter commands by pattern (regex)")

    args = parser.parse_args()

    # Extract commands
    commands = extract_commands_from_log(args.log_path, args.output)

    # Apply filter if specified
    if args.filter:
        pattern = re.compile(args.filter)
        commands = [cmd for cmd in commands if pattern.search(cmd["command"])]

    # Print summary
    if args.summary or not args.output:
        print_command_summary(commands)

    if args.output:
        print(f"\nExtracted {len(commands)} commands")
        print(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()
