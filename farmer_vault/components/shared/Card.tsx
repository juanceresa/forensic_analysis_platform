interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div
      className={`rounded-xl p-6 ${className}`}
      style={{
        backgroundColor: '#161616',
        border: '1px solid #222222',
      }}
    >
      {children}
    </div>
  );
}
