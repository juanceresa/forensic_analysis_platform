'use client';

interface ErrorStateProps {
  error: Error;
}

export function ErrorState({ error }: ErrorStateProps) {
  return (
    <div className="h-screen flex items-center justify-center bg-slate-950">
      <div className="text-center max-w-md" role="alert" aria-live="assertive">
        <h1 className="text-2xl font-display uppercase tracking-wide text-red-400 mb-2">
          Error Loading Case
        </h1>
        <p className="text-slate-300 mb-4 font-mono text-sm">{error.message}</p>
        <button
          onClick={() => window.location.reload()}
          className="min-h-[44px] px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded transition-colors font-display text-sm uppercase tracking-wider"
          aria-label="Retry loading case"
        >
          Retry
        </button>
      </div>
    </div>
  );
}
