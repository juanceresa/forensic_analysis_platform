import { type ReactNode } from 'react';

interface PlaceholderSectionProps {
  title: string;
  description: string;
  icon: ReactNode;
}

export default function PlaceholderSection({ title, description, icon }: PlaceholderSectionProps) {
  return (
    <section className="min-h-[40vh] flex items-center justify-center px-4 sm:px-8 border-t border-border/50">
      <div className="text-center space-y-4 max-w-md">
        <div className="mx-auto w-16 h-16 rounded-full bg-muted/50 border border-border flex items-center justify-center">
          {icon}
        </div>
        <h2 className="font-display text-xl text-muted-foreground tracking-tight">{title}</h2>
        <p className="font-mono text-xs uppercase tracking-[0.15em] text-muted-foreground/60">
          Coming Soon
        </p>
        <p className="text-muted-foreground/60 text-sm leading-relaxed">
          {description}
        </p>
      </div>
    </section>
  );
}
