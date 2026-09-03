CREATE TABLE github_connections (
  user_id TEXT PRIMARY KEY,
  github_username TEXT NOT NULL,
  personal_token TEXT,
  can_push INTEGER NOT NULL DEFAULT 0,
  synced_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);