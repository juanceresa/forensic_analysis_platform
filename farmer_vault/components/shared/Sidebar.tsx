'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface SidebarProps {
  caseId: string;
}

const SUB_ITEMS = [
  { label: 'Chronological', href: 'chronological' },
  { label: 'Geolocation', href: 'geolocation' },
  { label: 'Graph', href: 'graph' },
];

export function Sidebar({ caseId }: SidebarProps) {
  const pathname = usePathname();

  const narrativeBase = `/case/${caseId}/narrative`;
  const isNarrativeActive = pathname.startsWith(narrativeBase);

  const navItems = [
    {
      label: 'Dashboard',
      href: `/case/${caseId}`,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
    },
    {
      label: 'Documents',
      href: `/case/${caseId}/documents`,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      label: 'Entities',
      href: `/case/${caseId}/entities`,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
    },
    {
      label: 'AI Analysis',
      href: narrativeBase,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ];

  const isActive = (href: string) => {
    if (href === `/case/${caseId}`) {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <aside className="w-60 overflow-y-auto" style={{ backgroundColor: '#0D0D0D', borderRight: '1px solid #222222' }}>
      <nav className="p-4" aria-label="Main navigation">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg font-mono text-sm transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500"
                  style={active ? {
                    backgroundColor: '#161616',
                    border: '1px solid #222222',
                    color: '#f1f5f9',
                  } : {
                    color: '#9ca3af',
                  }}
                  aria-current={active ? 'page' : undefined}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>

                {/* Nested sub-items for AI Analysis */}
                {item.label === 'AI Analysis' && isNarrativeActive && (
                  <ul className="ml-8 mt-1 space-y-0.5">
                    {SUB_ITEMS.map((sub) => {
                      const subHref = `${narrativeBase}/${sub.href}`;
                      const subActive = pathname.startsWith(subHref);
                      return (
                        <li key={sub.href}>
                          <Link
                            href={subHref}
                            className={`
                              block px-2 py-1 rounded text-xs font-mono transition-colors
                              focus-visible:ring-2 focus-visible:ring-blue-500
                              ${
                                subActive
                                  ? 'text-slate-200 bg-slate-800/50'
                                  : 'text-slate-500 hover:text-slate-400 hover:bg-slate-900/50'
                              }
                            `}
                            aria-current={subActive ? 'page' : undefined}
                          >
                            {sub.label}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
