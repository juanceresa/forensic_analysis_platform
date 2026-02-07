'use client';

import { useCallback, useEffect, useState } from 'react';
import { KnowledgeGraph } from './KnowledgeGraph';
import { EntitySidebar } from './EntitySidebar';
import { useGraphSettings } from '@/hooks/useGraphSettings';
import type { GraphData, BaseNode, EntityType } from '@/lib/types';
import { ENTITY_COLORS, ENTITY_LABELS } from '@/lib/graph-settings';
import { RELATION_CATEGORIES } from '@/lib/relation-categories';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

const ENTITY_TYPES: EntityType[] = ['PERSON', 'PROPERTY', 'ORGANIZATION', 'LOCATION', 'DOCUMENT'];

interface GraphViewProps {
  caseId: string;
}

export function GraphView({ caseId }: GraphViewProps) {
  const { settings, updateSetting, resetSettings, isLoaded } = useGraphSettings();
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  useEffect(() => {
    async function fetchGraphData() {
      try {
        const res = await fetch(`/api/cases/${caseId}/graph`);
        if (!res.ok) throw new Error('Failed to fetch graph data');
        const data = await res.json();
        setGraphData(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load graph');
      } finally {
        setLoading(false);
      }
    }
    fetchGraphData();
  }, [caseId]);

  const handleNodeClick = useCallback((node: BaseNode) => {
    setSelectedNodeId(node.id);
  }, []);

  const handleBackgroundClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  const toggleEntityType = useCallback((type: EntityType) => {
    updateSetting('entityTypeFilters', {
      ...settings.entityTypeFilters,
      [type]: !settings.entityTypeFilters[type],
    });
  }, [settings.entityTypeFilters, updateSetting]);

  const toggleRelationCategory = useCallback((category: string) => {
    updateSetting('relationCategoryVisibility', {
      ...settings.relationCategoryVisibility,
      [category]: !settings.relationCategoryVisibility[category],
    });
  }, [settings.relationCategoryVisibility, updateSetting]);

  if (loading || !isLoaded) {
    return (
      <div className="h-full flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin motion-reduce:animate-none rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground font-mono text-sm">Loading graph...</p>
        </div>
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div className="h-full flex items-center justify-center bg-background">
        <div className="text-center p-8 bg-card border border-destructive/30 rounded-lg">
          <p className="text-destructive font-mono text-sm">{error || 'Failed to load graph data'}</p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="h-full flex flex-col bg-background">
        {/* Toolbar */}
        <div className="shrink-0 border-b border-border">
          <div className="px-3 py-1.5 flex items-center gap-1 flex-wrap">
            {/* Entity type filters */}
            {ENTITY_TYPES.map((type) => {
              const active = settings.entityTypeFilters[type];
              return (
                <Tooltip key={type}>
                  <TooltipTrigger asChild>
                    <Button
                      variant={active ? 'secondary' : 'ghost'}
                      size="xs"
                      onClick={() => toggleEntityType(type)}
                      className={active ? 'opacity-100' : 'opacity-40'}
                    >
                      <span
                        className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: ENTITY_COLORS[type] }}
                      />
                      <span className="font-mono text-xs">{ENTITY_LABELS[type]}</span>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>{active ? 'Hide' : 'Show'} {ENTITY_LABELS[type].toLowerCase()} nodes</TooltipContent>
                </Tooltip>
              );
            })}

            <Separator orientation="vertical" className="mx-1 h-5" />

            {/* Relation category filters */}
            {Object.entries(RELATION_CATEGORIES).map(([key, cat]) => {
              const active = settings.relationCategoryVisibility[key];
              return (
                <Tooltip key={key}>
                  <TooltipTrigger asChild>
                    <Button
                      variant={active ? 'secondary' : 'ghost'}
                      size="xs"
                      onClick={() => toggleRelationCategory(key)}
                      className={active ? 'opacity-100' : 'opacity-40'}
                    >
                      <span
                        className="inline-block w-4 h-0.5 rounded shrink-0"
                        style={{ backgroundColor: cat.color }}
                      />
                      <span className="font-mono text-xs">{cat.label}</span>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>{active ? 'Hide' : 'Show'} {cat.label.toLowerCase()} links</TooltipContent>
                </Tooltip>
              );
            })}

            <Separator orientation="vertical" className="mx-1 h-5" />

            {/* Toggle controls */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={settings.hideOrphans ? 'secondary' : 'ghost'}
                  size="xs"
                  onClick={() => updateSetting('hideOrphans', !settings.hideOrphans)}
                >
                  <OrphanIcon />
                  <span className="font-mono text-xs">Orphans</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>{settings.hideOrphans ? 'Show' : 'Hide'} unconnected nodes</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={settings.showArrows ? 'secondary' : 'ghost'}
                  size="xs"
                  onClick={() => updateSetting('showArrows', !settings.showArrows)}
                >
                  <ArrowIcon />
                  <span className="font-mono text-xs">Arrows</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>{settings.showArrows ? 'Hide' : 'Show'} directional arrows</TooltipContent>
            </Tooltip>

            <div className="ml-auto flex items-center gap-1">
              <span className="text-xs text-muted-foreground font-mono mr-2">
                {graphData.nodes.length} entities · {graphData.links.length} relations
              </span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="xs" onClick={resetSettings}>
                    <ResetIcon />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Reset filters</TooltipContent>
              </Tooltip>
            </div>
          </div>
        </div>

        {/* Graph + Sidebar */}
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 min-w-0 relative">
            <KnowledgeGraph
              data={graphData}
              selectedNodeId={selectedNodeId}
              onNodeClick={handleNodeClick}
              onBackgroundClick={handleBackgroundClick}
              settings={settings}
            />
          </div>

          <EntitySidebar
            selectedNodeId={selectedNodeId}
            caseId={caseId}
          />
        </div>
      </div>
    </TooltipProvider>
  );
}

function OrphanIcon() {
  return (
    <svg className="size-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="8" cy="8" r="3" />
      <path d="M8 1v2M8 13v2M1 8h2M13 8h2" strokeLinecap="round" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg className="size-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M2 8h10M9 5l3 3-3 3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ResetIcon() {
  return (
    <svg className="size-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M2 8a6 6 0 1 1 1.5 4" strokeLinecap="round" />
      <path d="M2 12V8h4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
