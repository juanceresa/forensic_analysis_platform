import { readdir } from 'fs/promises';
import path from 'path';
import { redirect } from 'next/navigation';

const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

async function pickDefaultCaseId(): Promise<string | null> {
  const configured = process.env.DEFAULT_CASE_ID;
  if (configured && CASE_ID_PATTERN.test(configured)) {
    return configured;
  }

  try {
    const casesDir = path.join(process.cwd(), '..', 'cases');
    const entries = await readdir(casesDir, { withFileTypes: true });
    const caseIds = entries
      .filter((entry) => entry.isDirectory() && CASE_ID_PATTERN.test(entry.name))
      .map((entry) => entry.name)
      .sort();

    if (caseIds.length === 0) return null;
    if (caseIds.includes('DEMO-SYNTHETIC')) return 'DEMO-SYNTHETIC';
    return caseIds[0];
  } catch {
    return null;
  }
}

export default async function Home() {
  const caseId = await pickDefaultCaseId();

  if (caseId) {
    redirect(`/case/${encodeURIComponent(caseId)}`);
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="max-w-2xl w-full p-8 border border-[var(--border)] rounded bg-[var(--card)]">
        <h1 className="text-2xl font-mono text-foreground mb-4">Civic Table</h1>
        <p className="text-sm text-muted-foreground mb-4">
          No local case directory was found.
        </p>
        <p className="text-sm text-muted-foreground mb-2">
          Install the synthetic demo case from repository root:
        </p>
        <pre className="text-xs font-mono bg-muted/40 border border-[var(--border)] rounded p-3 overflow-x-auto">
          bash scripts/install_demo_case.sh
        </pre>
      </div>
    </main>
  );
}
