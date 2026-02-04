'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AnimatedNumber } from './AnimatedNumber';

// Tier configuration with colors matching CSS variables
const TIER_CONFIG = {
  TIER_3_AI: {
    label: 'AI Extracted',
    color: '#f59e0b', // amber
    glowClass: 'shadow-glow-amber',
    bgClass: 'bg-amber-500',
  },
  TIER_2_ANALYST: {
    label: 'Analyst Verified',
    color: '#3b82f6', // blue
    glowClass: 'shadow-glow-blue',
    bgClass: 'bg-blue-500',
  },
  TIER_1_CERTIFIED: {
    label: 'Certified',
    color: '#10b981', // emerald
    glowClass: 'shadow-glow-emerald',
    bgClass: 'bg-emerald-500',
  },
  TIER_4_SOURCE: {
    label: 'Source Document',
    color: '#a855f7', // purple
    glowClass: 'shadow-glow-purple',
    bgClass: 'bg-purple-500',
  },
} as const;

type TierKey = keyof typeof TIER_CONFIG;

interface VerificationChartProps {
  distribution: Record<string, number>;
  totalEntities: number;
}

export function VerificationChart({
  distribution,
  totalEntities,
}: VerificationChartProps) {
  // Transform distribution into chart data
  const chartData = Object.entries(distribution)
    .filter(([, count]) => count > 0)
    .map(([tier, count]) => ({
      name: tier,
      value: count,
      label: TIER_CONFIG[tier as TierKey]?.label || tier,
      color: TIER_CONFIG[tier as TierKey]?.color || '#6b7280',
      percent: totalEntities > 0 ? (count / totalEntities) * 100 : 0,
    }));

  // Count AI tier entities for live indicator
  const aiCount = distribution.TIER_3_AI || 0;
  const showLiveIndicator = aiCount > 0;

  // Custom tooltip content
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-lg">
          <p className="text-sm font-medium text-foreground">{data.label}</p>
          <p className="text-xs text-muted-foreground">
            {data.value} entities ({Math.round(data.percent)}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="w-fit">
      <CardHeader className="pb-2 px-5">
        <div className="flex items-center gap-2">
          <CardTitle className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
            Verification Status
          </CardTitle>
          {showLiveIndicator && (
            <UITooltip>
              <TooltipTrigger asChild>
                <div className="w-2 h-2 rounded-full bg-amber-500 pulse-live cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="right">
                {aiCount} entities awaiting analyst review
              </TooltipContent>
            </UITooltip>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0 px-5 pb-5">
        <div className="flex flex-col items-center gap-3">
          {/* Donut Chart */}
          <div className="relative w-28 h-28">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={32}
                  outerRadius={48}
                  paddingAngle={2}
                  dataKey="value"
                  stroke="none"
                >
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      className="transition-all duration-200 hover:opacity-80"
                      style={{
                        filter: `drop-shadow(0 0 4px ${entry.color}80)`,
                      }}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>

            {/* Center total */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <AnimatedNumber
                value={totalEntities}
                className="text-xl font-mono font-semibold"
              />
              <span className="text-[8px] text-muted-foreground uppercase tracking-wider">
                total
              </span>
            </div>
          </div>

          {/* Legend - stacked */}
          <div className="flex flex-col gap-1">
            {chartData.map((item) => {
              const config = TIER_CONFIG[item.name as TierKey];
              return (
                <div
                  key={item.name}
                  className="flex items-center gap-2"
                >
                  <div
                    className={`w-2 h-2 rounded-sm ${config?.bgClass || 'bg-gray-500'}`}
                    style={{
                      boxShadow: `0 0 6px ${item.color}50`,
                    }}
                  />
                  <span className="text-xs text-muted-foreground">
                    {item.label}
                  </span>
                  <span className="text-xs font-mono tabular-nums text-foreground">
                    {item.value}
                  </span>
                  <span className="text-[10px] text-muted-foreground/60">
                    ({Math.round(item.percent)}%)
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
