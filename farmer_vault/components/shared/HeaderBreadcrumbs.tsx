'use client';

import { Fragment } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

interface HeaderBreadcrumbsProps {
  caseId: string;
}

// Map route segments to display labels
const ROUTE_LABELS: Record<string, string> = {
  documents: 'Documents',
  document: 'Documents', // Singular route shows as plural
  entities: 'Entities',
  entity: 'Entities', // Singular route shows as plural
  narrative: 'AI Analysis',
  chronological: 'Timeline',
  geolocation: 'Geolocation',
  graph: 'Knowledge Graph',
};

// Routes that should redirect to a different path when clicked
const ROUTE_REDIRECTS: Record<string, string> = {
  document: 'documents', // /document/[id] breadcrumb links to /documents
  entity: 'entities', // /entity/[id] breadcrumb links to /entities
};

export function HeaderBreadcrumbs({ caseId }: HeaderBreadcrumbsProps) {
  const pathname = usePathname();

  // Parse pathname into segments after /case/[caseId]/
  const basePath = `/case/${caseId}`;
  const relativePath = pathname.replace(basePath, '');
  const segments = relativePath.split('/').filter(Boolean);

  // If on dashboard (no segments), show just "Dashboard"
  if (segments.length === 0) {
    return (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              Dashboard
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    );
  }

  // Build breadcrumb items
  const items: { label: string; href?: string }[] = [];

  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];
    const isLast = i === segments.length - 1;
    const prevSegment = segments[i - 1];

    // Check if this is an ID (comes after document/entity)
    const isId = prevSegment === 'document' || prevSegment === 'entity';

    if (isId) {
      // This is the document/entity ID - format it nicely
      const label = decodeURIComponent(segment).replace(/_/g, ' ').replace(/-/g, ' ');
      items.push({
        label,
        href: undefined, // Current page, no link
      });
    } else {
      // This is a route segment
      const label = ROUTE_LABELS[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);

      // Build href - check for redirects
      const redirectSegment = ROUTE_REDIRECTS[segment] || segment;
      const href = isLast ? undefined : `${basePath}/${redirectSegment}`;

      items.push({
        label,
        href,
      });
    }
  }

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {items.map((item, index) => (
          <Fragment key={index}>
            {index > 0 && <BreadcrumbSeparator className="text-muted-foreground/40" />}
            <BreadcrumbItem>
              {item.href ? (
                <BreadcrumbLink asChild>
                  <Link
                    href={item.href}
                    className="font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {item.label}
                  </Link>
                </BreadcrumbLink>
              ) : (
                <BreadcrumbPage className="font-mono text-xs uppercase tracking-wider text-foreground">
                  {item.label}
                </BreadcrumbPage>
              )}
            </BreadcrumbItem>
          </Fragment>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
