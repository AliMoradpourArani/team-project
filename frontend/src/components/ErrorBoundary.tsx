import { Component, type ErrorInfo, type ReactNode } from "react";

import { I18nContext } from "../i18n";

interface Props {
  children: ReactNode;
}

interface State {
  failed: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static contextType = I18nContext;
  declare context: React.ContextType<typeof I18nContext>;

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled frontend render error", error, info.componentStack);
  }

  render() {
    if (this.state.failed) {
      const { t } = this.context;
      return (
        <div className="empty-state" role="alert">
          <p className="eyebrow">{t("error.unexpected")}</p>
          <h1>{t("error.somethingWrong")}</h1>
          <p>{t("error.description")}</p>
          <button className="primary-button" type="button" onClick={() => window.location.reload()}>
            {t("error.reload")}
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
