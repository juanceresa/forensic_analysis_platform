interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-slate-900 border border-slate-800 rounded p-6 ${className}`}>
      {children}
    </div>
  );
}
