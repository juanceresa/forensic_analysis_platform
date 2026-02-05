'use client';

import { Calendar, FileText, Users, GitBranch } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import { AnimatedNumber } from './AnimatedNumber';

interface StatPill {
  label: string;
  value: number;
  color: string;
  glowClass: string;
  icon: React.ReactNode;
  hoverContent?: React.ReactNode;
}

interface AmbientHeroProps {
  caseId: string;
  dateRange?: {
    earliest: string | null;
    latest: string | null;
  };
  metrics: {
    documents: number;
    entities: number;
    relationships: number;
  };
  entityTypeSummary?: Record<string, number>;
}

export function AmbientHero({
  caseId,
  dateRange,
  metrics,
  entityTypeSummary,
}: AmbientHeroProps) {
  // Format date range for display
  const dateRangeText =
    dateRange?.earliest && dateRange?.latest
      ? `${new Date(dateRange.earliest).getFullYear()} — ${new Date(dateRange.latest).getFullYear()}`
      : null;

  const statPills: StatPill[] = [
    {
      label: 'documents',
      value: metrics.documents,
      color: 'bg-primary',
      glowClass: 'shadow-glow-mint',
      icon: <FileText className="w-3.5 h-3.5" />,
      hoverContent: (
        <div className="space-y-1">
          <p className="text-sm font-medium">Source Documents</p>
          <p className="text-xs text-muted-foreground">
            {metrics.documents} documents processed and analyzed
          </p>
        </div>
      ),
    },
    {
      label: 'entities',
      value: metrics.entities,
      color: 'bg-blue-500',
      glowClass: 'shadow-glow-blue',
      icon: <Users className="w-3.5 h-3.5" />,
      hoverContent: entityTypeSummary ? (
        <div className="space-y-2">
          <p className="text-sm font-medium">Entity Breakdown</p>
          <div className="space-y-1">
            {Object.entries(entityTypeSummary).map(([type, count]) => (
              <div
                key={type}
                className="flex items-center justify-between text-xs"
              >
                <span className="text-muted-foreground capitalize">
                  {type.toLowerCase()}
                </span>
                <span className="font-mono tabular-nums">{count}</span>
              </div>
            ))}
          </div>
        </div>
      ) : undefined,
    },
    {
      label: 'relationships',
      value: metrics.relationships,
      color: 'bg-purple-500',
      glowClass: 'shadow-glow-purple',
      icon: <GitBranch className="w-3.5 h-3.5" />,
      hoverContent: (
        <div className="space-y-1">
          <p className="text-sm font-medium">Knowledge Graph</p>
          <p className="text-xs text-muted-foreground">
            {metrics.relationships} connections between entities
          </p>
        </div>
      ),
    },
  ];

  return (
    <header className="relative overflow-hidden min-h-[180px]">
      {/* Background Image Layer */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-[0.08] grayscale"
        style={{
          backgroundImage:
            'url(https://images.unsplash.com/photo-1639322537228-f710d846310a?w=1920&q=80)',
        }}
      />

      {/* Gradient Overlay */}
      <div
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(180deg, transparent 0%, hsl(var(--background)) 85%)',
        }}
      />

      {/* Subtle Top Glow */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[200px] pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at center, rgba(167, 243, 208, 0.06) 0%, transparent 70%)',
        }}
      />

      {/* Content */}
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 sm:pt-10 pb-6 sm:pb-8">
        {/* Badge Cluster */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
          <Badge
            variant="outline"
            className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground border-border/50 bg-background/50"
          >
            Case File
          </Badge>

          {dateRangeText && (
            <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wide text-muted-foreground/60">
              <Calendar className="w-3 h-3" />
              {dateRangeText}
            </span>
          )}
        </div>

        {/* Case Name */}
        <h1 className="font-mono text-2xl sm:text-3xl lg:text-4xl font-semibold text-foreground leading-tight tracking-tight">
          {caseId}
        </h1>

        {/* Stat Pills Row */}
        <div className="flex flex-wrap items-center gap-3 sm:gap-6 mt-3 sm:mt-4">
          {statPills.map((stat, index) => (
            <HoverCard key={stat.label} openDelay={200} closeDelay={100}>
              <HoverCardTrigger asChild>
                <button className="flex items-center gap-2 group cursor-default">
                  <div
                    className={`w-2 h-2 rounded-full ${stat.color} ${stat.glowClass}`}
                  />
                  <span className="text-xs text-muted-foreground">
                    <AnimatedNumber
                      value={stat.value}
                      delay={index * 0.1}
                      className="font-semibold text-foreground/80"
                    />{' '}
                    {stat.label}
                  </span>
                </button>
              </HoverCardTrigger>
              {stat.hoverContent && (
                <HoverCardContent
                  className="w-56 bg-card border-border"
                  align="start"
                >
                  {stat.hoverContent}
                </HoverCardContent>
              )}
            </HoverCard>
          ))}
        </div>
      </div>
    </header>
  );
}
