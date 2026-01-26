import { Header, Sidebar } from '@/components/shared';

interface CaseLayoutProps {
  children: React.ReactNode;
  params: Promise<{ caseId: string }>;
}

export default async function CaseLayout({ children, params }: CaseLayoutProps) {
  const { caseId } = await params;

  return (
    <div className="h-screen flex flex-col bg-slate-950">
      <Header caseName={caseId} />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar caseId={caseId} />

        <main id="main-content" className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
