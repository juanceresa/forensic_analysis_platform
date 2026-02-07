'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function LoginPage() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });

      if (res.ok) {
        const next = searchParams.get('next') || '/';
        router.push(next);
        router.refresh();
      } else {
        setError('Invalid password');
        setPassword('');
      }
    } catch {
      setError('Connection error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-mono tracking-tight text-foreground">Civic Table</h1>
          <p className="text-sm text-muted-foreground mt-2">Forensic Intelligence Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter access code"
              autoFocus
              className="w-full px-4 py-3 bg-[var(--card)] border border-[var(--border)] rounded
                         text-foreground placeholder-muted-foreground font-mono text-sm text-center
                         focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            />
          </div>

          {error && (
            <p className="text-sm text-red-400 text-center font-mono">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !password}
            className="w-full px-4 py-3 bg-foreground text-background font-mono text-sm rounded
                       hover:bg-foreground/90 transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Verifying...' : 'Enter'}
          </button>
        </form>

        <p className="text-xs text-muted-foreground/50 text-center mt-8">
          AI-generated research analysis — not a legal document
        </p>
      </div>
    </div>
  );
}
