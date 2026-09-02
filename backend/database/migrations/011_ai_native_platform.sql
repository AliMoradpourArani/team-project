CREATE TABLE ai_project_memory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  project_id TEXT,
  memory_key TEXT NOT NULL,
  memory_value TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  UNIQUE(user_id, project_id, memory_key)
);

CREATE INDEX idx_ai_project_memory_scope
  ON ai_project_memory(user_id, project_id, updated_at DESC);

CREATE TABLE ai_github_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  project_id TEXT,
  activity_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('branch', 'commit', 'pull-request', 'issue')),
  reference TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

CREATE INDEX idx_ai_github_links_activity
  ON ai_github_links(user_id, activity_id, created_at DESC);
