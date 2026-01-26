interface HeaderProps {
  caseName?: string;
}

export function Header({ caseName }: HeaderProps) {
  return (
    <header className="h-14 border-b border-slate-800 flex items-center px-6 bg-slate-950">
      <div className="flex items-center gap-4 flex-1">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-slate-800 rounded flex items-center justify-center">
            <span className="text-xs font-mono font-bold text-slate-400">CT</span>
          </div>
          <span className="font-mono text-sm text-slate-300">Civic Table</span>
        </div>

        {/* Case Name */}
        {caseName && (
          <>
            <div className="w-px h-6 bg-slate-800" aria-hidden="true" />
            <span className="text-sm text-slate-400 font-mono">{caseName}</span>
          </>
        )}
      </div>

      {/* User Menu Placeholder */}
      <div className="flex items-center gap-3">
        <button
          className="p-2 hover:bg-slate-800 rounded transition-colors focus-visible:ring-2 focus-visible:ring-blue-500"
          aria-label="User menu"
        >
          <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </button>
      </div>
    </header>
  );
}
