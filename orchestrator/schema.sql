-- FDE Job Orchestrator Schema
-- SQLite database for tracking jobs

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    job_type TEXT NOT NULL,  -- 'cron', 'event', 'manual'
    status TEXT NOT NULL,    -- 'pending', 'running', 'success', 'failed', 'retrying'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    log_output TEXT,
    metadata TEXT  -- JSON string
);

CREATE TABLE IF NOT EXISTS job_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    command TEXT NOT NULL,
    schedule TEXT,  -- Cron expression or 'event-driven'
    working_dir TEXT,
    max_retries INTEGER DEFAULT 3,
    notify_on TEXT DEFAULT 'failure',  -- 'always', 'failure', 'success', 'never'
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    channel TEXT,  -- 'telegram', 'slack', 'email'
    message TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_started ON jobs(started_at);
CREATE INDEX IF NOT EXISTS idx_jobs_name ON jobs(job_name);
