import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { AppSidebar } from '@/components/shared/AppSidebar';
import { HeaderBreadcrumbs } from '@/components/shared/HeaderBreadcrumbs';

interface CaseLayoutProps {
  children: React.ReactNode;
  params: Promise<{ caseId: string }>;
}

export default async function CaseLayout({ children, params }: CaseLayoutProps) {
  const { caseId } = await params;

  return (
    <div className="dark">
      <SidebarProvider
        defaultOpen={true}
        style={
          {
            '--sidebar-width': '16rem',
            '--sidebar-width-icon': '4rem',
          } as React.CSSProperties
        }
      >
        <AppSidebar caseId={caseId} />
        <SidebarInset className="bg-background min-w-0 overflow-x-hidden">
          {/* Header with trigger and breadcrumbs */}
          <header className="flex h-12 shrink-0 items-center gap-2 border-b border-border/50 px-4">
            <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-foreground hover:bg-sidebar-accent" />
            <Separator
              orientation="vertical"
              className="mr-2 h-4 bg-border"
            />
            <HeaderBreadcrumbs caseId={caseId} />
          </header>

          {/* Main content */}
          <main id="main-content" className="relative flex-1 min-h-0 overflow-y-auto overflow-x-hidden">
            {children}
          </main>
        </SidebarInset>
      </SidebarProvider>
    </div>
  );
}
