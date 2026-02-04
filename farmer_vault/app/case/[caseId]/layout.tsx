import { Header } from '@/components/shared';

interface CaseLayoutProps {
  children: React.ReactNode;
  params: Promise<{ caseId: string }>;
}

export default async function CaseLayout({ children, params }: CaseLayoutProps) {
  const { caseId } = await params;

  return (
    <div className="h-screen flex" style={{ backgroundColor: '#0D0D0D' }}>
      {/* Slim sidebar (64px) */}
      <Header caseId={caseId} />

      {/* Main content */}
      <main id="main-content" className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
