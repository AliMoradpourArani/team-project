CREATE TABLE project_reviews (
    project_id TEXT PRIMARY KEY,
    reviewer_account_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('in-review', 'changes-requested', 'approved')),
    functionality_score INTEGER NOT NULL CHECK (functionality_score BETWEEN 0 AND 30),
    code_quality_score INTEGER NOT NULL CHECK (code_quality_score BETWEEN 0 AND 20),
    documentation_score INTEGER NOT NULL CHECK (documentation_score BETWEEN 0 AND 15),
    integration_score INTEGER NOT NULL CHECK (integration_score BETWEEN 0 AND 20),
    contribution_score INTEGER NOT NULL CHECK (contribution_score BETWEEN 0 AND 15),
    feedback TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_account_id) REFERENCES auth_accounts(id) ON DELETE RESTRICT
);

CREATE INDEX idx_project_reviews_status_updated_at
    ON project_reviews(status, updated_at DESC);
