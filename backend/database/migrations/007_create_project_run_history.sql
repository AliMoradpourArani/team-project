CREATE TABLE project_run_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    runner TEXT NOT NULL,
    exit_code INTEGER,
    timed_out INTEGER NOT NULL CHECK (timed_out IN (0, 1)),
    duration_ms INTEGER NOT NULL CHECK (duration_ms >= 0),
    stdout_preview TEXT NOT NULL DEFAULT '',
    stderr_preview TEXT NOT NULL DEFAULT '',
    output_truncated INTEGER NOT NULL CHECK (output_truncated IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_project_run_history_project_id_created_at
    ON project_run_history(project_id, created_at DESC);
