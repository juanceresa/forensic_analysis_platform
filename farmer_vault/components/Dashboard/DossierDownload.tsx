'use client';

import { useState, useEffect, useCallback } from 'react';

interface DossierDownloadProps {
  caseId: string;
}

export function DossierDownload({ caseId }: DossierDownloadProps) {
  const [dossierAvailable, setDossierAvailable] = useState(false);
  const [checkingDossier, setCheckingDossier] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkAvailability = useCallback(async () => {
    setCheckingDossier(true);
    setError(null);
    try {
      const res = await fetch(`/api/cases/${caseId}/dossier`, { method: 'HEAD' });
      setDossierAvailable(res.ok);
    } catch {
      setDossierAvailable(false);
    } finally {
      setCheckingDossier(false);
    }
  }, [caseId]);

  useEffect(() => {
    checkAvailability();
  }, [checkAvailability]);

  const handleDownload = async () => {
    setDownloading(true);
    setError(null);
    try {
      const res = await fetch(`/api/cases/${caseId}/dossier`);
      if (!res.ok) {
        throw new Error(`Download failed: ${res.status}`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${caseId}_dossier.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Download failed. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex items-center gap-3 p-2 -m-2">
      {/* Status indicator */}
      <div
        className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0
                   ${dossierAvailable ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}
      >
        {checkingDossier ? (
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : dossierAvailable ? (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        )}
      </div>

      {/* Label and action */}
      <div className="flex-1 flex items-center justify-between">
        <span
          className={`font-mono text-sm uppercase tracking-wider
                     ${dossierAvailable ? 'text-slate-200' : 'text-slate-500'}`}
        >
          {checkingDossier
            ? 'Checking dossier...'
            : dossierAvailable
              ? 'Dossier ready'
              : 'Dossier in preparation'}
        </span>

        {!checkingDossier && (
          <div className="flex items-center gap-2">
            {dossierAvailable ? (
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800
                         text-white text-xs font-mono uppercase tracking-wider rounded
                         transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {downloading ? 'Downloading...' : 'Download PDF'}
              </button>
            ) : (
              <button
                onClick={checkAvailability}
                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600
                         text-slate-300 text-xs font-mono uppercase tracking-wider rounded
                         transition-colors focus:outline-none focus:ring-2 focus:ring-slate-500"
              >
                Check again
              </button>
            )}
          </div>
        )}
      </div>

      {/* Error message */}
      {error && <span className="text-xs text-red-400 ml-2">{error}</span>}
    </div>
  );
}
