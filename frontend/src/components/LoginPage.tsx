import { useState } from "react";

import { login } from "../api";
import { useI18n } from "../i18n";
import type { AuthSession } from "../types";

export default function LoginPage({ onLogin }: { onLogin: (session: AuthSession) => void }) {
  const { t } = useI18n();
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
      setError(requestError instanceof Error ? requestError.message : t("login.signinError"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="login-shell">
      <div className="login-copy">
        <p className="eyebrow">{t("login.protectedWorkspace")}</p>
        <h1>
          {t("login.heroLine1")}
          <br />
          <em>{t("login.heroEm")}</em>
        </h1>
        <p className="hero-copy">{t("login.heroCopy")}</p>
      </div>
      <form className="login-card" onSubmit={submit}>
        <p className="eyebrow">{t("login.signIn")}</p>
        <h2>{t("login.welcomeBack")}</h2>
        <label>
          {t("login.username")}
          <input
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </label>
        <label>
          {t("login.password")}
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
          {submitting ? t("login.signingIn") : t("login.signIn")}
        </button>
        <small>{t("login.localAccountsNote")}</small>
      </form>
    </section>
  );
}
