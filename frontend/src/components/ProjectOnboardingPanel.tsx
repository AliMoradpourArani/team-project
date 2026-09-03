import { useEffect, useState } from "react";

import { getProjectOnboarding } from "../api";
import { useI18n } from "../i18n";
import "../onboarding.css";
import type { AuthRole, ProjectOnboarding } from "../types";
import StatusMessage from "./StatusMessage";

interface Props {
  projectId: string;
  role: AuthRole;
}

export default function ProjectOnboardingPanel({ projectId, role }: Props) {
  const { t } = useI18n();
  const [onboarding, setOnboarding] = useState<ProjectOnboarding | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setOnboarding(null);
    setError("");
    getProjectOnboarding(projectId)
      .then(setOnboarding)
      .catch((requestError: Error) => setError(requestError.message));
  }, [projectId]);

  if (error) return <StatusMessage error>{error}</StatusMessage>;
  if (!onboarding) return <StatusMessage>{t("on.loading")}</StatusMessage>;

  return (
    <section className="dashboard-card onboarding-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">{t("on.eyebrow")}</p>
          <h2>{t("on.title")}</h2>
        </div>
        <span className={`onboarding-status ${onboarding.status}`}>{onboarding.status}</span>
      </div>

      <div className="onboarding-summary">
        <strong>
          {t("on.gatesComplete", {
            done: onboarding.completedGates,
            total: onboarding.totalGates,
          })}
        </strong>
        <span>{onboarding.readyForSubmission ? t("on.ready") : t("on.blocked")}</span>
      </div>

      <div className="onboarding-paths">
        <div>
          <span>{t("on.trackedMetadata")}</span>
          <code>{onboarding.expectedMetadataPath}</code>
        </div>
        <div>
          <span>{t("on.projectSource")}</span>
          <code>{onboarding.expectedRepositoryPath}</code>
        </div>
      </div>

      <div className="onboarding-gates">
        {onboarding.gates.map((gate) => (
          <article
            className={`onboarding-gate ${gate.passed ? "passed" : "blocked"}`}
            key={gate.key}
          >
            <span className="onboarding-gate-mark">{gate.passed ? "✓" : "×"}</span>
            <div>
              <strong>{gate.label}</strong>
              <p>{gate.detail}</p>
              {!gate.passed ? <small>{gate.remediation}</small> : null}
            </div>
          </article>
        ))}
      </div>

      <div className="onboarding-next">
        <span>{role === "professor" ? t("on.readonlyReadiness") : t("on.nextAction")}</span>
        <p>{onboarding.nextAction}</p>
        <code>{onboarding.localCheckCommand}</code>
      </div>

      <details className="onboarding-contracts">
        <summary>{t("on.contracts")}</summary>
        <div>
          {onboarding.supportedContracts.map((contract) => (
            <article key={contract.runner}>
              <strong>{contract.projectType}</strong>
              <span>{contract.runner}</span>
              <small>
                {contract.demoMode} · {t("on.entryExample")} {contract.entryPointExample}
              </small>
            </article>
          ))}
        </div>
      </details>
    </section>
  );
}
