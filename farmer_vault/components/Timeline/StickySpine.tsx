'use client';

/**
 * Renders the animated gradient vertical line that stays in viewport.
 * Year markers are now rendered inline with content in ScrollTimeline
 * so they always align with their events.
 */
export default function StickySpine() {
  return (
    <div className="sticky top-0 h-screen w-12 flex flex-col items-center py-8 z-10 pointer-events-none select-none">
      {/* Animated gradient line overlay — viewport portion of the timeline spine */}
      <div className="absolute inset-y-8 left-1/2 w-px bg-gradient-to-b from-transparent via-slate-700/50 to-transparent animate-spine-draw" />
    </div>
  );
}
