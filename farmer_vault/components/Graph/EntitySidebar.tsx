'use client';

import { useEffect, useState } from 'react';
import { EntityDetail } from '../Entities/EntityDetail';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { BaseNode } from '@/lib/types';
import { PanelRightClose, PanelRightOpen } from 'lucide-react';

interface EntityData {
  entity: BaseNode;
  sourceDocuments: { id: string; filename: string }[];
  connections: {
    relation_type: string;
    targetEntity: {
      id: string;
      name: string;
      entity_type: string;
      verification: { tier: string; confidence: number };
    };
  }[];
}

interface EntitySidebarProps {
  selectedNodeId: string | null;
  caseId: string;
}

export function EntitySidebar({ selectedNodeId, caseId }: EntitySidebarProps) {
  const [entityData, setEntityData] = useState<EntityData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);

  // Auto-expand when a node is selected
  useEffect(() => {
    if (selectedNodeId) setCollapsed(false);
  }, [selectedNodeId]);

  useEffect(() => {
    if (!selectedNodeId) {
      setEntityData(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(`/api/cases/${caseId}/entity/${encodeURIComponent(selectedNodeId)}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch entity');
        return res.json();
      })
      .then((data) => { if (!cancelled) setEntityData(data); })
      .catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [caseId, selectedNodeId]);

  if (collapsed) {
    return (
      <div className="w-8 h-full min-h-0 shrink-0 overflow-hidden border-l border-border flex items-start justify-center pt-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => setCollapsed(false)}
              className="text-muted-foreground hover:text-foreground"
              aria-label="Show entity panel"
            >
              <PanelRightOpen className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">Show entity panel</TooltipContent>
        </Tooltip>
      </div>
    );
  }

  return (
    <div className="w-[460px] max-w-[45vw] min-h-0 shrink-0 overflow-hidden border-l border-border flex flex-col bg-background">
      <div className="px-4 py-2 border-b border-border flex items-center justify-between">
        <h2 className="text-sm font-mono font-medium text-foreground">Entity Detail</h2>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => setCollapsed(true)}
              className="text-muted-foreground hover:text-foreground"
              aria-label="Hide entity panel"
            >
              <PanelRightClose className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">Hide entity panel</TooltipContent>
        </Tooltip>
      </div>

      <ScrollArea className="flex-1 min-h-0 [&>[data-slot=scroll-area-viewport]]:!overflow-x-hidden">
        <div className="w-full">
          {!selectedNodeId && (
            <div className="flex items-center justify-center h-64 p-8">
              <p className="text-muted-foreground font-mono text-sm text-center">
                Click a node to view details
              </p>
            </div>
          )}

          {selectedNodeId && loading && (
            <div className="flex items-center justify-center h-64 p-8">
              <div className="text-center">
                <div className="animate-spin motion-reduce:animate-none rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-3" />
                <p className="text-muted-foreground font-mono text-sm">Loading entity...</p>
              </div>
            </div>
          )}

          {selectedNodeId && error && (
            <div className="p-6">
              <div className="p-4 bg-card border border-destructive/30 rounded-lg">
                <p className="text-destructive font-mono text-sm">{error}</p>
              </div>
            </div>
          )}

          {selectedNodeId && !loading && !error && entityData && (
            <EntityDetail
              entity={entityData.entity}
              sourceDocuments={entityData.sourceDocuments}
              connections={entityData.connections}
              caseId={caseId}
            />
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
