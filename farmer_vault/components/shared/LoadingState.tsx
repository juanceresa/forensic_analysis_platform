export function LoadingState() {
  return (
    <div className="h-screen flex items-center justify-center bg-slate-950">
      <div className="text-center" role="status" aria-live="polite" aria-label="Loading graph data">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto mb-4" />
        <p className="text-slate-400 font-mono text-sm">
          Loading intelligence graph...
        </p>
      </div>
    </div>
  );
}
