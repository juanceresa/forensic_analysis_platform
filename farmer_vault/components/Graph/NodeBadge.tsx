import type { VerificationTier } from '@/lib/types';

interface NodeBadgeProps {
  tier: VerificationTier;
  className?: string;
}

export function NodeBadge({ tier, className = '' }: NodeBadgeProps) {
  const styles = {
    TIER_1_CERTIFIED: {
      bg: 'bg-cyan-950',
      border: 'border-cyan-400',
      text: 'text-cyan-300',
      stamp: '✓ CERTIFIED',
      rotate: '-rotate-2',
      glow: 'shadow-[0_0_10px_rgba(6,182,212,0.4)]',
    },
    TIER_2_INSTITUTIONAL: {
      bg: 'bg-purple-950',
      border: 'border-purple-500',
      text: 'text-purple-300',
      stamp: '⚠ INSTITUTIONAL',
      rotate: 'rotate-1',
      glow: 'shadow-[0_0_10px_rgba(139,92,246,0.4)]',
    },
    TIER_2_ANALYST: {
      bg: 'bg-blue-950',
      border: 'border-blue-400',
      text: 'text-blue-300',
      stamp: '✓ ANALYST',
      rotate: '-rotate-1',
      glow: 'shadow-[0_0_10px_rgba(59,130,246,0.4)]',
    },
    TIER_3_AI: {
      bg: 'bg-slate-900',
      border: 'border-slate-600',
      text: 'text-slate-400',
      stamp: '⚠ UNVERIFIED',
      rotate: 'rotate-2',
      glow: '',
    },
  };

  const style = styles[tier];

  return (
    <div className={`relative ${className}`}>
      {/* Evidence stamp effect */}
      <div
        className={`
          inline-block px-3 py-1.5
          ${style.bg} ${style.text}
          border-2 ${style.border} ${style.rotate} ${style.glow}
          font-mono text-[10px] font-black uppercase tracking-wider
          shadow-lg transition-all
        `}
        role="status"
        aria-label={`Verification tier: ${tier}`}
      >
        {style.stamp}
      </div>
    </div>
  );
}
