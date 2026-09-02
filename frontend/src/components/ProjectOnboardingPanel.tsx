import { useEffect, useState } from "react";

import { getProjectOnboarding } from "../api";
import "../onboarding.css";
import type { AuthRole, ProjectOnboarding } from "../types";
import StatusMessage from "./StatusMessage";

interface Props {
  projectId: string;
  role: AuthRole;
}

export default function ProjectOnboardingPanel({ projectId, role }: Props) {
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
  if (!onboarding) return <StatusMessage>Loading onboarding gates…</StatusMessage>;

  return (
    <section className="dashboard-card onboarding-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Phase 10 onboarding</p>
          <h2>Member project integration gates</h2>
        </div>
        <span className={`onboarding-status ${onboarding.status}`}>{onboarding.status}</span>
      </div>

      <div className="onboarding-summary">
        <strong>
          {onboarding.completedGates}/{onboarding.totalGates} blocking gates complete
        </strong>
        <span>
          {onboarding.readyForSubmission
            ? "Integration-ready for the Phase 9 submission flow."
            : "Submission stays blocked until every integration gate passes."}
        </span>
      </div>

      <div className="onboarding-paths">
        <div>
          <span>Tracked metadata</span>
          <code>{onboarding.expectedMetadataPath}</code>
        </div>
        <div>
          <span>Project source</span>
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
        <span>{role === "professor" ? "Read-only readiness" : "Next action"}</span>
        <p>{onboarding.nextAction}</p>
        <code>{onboarding.localCheckCommand}</code>
      </div>

      <details className="onboarding-contracts">
        <summary>Supported typed project contracts</summary>
        <div>
          {onboarding.supportedContracts.map((contract) => (
            <article key={contract.runner}>
              <strong>{contract.projectType}</strong>
              <span>{contract.runner}</span>
              <small>
                {contract.demoMode} · example entry point: {contract.entryPointExample}
              </small>
            </article>
          ))}
        </div>
      </details>
    </section>
  );
}
