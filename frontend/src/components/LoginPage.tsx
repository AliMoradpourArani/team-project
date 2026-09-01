import { useState } from "react";

import { login } from "../api";
import type { AuthSession } from "../types";

export default function LoginPage({ onLogin }: { onLogin: (session: AuthSession) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const session = await login(username.trim(), password);
      onLogin(session);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not sign in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="login-shell">
      <div className="login-copy">
        <p className="eyebrow">Protected workspace</p>
        <h1>
          Team work,
          <br />
          <em>accountable.</em>
        </h1>
        <p className="hero-copy">
          Students manage only their own work. Professors get a read-only view across the team.
        </p>
      </div>
      <form className="login-card" onSubmit={submit}>
        <p className="eyebrow">Sign in</p>
        <h2>Welcome back</h2>
        <label>
          Username
          <input
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            required
          />
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        <button className="primary-button" type="submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
        <small>
          Accounts are provisioned locally by the team lead. Passwords are never stored in Git.
        </small>
      </form>
    </section>
  );
}
