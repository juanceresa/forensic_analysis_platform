import type { VerificationTier } from '@/lib/types';

interface NodeBadgeProps {
  tier: VerificationTier;
  className?: string;
}

export function NodeBadge({ tier, className = '' }: NodeBadgeProps) {
  const styles = {
    TIER_1_CERTIFIED: {
      bg: 'bg-blue-950',
      border: 'border-blue-400',
      text: 'text-blue-300',
      stamp: '✓ CERTIFIED',
      rotate: '-rotate-2',
    },
    TIER_2_INSTITUTIONAL: {
      bg: 'bg-amber-950',
      border: 'border-amber-600',
      text: 'text-amber-400',
      stamp: '⚠ INSTITUTIONAL',
      rotate: 'rotate-1',
    },
    TIER_2_ANALYST: {
      bg: 'bg-amber-950',
      border: 'border-amber-500',
      text: 'text-amber-300',
      stamp: '✓ ANALYST',
      rotate: '-rotate-1',
    },
    TIER_3_AI: {
      bg: 'bg-gray-950',
      border: 'border-gray-600',
      text: 'text-gray-400',
      stamp: '⚠ UNVERIFIED',
      rotate: 'rotate-2',
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
          border-2 ${style.border} ${style.rotate}
          font-mono text-[10px] font-black uppercase tracking-wider
          shadow-lg
        `}
        role="status"
        aria-label={`Verification tier: ${tier}`}
      >
        {style.stamp}
      </div>
    </div>
  );
}
