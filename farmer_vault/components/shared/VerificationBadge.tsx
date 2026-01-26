interface VerificationBadgeProps {
  tier: 'TIER_1_CERTIFIED' | 'TIER_2_ANALYST' | 'TIER_3_AI' | 'TIER_4_SOURCE';
  size?: 'tiny' | 'small' | 'medium' | 'large';
}

export function VerificationBadge({ tier, size = 'medium' }: VerificationBadgeProps) {
  const config = {
    TIER_3_AI: {
      label: 'AI',
      className: 'bg-[rgb(245_158_11_/_0.1)] text-[#fbbf24] border-[rgb(245_158_11_/_0.2)]',
    },
    TIER_2_ANALYST: {
      label: 'Analyst',
      className: 'bg-[rgb(59_130_246_/_0.1)] text-[#60a5fa] border-[rgb(59_130_246_/_0.2)]',
    },
    TIER_1_CERTIFIED: {
      label: 'Certified',
      className: 'bg-[rgb(16_185_129_/_0.1)] text-[#34d399] border-[rgb(16_185_129_/_0.2)]',
    },
    TIER_4_SOURCE: {
      label: 'Source',
      className: 'bg-[rgb(168_85_247_/_0.1)] text-[#c084fc] border-[rgb(168_85_247_/_0.2)]',
    },
  }[tier];

  const sizeClasses = {
    tiny: 'px-1.5 py-0.5 text-[10px]',
    small: 'px-2 py-0.5 text-xs',
    medium: 'px-2 py-1 text-xs',
    large: 'px-3 py-1.5 text-sm',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded font-mono uppercase tracking-wider border ${config.className} ${sizeClasses}`}
      title={tier}
    >
      {config.label}
    </span>
  );
}
