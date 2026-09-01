import type { ProjectPreview } from "../types";
import "../project-demo.css";

const STATIC_PREVIEW_CSP =
  "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src 'none'; connect-src 'none'; img-src data:; media-src 'none'; font-src data:; style-src 'unsafe-inline'; frame-src 'none'; form-action 'none'; base-uri 'none';\">";

export default function ProjectDemoPreview({ preview }: { preview: ProjectPreview }) {
  if (preview.kind === "static-html") {
    return (
      <section className="dashboard-card project-demo-card">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">Safe preview</p>
            <h2>Static web demo</h2>
          </div>
          {preview.truncated ? <span>truncated</span> : null}
        </div>
        <p className="project-demo-summary">{preview.summary}</p>
        <iframe
          className="project-static-preview"
          title="Sandboxed static project preview"
          sandbox=""
          referrerPolicy="no-referrer"
          srcDoc={`${STATIC_PREVIEW_CSP}${preview.content}`}
        />
      </section>
    );
  }

  return (
    <section className="dashboard-card project-demo-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Safe preview</p>
          <h2>OpenAPI contract</h2>
        </div>
      </div>
      <p className="project-demo-summary">{preview.summary}</p>
      <pre className="project-openapi-preview">{preview.content}</pre>
    </section>
  );
}
