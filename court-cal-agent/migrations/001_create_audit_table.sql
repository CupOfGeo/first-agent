-- Migration: Create calendar audit table
-- This table tracks all calendar operations (add, edit, delete) for audit purposes

CREATE TABLE IF NOT EXISTS calendar_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    operation VARCHAR(10) NOT NULL, -- 'add', 'edit', 'delete'
    command TEXT NOT NULL,           -- Full gcalcli command executed
    calendar_name TEXT,              -- Calendar being modified
    event_title TEXT,                -- Event title if available
    event_date TEXT,                 -- Event date/time if available
    event_id TEXT,                   -- Calendar event ID if available
    case_number TEXT,                -- Court case number if available
    defendant_name TEXT,             -- Defendant name if available
    success BOOLEAN DEFAULT 1,       -- Whether command succeeded
    error_message TEXT,              -- Error message if failed
    output TEXT,                     -- Command output
    session_id TEXT,                 -- Session identifier for grouping related operations
    metadata JSON                    -- Additional metadata as JSON
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON calendar_audit(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_operation ON calendar_audit(operation);
CREATE INDEX IF NOT EXISTS idx_audit_case_number ON calendar_audit(case_number);
CREATE INDEX IF NOT EXISTS idx_audit_session ON calendar_audit(session_id);
