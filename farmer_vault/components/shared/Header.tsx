'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useMemo, useRef, useCallback } from 'react';

interface SlimSidebarProps {
  caseId: string;
}

// Hoisted static icons (rendering-hoist-jsx)
const TimelineIcon = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const GeoIcon = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const GraphIcon = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
  </svg>
);

export function Header({ caseId }: SlimSidebarProps) {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState(false);

  const narrativeBase = `/case/${caseId}/narrative`;
  const isNarrativeActive = pathname.startsWith(narrativeBase);

  // Memoize AI Analysis tabs config (rerender-memo pattern)
  const aiAnalysisTabs = useMemo(() => [
    { label: 'Timeline', shortLabel: 'T', href: `${narrativeBase}/chronological`, icon: TimelineIcon },
    { label: 'Geo', shortLabel: 'G', href: `${narrativeBase}/geolocation`, icon: GeoIcon },
    { label: 'Graph', shortLabel: 'K', href: `${narrativeBase}/graph`, icon: GraphIcon },
  ], [narrativeBase]);

  // Get active tab index for indicator position
  const activeTabIndex = useMemo(() => {
    const idx = aiAnalysisTabs.findIndex(tab =>
      pathname === tab.href || pathname.startsWith(tab.href + '/')
    );
    return idx >= 0 ? idx : 0;
  }, [pathname, aiAnalysisTabs]);

  const navItems = [
    {
      label: 'Dashboard',
      href: `/case/${caseId}`,
      icon: (
        <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
    },
    {
      label: 'Documents',
      href: `/case/${caseId}/documents`,
      icon: (
        <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      label: 'Entities',
      href: `/case/${caseId}/entities`,
      icon: (
        <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
    },
    {
      label: 'AI Analysis',
      href: narrativeBase,
      icon: (
        <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
      subItems: [
        { label: 'Timeline', href: `${narrativeBase}/chronological` },
        { label: 'Geolocation', href: `${narrativeBase}/geolocation` },
        { label: 'Knowledge Graph', href: `${narrativeBase}/graph` },
      ],
    },
  ];

  const isActive = (href: string) => {
    if (href === `/case/${caseId}`) {
      return pathname === href;
    }
    if (href === narrativeBase) {
      return pathname === narrativeBase || pathname.startsWith(narrativeBase + '/');
    }
    return pathname.startsWith(href);
  };

  const isSubActive = (href: string) => pathname === href || pathname.startsWith(href + '/');

  return (
    <aside
      className="h-screen flex flex-col shrink-0 transition-all duration-300"
      style={{
        width: expanded ? '256px' : '64px',
        backgroundColor: '#0D0D0D',
        borderRight: '1px solid #222222',
        transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {/* User Profile Section */}
      <div className="p-3">
        <div
          className="flex items-center gap-3 rounded-xl transition-all duration-300"
          style={{
            backgroundColor: expanded ? '#161616' : 'transparent',
            padding: expanded ? '8px' : '0px',
            justifyContent: expanded ? 'flex-start' : 'center',
          }}
        >
          {/* Avatar */}
          <div
            className="relative w-10 h-10 rounded-full flex items-center justify-center shrink-0 cursor-pointer transition-all duration-200 ease-out hover:scale-105 hover:z-10 hover-glow-lg"
            style={{
              backgroundColor: '#161616',
              border: expanded ? 'none' : '1px solid #222222',
            }}
          >
            <svg className="w-5 h-5" style={{ color: '#9ca3af' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>

          {/* User info (visible when expanded) */}
          <div
            className="min-w-0 overflow-hidden transition-all duration-200"
            style={{
              opacity: expanded ? 1 : 0,
              width: expanded ? 'auto' : 0,
              flex: expanded ? 1 : 0,
            }}
          >
            <p
              className="text-sm font-medium truncate"
              style={{ color: '#f1f5f9' }}
            >
              User Name
            </p>
            <p
              className="truncate"
              style={{
                color: 'rgba(255, 255, 255, 0.3)',
                fontSize: '10px',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}
            >
              Analyst · {caseId}
            </p>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="mx-3 mb-2" style={{ height: '1px', backgroundColor: '#222222' }} />

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto overflow-x-visible">
        {navItems.map((item) => {
          const active = isActive(item.href);
          const hasSubItems = item.subItems && item.subItems.length > 0;
          const showSubItems = hasSubItems && isNarrativeActive;

          return (
            <div key={item.href}>
              <Link
                href={item.href}
                title={!expanded ? item.label : undefined}
                className="relative flex items-center gap-3 rounded-xl transition-all duration-200 ease-out hover:scale-[1.02] hover:z-10 hover-glow"
                style={{
                  padding: expanded ? '10px 12px' : '10px',
                  justifyContent: expanded ? 'flex-start' : 'center',
                  backgroundColor: active ? '#161616' : 'transparent',
                  color: active ? '#f1f5f9' : '#6b7280',
                }}
              >
                {item.icon}
                <span
                  className="text-sm font-medium whitespace-nowrap overflow-hidden transition-opacity duration-200"
                  style={{
                    opacity: expanded ? 1 : 0,
                    width: expanded ? 'auto' : 0,
                  }}
                >
                  {item.label}
                </span>
              </Link>

              {/* Premium AI Analysis Tabs - Vertical Pillbox */}
              {hasSubItems && (
                <div
                  className="overflow-hidden transition-all duration-300"
                  style={{
                    maxHeight: showSubItems ? '200px' : '0px',
                    opacity: showSubItems ? 1 : 0,
                    transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
                  }}
                >
                  {/* Tab Container */}
                  <div
                    className="relative mt-2 rounded-lg p-1"
                    style={{
                      backgroundColor: '#0a0a0a',
                      border: '1px solid #1a1a1a',
                      marginLeft: expanded ? '20px' : '0px',
                    }}
                  >
                    {/* Sliding Indicator - Always Vertical */}
                    {activeTabIndex >= 0 && (
                      <div
                        className="absolute rounded-md transition-all duration-300 ease-out"
                        style={{
                          height: `calc(${100 / aiAnalysisTabs.length}% - ${expanded ? 2 : 4}px)`,
                          width: 'calc(100% - 8px)',
                          top: '4px',
                          left: '4px',
                          transform: `translateY(calc(${activeTabIndex * 100}% + ${activeTabIndex * (expanded ? 2 : 4)}px))`,
                          backgroundColor: '#161616',
                          boxShadow: '0 0 10px rgba(167, 243, 208, 0.15)',
                          border: '1px solid rgba(167, 243, 208, 0.1)',
                          transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
                        }}
                      />
                    )}

                    {/* Tab Items - Always Vertical */}
                    <div className="relative z-10 flex flex-col">
                      {aiAnalysisTabs.map((tab, index) => {
                        const tabActive = pathname === tab.href || pathname.startsWith(tab.href + '/');
                        return (
                          <Link
                            key={tab.href}
                            href={tab.href}
                            title={!expanded ? tab.label : undefined}
                            className="ai-tab relative flex items-center gap-2 rounded-md"
                            style={{
                              padding: expanded ? '8px 12px' : '8px 10px',
                              justifyContent: expanded ? 'flex-start' : 'center',
                              color: tabActive ? '#A7F3D0' : '#6b7280',
                              marginBottom: index < aiAnalysisTabs.length - 1 ? (expanded ? '2px' : '4px') : '0',
                            }}
                          >
                            {/* Icon */}
                            <span
                              className="shrink-0 transition-transform duration-200"
                              style={{
                                transform: tabActive ? 'scale(1.1)' : 'scale(1)',
                              }}
                            >
                              {tab.icon}
                            </span>

                            {/* Label (expanded only) */}
                            <span
                              className="text-xs font-medium whitespace-nowrap overflow-hidden transition-all duration-200"
                              style={{
                                opacity: expanded ? 1 : 0,
                                width: expanded ? 'auto' : 0,
                              }}
                            >
                              {tab.label}
                            </span>
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="p-3 space-y-2">
        {/* Notification bell */}
        <button
          className="relative flex items-center gap-3 w-full rounded-xl transition-all duration-200 ease-out hover:scale-[1.02] hover:z-10 hover-glow"
          style={{
            padding: expanded ? '10px 12px' : '10px',
            justifyContent: expanded ? 'flex-start' : 'center',
            backgroundColor: 'transparent',
            color: '#6b7280',
          }}
          title={!expanded ? 'Notifications' : undefined}
        >
          <div className="relative shrink-0">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span
              className="absolute -top-1 -right-1 w-2 h-2 rounded-full"
              style={{ backgroundColor: '#A7F3D0' }}
            />
          </div>
          <span
            className="text-sm font-medium whitespace-nowrap overflow-hidden transition-opacity duration-200"
            style={{
              opacity: expanded ? 1 : 0,
              width: expanded ? 'auto' : 0,
            }}
          >
            Notifications
          </span>
        </button>

        {/* Settings */}
        <button
          className="relative flex items-center gap-3 w-full rounded-xl transition-all duration-200 ease-out hover:scale-[1.02] hover:z-10 hover-glow"
          style={{
            padding: expanded ? '10px 12px' : '10px',
            justifyContent: expanded ? 'flex-start' : 'center',
            backgroundColor: 'transparent',
            color: '#6b7280',
          }}
          title={!expanded ? 'Settings' : undefined}
        >
          <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span
            className="text-sm font-medium whitespace-nowrap overflow-hidden transition-opacity duration-200"
            style={{
              opacity: expanded ? 1 : 0,
              width: expanded ? 'auto' : 0,
            }}
          >
            Settings
          </span>
        </button>

        {/* Expand/Collapse toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="relative flex items-center gap-3 w-full rounded-xl transition-all duration-200 ease-out hover:scale-[1.02] hover:z-10 hover-glow"
          style={{
            padding: expanded ? '10px 12px' : '10px',
            justifyContent: expanded ? 'flex-start' : 'center',
            backgroundColor: '#161616',
            color: '#f1f5f9',
          }}
        >
          <svg
            className="w-5 h-5 shrink-0 transition-transform duration-300"
            style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
          <span
            className="text-sm font-medium whitespace-nowrap overflow-hidden transition-opacity duration-200"
            style={{
              opacity: expanded ? 1 : 0,
              width: expanded ? 'auto' : 0,
            }}
          >
            Collapse
          </span>
        </button>
      </div>
    </aside>
  );
}
