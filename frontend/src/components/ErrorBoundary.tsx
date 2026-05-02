import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode };

type State = { hasError: boolean; message?: string };

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("UI error boundary:", error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "2rem", maxWidth: 560 }}>
          <h1 style={{ marginTop: 0 }}>Something broke in the UI</h1>
          <p style={{ opacity: 0.85 }}>{this.state.message ?? "Unknown error."}</p>
          <p className="mono" style={{ opacity: 0.6, fontSize: 13 }}>
            Try refreshing the page. If this persists, check the browser console for details.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
