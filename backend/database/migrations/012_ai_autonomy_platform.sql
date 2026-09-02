CREATE TABLE ai_repo_chunks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  project_id TEXT,
  path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  UNIQUE(user_id, project_id, path, chunk_index)
);

CREATE INDEX idx_ai_repo_chunks_scope
  ON ai_repo_chunks(user_id, project_id, path, chunk_index);

CREATE TABLE ai_agent_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  project_id TEXT,
  action_kind TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'executed', 'rejected', 'blocked', 'failed')),
  result_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  approved_at TEXT,
  executed_at TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_ai_agent_actions_scope
  ON ai_agent_actions(user_id, project_id, created_at DESC);

CREATE TABLE ai_memory_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  project_id TEXT,
  event_type TEXT NOT NULL,
  content TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'agent',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_ai_memory_events_scope
  ON ai_memory_events(user_id, project_id, created_at DESC);

CREATE TABLE ai_notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  project_id TEXT,
  fingerprint TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
  title TEXT NOT NULL,
  detail TEXT NOT NULL,
  read_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  UNIQUE(user_id, project_id, fingerprint)
);

CREATE INDEX idx_ai_notifications_scope
  ON ai_notifications(user_id, project_id, read_at, created_at DESC);

CREATE TABLE ai_health_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  project_id TEXT,
  overall_score INTEGER NOT NULL,
  delivery_score INTEGER NOT NULL,
  code_score INTEGER NOT NULL,
  security_score INTEGER NOT NULL,
  test_score INTEGER NOT NULL,
  schedule_score INTEGER NOT NULL,
  documentation_score INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_ai_health_snapshots_scope
  ON ai_health_snapshots(user_id, project_id, created_at DESC);
