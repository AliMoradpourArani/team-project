CREATE TABLE submission_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    is_open INTEGER NOT NULL DEFAULT 1 CHECK (is_open IN (0, 1)),
    deadline_at TEXT,
    updated_by_account_id INTEGER REFERENCES auth_accounts(id) ON DELETE RESTRICT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO submission_settings (id, is_open) VALUES (1, 1);

CREATE TABLE project_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    submitted_by_account_id INTEGER NOT NULL REFERENCES auth_accounts(id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK (version > 0),
    snapshot_digest TEXT NOT NULL CHECK (length(snapshot_digest) = 64),
    source_file_count INTEGER NOT NULL CHECK (source_file_count >= 0),
    source_total_bytes INTEGER NOT NULL CHECK (source_total_bytes >= 0),
    review_status TEXT CHECK (review_status IS NULL OR review_status IN ('in-review', 'changes-requested', 'approved')),
    review_total_score INTEGER CHECK (review_total_score IS NULL OR (review_total_score >= 0 AND review_total_score <= 100)),
    snapshot_json TEXT NOT NULL,
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, version)
);

CREATE INDEX idx_project_submissions_project ON project_submissions(project_id, version DESC);
CREATE INDEX idx_project_submissions_user ON project_submissions(user_id, submitted_at DESC);

CREATE TABLE submission_releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE CHECK (length(label) BETWEEN 1 AND 120),
    manifest_digest TEXT NOT NULL CHECK (length(manifest_digest) = 64),
    manifest_json TEXT NOT NULL,
    project_count INTEGER NOT NULL CHECK (project_count > 0),
    created_by_account_id INTEGER NOT NULL REFERENCES auth_accounts(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
