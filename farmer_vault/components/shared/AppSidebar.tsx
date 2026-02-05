'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  FileText,
  Users,
  Monitor,
  Clock,
  MapPin,
  Network,
  Bell,
  Settings,
  ChevronDown,
  Sparkles,
  Bookmark,
} from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
  SidebarSeparator,
} from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  caseId: string;
}

export function AppSidebar({ caseId, ...props }: AppSidebarProps) {
  const pathname = usePathname();
  const [aiAnalysisOpen, setAiAnalysisOpen] = React.useState(false);

  const narrativeBase = `/case/${caseId}/narrative`;
  const isNarrativeActive = pathname.startsWith(narrativeBase);

  // Auto-open AI Analysis when on a narrative route
  React.useEffect(() => {
    if (isNarrativeActive) {
      setAiAnalysisOpen(true);
    }
  }, [isNarrativeActive]);

  const navItems = [
    {
      label: 'Dashboard',
      href: `/case/${caseId}`,
      icon: Home,
    },
    {
      label: 'Documents',
      href: `/case/${caseId}/documents`,
      icon: FileText,
    },
    {
      label: 'Index',
      href: `/case/${caseId}/entities`,
      icon: Users,
    },
    {
      label: 'AI Analysis',
      href: narrativeBase,
      icon: Monitor,
      subItems: [
        { label: 'Explore', href: narrativeBase, icon: Sparkles },
        { label: 'Timeline', href: `${narrativeBase}/chronological`, icon: Clock },
        { label: 'Geolocation', href: `${narrativeBase}/geolocation`, icon: MapPin },
        { label: 'Knowledge Graph', href: `${narrativeBase}/graph`, icon: Network },
      ],
    },
    {
      label: 'Bookmarks',
      href: `/case/${caseId}/bookmarks`,
      icon: Bookmark,
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

  const isSubActive = (href: string) => {
    // For "Explore" (narrativeBase), require exact match only
    if (href === narrativeBase) {
      return pathname === href;
    }
    return pathname === href || pathname.startsWith(href + '/');
  };

  return (
    <Sidebar
      collapsible="icon"
      className="border-r border-border"
      {...props}
    >
      {/* User Profile Header */}
      <SidebarHeader className="p-3">
        <div className="flex items-center gap-3 rounded-xl bg-sidebar-accent p-2 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:bg-transparent group-data-[collapsible=icon]:p-0">
          {/* Avatar */}
          <div
            className={cn(
              'relative flex h-10 w-10 shrink-0 items-center justify-center rounded-full',
              'bg-sidebar-accent border border-border',
              'transition-all duration-200 ease-out',
              'hover:scale-105 hover:shadow-[0_0_15px_rgba(167,243,208,0.15)]'
            )}
          >
            <Users className="h-5 w-5 text-muted-foreground" />
          </div>

          {/* User info (hidden when collapsed) */}
          <div className="min-w-0 flex-1 group-data-[collapsible=icon]:hidden">
            <p className="truncate text-sm font-medium text-foreground">
              User Name
            </p>
            <p className="truncate text-[10px] font-bold uppercase tracking-wider text-muted-foreground/50">
              Analyst · {caseId}
            </p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarSeparator className="bg-border" />

      {/* Navigation */}
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const active = isActive(item.href);
                const hasSubItems = item.subItems && item.subItems.length > 0;

                // AI Analysis uses Collapsible
                if (hasSubItems) {
                  return (
                    <Collapsible
                      key={item.href}
                      open={aiAnalysisOpen}
                      onOpenChange={setAiAnalysisOpen}
                      className="group/collapsible"
                    >
                      <SidebarMenuItem>
                        <CollapsibleTrigger asChild>
                          <SidebarMenuButton
                            isActive={active}
                            tooltip={item.label}
                            className={cn(
                              'rounded-xl transition-all duration-200 ease-out',
                              'hover:scale-[1.02] hover:shadow-[0_0_12px_rgba(167,243,208,0.1)]',
                              active && 'bg-sidebar-accent text-foreground',
                              !active && 'text-muted-foreground hover:bg-sidebar-accent/50'
                            )}
                          >
                            <item.icon className="h-5 w-5" />
                            <span>{item.label}</span>
                            <ChevronDown className="ml-auto h-4 w-4 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-180" />
                          </SidebarMenuButton>
                        </CollapsibleTrigger>

                        {/* AI Analysis Sub-items with fall-down animation */}
                        <CollapsibleContent>
                          <AnimatePresence>
                            {aiAnalysisOpen && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.2, ease: 'easeOut' }}
                                className="overflow-hidden"
                              >
                                <SidebarMenuSub className="border-border">
                                  {item.subItems!.map((sub, index) => {
                                    const subActive = isSubActive(sub.href);
                                    return (
                                      <motion.div
                                        key={sub.href}
                                        initial={{ opacity: 0, y: -8 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{
                                          duration: 0.15,
                                          delay: index * 0.05,
                                          ease: 'easeOut',
                                        }}
                                      >
                                        <SidebarMenuSubItem>
                                          <SidebarMenuSubButton
                                            asChild
                                            isActive={subActive}
                                            className={cn(
                                              'rounded-lg transition-all duration-200',
                                              'hover:scale-[1.01] hover:shadow-[0_0_8px_rgba(167,243,208,0.08)]',
                                              subActive && 'bg-sidebar-accent text-primary',
                                              !subActive && 'text-muted-foreground hover:text-foreground'
                                            )}
                                          >
                                            <Link href={sub.href}>
                                              <sub.icon className="h-4 w-4" />
                                              <span>{sub.label}</span>
                                            </Link>
                                          </SidebarMenuSubButton>
                                        </SidebarMenuSubItem>
                                      </motion.div>
                                    );
                                  })}
                                </SidebarMenuSub>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </CollapsibleContent>
                      </SidebarMenuItem>
                    </Collapsible>
                  );
                }

                // Regular nav items (no sub-items)
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      asChild
                      isActive={active}
                      tooltip={item.label}
                      className={cn(
                        'rounded-xl transition-all duration-200 ease-out',
                        'hover:scale-[1.02] hover:shadow-[0_0_12px_rgba(167,243,208,0.1)]',
                        active && 'bg-sidebar-accent text-foreground',
                        !active && 'text-muted-foreground hover:bg-sidebar-accent/50'
                      )}
                    >
                      <Link href={item.href}>
                        <item.icon className="h-5 w-5" />
                        <span>{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* Footer */}
      <SidebarFooter className="p-3 space-y-1">
        {/* Notifications */}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Notifications"
              className={cn(
                'rounded-xl transition-all duration-200 ease-out',
                'hover:scale-[1.02] hover:shadow-[0_0_12px_rgba(167,243,208,0.1)]',
                'text-muted-foreground hover:bg-sidebar-accent/50'
              )}
            >
              <div className="relative">
                <Bell className="h-5 w-5" />
                <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-primary" />
              </div>
              <span>Notifications</span>
            </SidebarMenuButton>
          </SidebarMenuItem>

          {/* Settings */}
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Settings"
              className={cn(
                'rounded-xl transition-all duration-200 ease-out',
                'hover:scale-[1.02] hover:shadow-[0_0_12px_rgba(167,243,208,0.1)]',
                'text-muted-foreground hover:bg-sidebar-accent/50'
              )}
            >
              <Settings className="h-5 w-5" />
              <span>Settings</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
