'use client';

import { Component, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error boundary caught:', error, errorInfo);
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.reset);
      }

      return (
        <div className="h-screen flex items-center justify-center bg-slate-950">
          <div className="text-center max-w-md" role="alert">
            <h1 className="text-2xl font-display uppercase tracking-wide text-red-400 mb-2">
              Application Error
            </h1>
            <p className="text-slate-300 mb-4 font-mono text-sm">
              {this.state.error.message}
            </p>
            <button
              onClick={this.reset}
              className="min-h-[44px] px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded transition-colors font-display text-sm uppercase tracking-wider"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
