import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/** Catches rendering errors in the results section so a bad/unexpected
 * API response (e.g. an unexpected null somewhere) shows a readable
 * message instead of taking down the whole page with a blank screen. */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error("Results rendering crashed:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          role="alert"
          className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
        >
          <p className="font-semibold">Something went wrong displaying these results.</p>
          <p className="mt-1 text-red-700 dark:text-red-300">
            This is usually caused by an unusual data point in the response. Try a different ticker
            or date range.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
