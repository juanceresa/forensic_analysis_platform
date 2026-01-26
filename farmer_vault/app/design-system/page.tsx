import { Card, VerificationBadge } from '@/components/shared';

export default function DesignSystemPage() {
  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <header className="mb-12">
          <h1 className="text-4xl font-mono mb-2">Design System</h1>
          <p className="text-slate-400">
            Civic Table - Forensic Intelligence Platform
          </p>
        </header>

        {/* Typography */}
        <section>
          <h2 className="text-2xl font-mono mb-6 uppercase tracking-wider text-slate-300">
            Typography
          </h2>
          <Card className="space-y-4">
            <div>
              <p className="text-xs text-slate-500 font-mono uppercase tracking-wider mb-2">
                Display Font (IBM Plex Mono)
              </p>
              <h1 className="text-4xl">The quick brown fox</h1>
              <h2 className="text-3xl">The quick brown fox</h2>
              <h3 className="text-2xl">The quick brown fox</h3>
            </div>
            <div>
              <p className="text-xs text-slate-500 font-mono uppercase tracking-wider mb-2">
                Body Font (Inter)
              </p>
              <p className="text-base">
                The quick brown fox jumps over the lazy dog. This is the body text
                font used throughout the application for readable content.
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500 font-mono uppercase tracking-wider mb-2">
                Mono Font (JetBrains Mono) - Tabular Numbers
              </p>
              <code className="text-base font-mono">
                1234567890 ABCDEFGHIJKLMNOPQRSTUVWXYZ
              </code>
              <div className="mt-2 font-mono tabular-nums space-y-1">
                <div>100.00</div>
                <div>  1.23</div>
                <div> 45.67</div>
              </div>
            </div>
          </Card>
        </section>

        {/* Colors */}
        <section>
          <h2 className="text-2xl font-mono mb-6 uppercase tracking-wider text-slate-300">
            Colors
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <h3 className="text-sm font-mono uppercase tracking-wider text-slate-400 mb-4">
                Background Colors
              </h3>
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-slate-950 border border-slate-700 rounded" />
                  <div>
                    <p className="text-sm font-mono">slate-950</p>
                    <p className="text-xs text-slate-400">#020617</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-slate-900 border border-slate-700 rounded" />
                  <div>
                    <p className="text-sm font-mono">slate-900</p>
                    <p className="text-xs text-slate-400">#0f172a</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-slate-800 border border-slate-700 rounded" />
                  <div>
                    <p className="text-sm font-mono">slate-800</p>
                    <p className="text-xs text-slate-400">#1e293b</p>
                  </div>
                </div>
              </div>
            </Card>

            <Card>
              <h3 className="text-sm font-mono uppercase tracking-wider text-slate-400 mb-4">
                Text Colors
              </h3>
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-slate-100 border border-slate-700 rounded" />
                  <div>
                    <p className="text-sm font-mono">slate-100</p>
                    <p className="text-xs text-slate-400">Primary text</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-slate-400 border border-slate-700 rounded" />
                  <div>
                    <p className="text-sm font-mono">slate-400</p>
                    <p className="text-xs text-slate-400">Muted text</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-slate-500 border border-slate-700 rounded" />
                  <div>
                    <p className="text-sm font-mono">slate-500</p>
                    <p className="text-xs text-slate-400">Disabled text</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </section>

        {/* Verification Badges */}
        <section>
          <h2 className="text-2xl font-mono mb-6 uppercase tracking-wider text-slate-300">
            Verification Tiers
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <h3 className="text-sm font-mono uppercase tracking-wider text-slate-400 mb-4">
                Badge Sizes
              </h3>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <VerificationBadge tier="TIER_3_AI" size="tiny" />
                  <span className="text-sm text-slate-400">Tiny</span>
                </div>
                <div className="flex items-center gap-3">
                  <VerificationBadge tier="TIER_3_AI" size="small" />
                  <span className="text-sm text-slate-400">Small</span>
                </div>
                <div className="flex items-center gap-3">
                  <VerificationBadge tier="TIER_3_AI" size="medium" />
                  <span className="text-sm text-slate-400">Medium (default)</span>
                </div>
                <div className="flex items-center gap-3">
                  <VerificationBadge tier="TIER_3_AI" size="large" />
                  <span className="text-sm text-slate-400">Large</span>
                </div>
              </div>
            </Card>

            <Card>
              <h3 className="text-sm font-mono uppercase tracking-wider text-slate-400 mb-4">
                Tier Variants
              </h3>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <VerificationBadge tier="TIER_3_AI" />
                  <span className="text-sm text-slate-400">AI - Unverified</span>
                </div>
                <div className="flex items-center gap-3">
                  <VerificationBadge tier="TIER_2_ANALYST" />
                  <span className="text-sm text-slate-400">Analyst - Reviewed</span>
                </div>
                <div className="flex items-center gap-3">
                  <VerificationBadge tier="TIER_1_CERTIFIED" />
                  <span className="text-sm text-slate-400">Certified - Legal</span>
                </div>
                <div className="flex items-center gap-3">
                  <VerificationBadge tier="TIER_4_SOURCE" />
                  <span className="text-sm text-slate-400">Source - Original</span>
                </div>
              </div>
            </Card>
          </div>
        </section>

        {/* Cards */}
        <section>
          <h2 className="text-2xl font-mono mb-6 uppercase tracking-wider text-slate-300">
            Card Component
          </h2>
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">
                Documents
              </div>
              <div className="mt-2 text-4xl font-mono tabular-nums">18</div>
              <div className="mt-3 text-xs text-blue-400">View all →</div>
            </Card>

            <Card>
              <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">
                Entities
              </div>
              <div className="mt-2 text-4xl font-mono tabular-nums">87</div>
              <div className="mt-3 text-xs text-blue-400">View all →</div>
            </Card>

            <Card>
              <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">
                Relationships
              </div>
              <div className="mt-2 text-4xl font-mono tabular-nums">142</div>
              <div className="mt-3 text-xs text-blue-400">View all →</div>
            </Card>
          </div>
        </section>

        {/* Animations */}
        <section>
          <h2 className="text-2xl font-mono mb-6 uppercase tracking-wider text-slate-300">
            Animations
          </h2>
          <Card>
            <p className="text-sm text-slate-400 mb-4">
              Staggered fade-in animation (refresh page to see)
            </p>
            <div className="space-y-2">
              <div className="p-4 bg-slate-800 rounded animate-fade-in-up stagger-delay-1">
                Item 1
              </div>
              <div className="p-4 bg-slate-800 rounded animate-fade-in-up stagger-delay-2">
                Item 2
              </div>
              <div className="p-4 bg-slate-800 rounded animate-fade-in-up stagger-delay-3">
                Item 3
              </div>
              <div className="p-4 bg-slate-800 rounded animate-fade-in-up stagger-delay-4">
                Item 4
              </div>
            </div>
          </Card>
        </section>
      </div>
    </div>
  );
}
