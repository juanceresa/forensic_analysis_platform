'use client';

import { useEffect, useRef, useState } from 'react';

interface StickySpineProps {
  years: number[];
}

export default function StickySpine({ years }: StickySpineProps) {
  const spineRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      if (!spineRef.current) return;
      const viewportCenter = window.innerHeight / 2;
      // Find which year marker is closest to viewport center
      const markers = spineRef.current.querySelectorAll('[data-year]');
      let closestIdx = 0;
      let closestDist = Infinity;
      markers.forEach((el, i) => {
        const rect = el.getBoundingClientRect();
        const dist = Math.abs(rect.top - viewportCenter);
        if (dist < closestDist) {
          closestDist = dist;
          closestIdx = i;
        }
      });
      setActiveIndex(closestIdx);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  if (years.length === 0) return null;

  return (
    <div
      ref={spineRef}
      className="sticky top-0 h-screen w-12 flex flex-col items-center py-8 z-10 pointer-events-none select-none"
    >
      {/* Vertical line */}
      <div className="absolute inset-y-8 left-1/2 w-px bg-gradient-to-b from-transparent via-slate-700/50 to-transparent animate-spine-draw" />

      {/* Year markers */}
      <div className="relative flex flex-col justify-between h-full">
        {years.map((year, i) => (
          <div
            key={year}
            data-year={year}
            data-active={i === activeIndex}
            className="spine-year-marker font-mono text-[9px] tabular-nums text-slate-600 -rotate-90 origin-center whitespace-nowrap"
          >
            {year}
          </div>
        ))}
      </div>
    </div>
  );
}
