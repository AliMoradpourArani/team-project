import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  failed: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled frontend render error", error, info.componentStack);
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="empty-state" role="alert">
          <p className="eyebrow">Unexpected error</p>
          <h1>Something went wrong</h1>
          <p>The page hit an unexpected rendering error. Reload to try again.</p>
          <button className="primary-button" type="button" onClick={() => window.location.reload()}>
            Reload application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
