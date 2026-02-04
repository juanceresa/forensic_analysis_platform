'use client';

import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import { AnimatedNumber } from './AnimatedNumber';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: number | string;
  href?: string;
  subtitle?: string;
  tooltip?: string;
  progress?: {
    value: number;
    glowColor?: 'blue' | 'mint' | 'amber' | 'emerald' | 'purple';
  };
  hoverContent?: React.ReactNode;
  animationDelay?: number;
  className?: string;
}

const glowClasses = {
  blue: 'shadow-glow-blue',
  mint: 'shadow-glow-mint',
  amber: 'shadow-glow-amber',
  emerald: 'shadow-glow-emerald',
  purple: 'shadow-glow-purple',
};

export function MetricCard({
  label,
  value,
  href,
  subtitle,
  tooltip,
  progress,
  hoverContent,
  animationDelay = 0,
  className,
}: MetricCardProps) {
  const cardContent = (
    <Card
      className={cn(
        'transition-all duration-200 ease-out cursor-default py-4',
        'hover:scale-[1.01] hover:border-primary/20',
        href && 'cursor-pointer hover:shadow-glow-mint/10',
        className
      )}
    >
      <CardContent className="space-y-2">
        {/* Label with optional tooltip */}
        {tooltip ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider cursor-help">
                {label}
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              {tooltip}
            </TooltipContent>
          </Tooltip>
        ) : (
          <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">
            {label}
          </div>
        )}

        {/* Value - animated number or text */}
        <div className="text-4xl font-mono tabular-nums">
          {typeof value === 'number' ? (
            <AnimatedNumber value={value} delay={animationDelay} />
          ) : (
            <span>{value}</span>
          )}
        </div>

        {/* Progress bar with glow */}
        {progress && (
          <div className="flex items-center gap-2 mt-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex-1">
                  <Progress
                    value={progress.value}
                    className={cn(
                      'h-1.5 bg-muted',
                      '[&>[data-slot=progress-indicator]]:transition-all',
                      progress.glowColor &&
                        `[&>[data-slot=progress-indicator]]:${glowClasses[progress.glowColor]}`
                    )}
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                {progress.value}% complete
              </TooltipContent>
            </Tooltip>
            <span className="text-xs text-muted-foreground font-mono tabular-nums">
              {progress.value}%
            </span>
          </div>
        )}

        {/* Subtitle / link hint */}
        {subtitle && (
          <div className="text-xs text-muted-foreground mt-1">{subtitle}</div>
        )}
      </CardContent>
    </Card>
  );

  // Wrap with HoverCard if hoverContent provided
  const withHoverCard = hoverContent ? (
    <HoverCard openDelay={300} closeDelay={100}>
      <HoverCardTrigger asChild>
        {href ? <Link href={href}>{cardContent}</Link> : cardContent}
      </HoverCardTrigger>
      <HoverCardContent className="w-64 bg-card border-border" align="start">
        {hoverContent}
      </HoverCardContent>
    </HoverCard>
  ) : href ? (
    <Link href={href}>{cardContent}</Link>
  ) : (
    cardContent
  );

  return withHoverCard;
}
