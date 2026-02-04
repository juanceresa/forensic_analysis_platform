'use client';

import React, { useState } from 'react';
import { ChevronRight, FileDown } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
// Note: Can't use Radix Collapsible inside tables (renders div, breaks HTML semantics)
// Using simple state-based conditional rendering instead
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { DossierDownload } from './DossierDownload';
import { cn } from '@/lib/utils';

interface TaskItem {
  label: string;
  complete: boolean;
  reviewer?: string;
}

interface WorkflowStage {
  complete: boolean;
  items: TaskItem[];
}

interface WorkflowStages {
  intake: WorkflowStage;
  processing: WorkflowStage;
  analysis: WorkflowStage;
  certification: WorkflowStage;
}

interface WorkflowTableProps {
  stages: WorkflowStages;
  caseId: string;
}

const STAGE_ORDER = ['intake', 'processing', 'analysis', 'certification'] as const;

const STAGE_LABELS: Record<(typeof STAGE_ORDER)[number], string> = {
  intake: 'Intake',
  processing: 'Processing',
  analysis: 'Analysis',
  certification: 'Certification',
};

export function WorkflowTable({ stages, caseId }: WorkflowTableProps) {
  // Track which stages are open
  const [openStages, setOpenStages] = useState<Set<string>>(() => {
    // Default: open stages that are in progress (not complete, but have some items done)
    const initial = new Set<string>();
    STAGE_ORDER.forEach((stageKey) => {
      const stage = stages[stageKey];
      const completed = stage.items.filter((i) => i.complete).length;
      const total = stage.items.length;
      if (!stage.complete && completed > 0 && completed < total) {
        initial.add(stageKey);
      }
      // Also open first incomplete stage
      if (!stage.complete && initial.size === 0) {
        initial.add(stageKey);
      }
    });
    return initial;
  });

  const toggleStage = (stageKey: string) => {
    setOpenStages((prev) => {
      const next = new Set(prev);
      if (next.has(stageKey)) {
        next.delete(stageKey);
      } else {
        next.add(stageKey);
      }
      return next;
    });
  };

  // Calculate stats for each stage
  const stageStats = STAGE_ORDER.map((stageKey) => {
    const stage = stages[stageKey];
    const total = stage.items.length;
    const completed = stage.items.filter((item) => item.complete).length;
    const percent = total > 0 ? (completed / total) * 100 : 0;
    return {
      stageKey,
      stage,
      total,
      completed,
      percent,
      isComplete: stage.complete,
    };
  });

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="border-b border-border hover:bg-transparent">
              <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 w-[40%]">
                Stage
              </TableHead>
              <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 text-center w-[25%]">
                Progress
              </TableHead>
              <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 text-center w-[15%]">
                Tasks
              </TableHead>
              <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 text-right w-[20%]">
                Status
              </TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {stageStats.map(
              ({ stageKey, stage, total, completed, percent, isComplete }) => {
                const isOpen = openStages.has(stageKey);

                return (
                  <React.Fragment key={stageKey}>
                    {/* Stage Row */}
                    <TableRow
                      className={cn(
                        'cursor-pointer transition-colors',
                        isOpen && 'bg-muted/30'
                      )}
                      onClick={() => toggleStage(stageKey)}
                    >
                      <TableCell>
                        <button className="flex items-center gap-2 w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded">
                          <ChevronRight
                            className={cn(
                              'w-4 h-4 text-muted-foreground transition-transform duration-200',
                              isOpen && 'rotate-90'
                            )}
                          />
                          <span className="text-sm font-medium">
                            {STAGE_LABELS[stageKey]}
                          </span>
                        </button>
                      </TableCell>

                        <TableCell>
                          <div className="flex items-center justify-center">
                            <Progress
                              value={percent}
                              className={cn(
                                'h-1.5 w-full max-w-[100px]',
                                '[&>[data-slot=progress-indicator]]:transition-all',
                                isComplete
                                  ? '[&>[data-slot=progress-indicator]]:bg-emerald-500 [&>[data-slot=progress-indicator]]:shadow-glow-emerald'
                                  : '[&>[data-slot=progress-indicator]]:bg-blue-500 [&>[data-slot=progress-indicator]]:shadow-glow-blue'
                              )}
                            />
                          </div>
                        </TableCell>

                        <TableCell className="text-center">
                          <span className="text-sm font-mono tabular-nums text-muted-foreground">
                            {completed}/{total}
                          </span>
                        </TableCell>

                        <TableCell className="text-right">
                          {isComplete ? (
                            <Badge
                              variant="outline"
                              className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            >
                              <svg
                                className="w-3 h-3 mr-1"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                              Done
                            </Badge>
                          ) : completed === 0 ? (
                            <Badge
                              variant="outline"
                              className="bg-muted/50 text-muted-foreground border-border"
                            >
                              Pending
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="bg-blue-500/10 text-blue-400 border-blue-500/20"
                            >
                              In Progress
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>

                    {/* Expanded Tasks */}
                    {isOpen && (
                      <tr>
                        <td colSpan={4} className="p-0">
                          <div className="ml-6 mr-4 mb-3 mt-1 border-l-2 border-border/50 pl-4">
                            {stage.items.map((item, itemIndex) => (
                              <div
                                key={itemIndex}
                                className={cn(
                                  'flex items-center gap-3 py-2 transition-colors',
                                  itemIndex < stage.items.length - 1 &&
                                    'border-b border-border/20'
                                )}
                              >
                                <Checkbox
                                  checked={item.complete}
                                  disabled
                                  className={cn(
                                    'h-4 w-4',
                                    item.complete &&
                                      'data-[state=checked]:bg-emerald-500 data-[state=checked]:border-emerald-500'
                                  )}
                                />
                                <span
                                  className={cn(
                                    'text-sm flex-1',
                                    item.complete
                                      ? 'text-muted-foreground line-through decoration-muted-foreground/30'
                                      : 'text-foreground/80'
                                  )}
                                >
                                  {item.label}
                                </span>
                                {item.reviewer && (
                                  <span className="text-xs text-muted-foreground/60">
                                    {item.reviewer}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              }
            )}
            {/* Dossier Row */}
            <TableRow className="border-t border-border hover:bg-transparent">
              <TableCell colSpan={4} className="py-3">
                <DossierDownload caseId={caseId} />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
