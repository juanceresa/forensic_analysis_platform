# Dashboard shadcn/ui Migration Design

> **Date:** 2026-02-04
> **Status:** Approved
> **Scope:** Dashboard page first, then full Vault migration

---

## Overview

Migrate the Farmer Vault dashboard from custom inline-styled components to shadcn/ui for:
- Premium feel and smoothness
- High-tech forensic intelligence aesthetic (Palantir-inspired)
- Maintainability via well-supported component library
- Foundation for full Vault migration

---

## Design Direction

**Visual Identity:** Dark Editorial + Forensic Intelligence
- Keep #0D0D0D/#161616/#222222 palette
- Mint glow accents for primary actions
- High-tech, data-rich interface feel
- Animated metrics, live indicators, micro-interactions everywhere

---

## Section 1: Theme Foundation

### CSS Variables

Customize shadcn's CSS variables in `globals.css` to implement Dark Editorial.

**Note:** The codebase uses `oklch()` format (Tailwind v4). Values below are converted accordingly.

Update the `.dark` selector in `globals.css`:

```css
.dark {
  /* Dark Editorial palette - deeper blacks than shadcn defaults */
  --background: oklch(0.035 0 0);    /* #0D0D0D - near black */
  --foreground: oklch(0.93 0.01 250); /* slate-100 text */

  --card: oklch(0.065 0 0);          /* #161616 - panel surface */
  --card-foreground: oklch(0.93 0.01 250);

  --muted: oklch(0.10 0 0);          /* #222222 - borders/dividers */
  --muted-foreground: oklch(0.55 0.01 250);

  --border: oklch(0.10 0 0);         /* #222222 */

  /* Primary = Mint accent (already exists as --color-tier-certified) */
  --primary: oklch(0.85 0.15 160);   /* Mint #A7F3D0 */
  --primary-foreground: oklch(0.15 0 0);
}
```

**Existing tier colors** are already defined in `@theme inline` block:
- `--color-tier-ai`, `--color-tier-analyst`, `--color-tier-certified`, `--color-tier-source`
- Background/border/text variants for each tier

No changes needed to tier colors — they align with the design.

### Glow Utilities

Add Tailwind utilities for signature glow effects:
- `shadow-glow-mint` — Primary accent glow
- `shadow-glow-blue` — Processing/analyst states
- `shadow-glow-pulse` — Animated breathing glow for live indicators

---

## Section 2: Dashboard Layout & Hero

### Hero Section

- **Ambient background** — Grayscale image with gradient overlay, extracted to `AmbientHero` component
- **Badge cluster** — shadcn `Badge` for "Case File" tag and date range
- **Stat pills** — Document/entity/relationship counts with `HoverCard` for details on hover

### Animated Numbers

`<AnimatedNumber value={123} />` component:
- Numbers count up from 0 on initial render (600ms, ease-out)
- Stagger delay between metrics (100ms offset)
- `tabular-nums` for stable widths during animation
- Uses `framer-motion` for animation

### Layout Structure

```
┌─────────────────────────────────────────────┐
│  AmbientHero                                │
│  ┌─────┐ ┌──────────┐                       │
│  │Badge│ │Date Range│                       │
│  └─────┘ └──────────┘                       │
│  CASE-ID-001                    [pulse dot] │
│  ┌────┐ ┌────┐ ┌────┐                       │
│  │ 12 │ │ 47 │ │ 89 │  ← animated counts    │
│  │docs│ │ent │ │rel │     with hover cards  │
│  └────┘ └────┘ └────┘                       │
└─────────────────────────────────────────────┘
```

---

## Section 3: Metrics Cards Grid

### Card Structure

Use shadcn `Card`, `CardHeader`, `CardContent`, `CardFooter`:
- **Header** — Muted uppercase label + optional `Tooltip`
- **Content** — Large `AnimatedNumber`
- **Footer** — Contextual link or secondary info

### Four-Card Grid

| Card | Content | Interactions |
|------|---------|--------------|
| **Current Stage** | Stage name + `Progress` bar | Tooltip shows stage description |
| **Documents** | Count + "View all →" | Click navigates, hover shows `HoverCard` with recent docs |
| **Entities** | Count + type breakdown | Hover shows mini-chart of entity types |
| **Relationships** | Count + "View graph →" | Hover shows density indicator |

### Progress Bar Enhancement

- shadcn `Progress` with `shadow-glow-blue` on indicator
- Animate width on load
- Percentage in `Tooltip` on hover

### Hover States

All cards:
- `transition-all duration-200`
- `hover:border-primary/30 hover:shadow-glow-mint/10`
- `hover:scale-[1.01]`

---

## Section 4: Verification Status with Chart

### Donut Chart

Replace stacked progress bar with a donut chart using the existing `chart.tsx` component.

**Note:** `recharts` is already installed. The shadcn `chart.tsx` provides a `ChartContainer` wrapper with theming support. We'll use `PieChart` from Recharts directly within the container.
- Center shows total entity count
- Tier segments with glow on hover
- Horizontal legend using `Badge` components

```
        ┌─────────────┐
       /   ┌─────┐     \
      │    │ 47  │      │
      │    │total│      │
       \   └─────┘     /
        └─────────────┘

   🟡 AI: 28    🔵 Analyst: 12    🟢 Certified: 5    🟣 Source: 2
```

### Interactions

- Hover segment → Tooltip with exact count/percentage
- Hover segment → 2px outward translate
- Legend badges clickable (future: filter by tier)

### Live Indicator

Pulsing dot next to header when TIER_3_AI entities exist:
- `animate-pulse` with mint/amber color
- Tooltip: "N entities awaiting analyst review"

---

## Section 5: Workflow Checklist

### Keep Existing Structure

Maintain current layout, swap to shadcn components:

```
┌───────────────────────────────────────────────────────────────────┐
│ STAGE              PROGRESS         TASKS      STATUS             │
├───────────────────────────────────────────────────────────────────┤
│ ▷ Intake           ████████████     3/3        ✓ Done             │
│ ∨ Processing       ████████████     3/3        ✓ Done             │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │ TASK                                          REVIEWER      │ │
│   ├─────────────────────────────────────────────────────────────┤ │
│   │ ☑ OCR extraction complete                     J. Ceresa     │ │
│   │ ☑ Entity extraction complete                  J. Ceresa     │ │
│   │ ☑ Graph construction complete                 —             │ │
│   └─────────────────────────────────────────────────────────────┘ │
│ ∨ Analysis         ░░░░░░░░░░░░     0/3        Pending            │
│ ∨ Certification    ░░░░░░░░░░░░     0/3        Pending            │
└───────────────────────────────────────────────────────────────────┘
```

### Component Swaps

| Current | → shadcn |
|---------|----------|
| `<details>/<summary>` | `Collapsible` + `CollapsibleTrigger` + `CollapsibleContent` |
| Inline progress bar | `Progress` with glow styling |
| Inline status span | `Badge` (Done/In Progress/Pending variants) |
| Custom checkbox div | `Checkbox` (read-only) |
| Grid layout | `Table` for alignment |

### Expanded Row — Reviewer Column

When stage is expanded, show task rows with:
- Checkbox (visual state)
- Task name
- Reviewer (Avatar + name, or "Unassigned" / em-dash)

### Dossier Download Footer

Keep at bottom, style button with:
- `variant="outline"` with mint border
- Download icon

### Data Requirements

**Current API response** (`/api/cases/[caseId]/dashboard`):
- `workflowStages` includes `items[]` with `label` and `complete` boolean
- Does NOT include reviewer assignment per task

**Reviewer column approach:**
1. **Phase 1 (this migration):** Display read-only, show "—" for all tasks (data not yet available)
2. **Phase 2 (future):** Extend API to include `reviewer` field per task item

This keeps the migration focused on UI while preparing the column for future data.

**State management:**
- WorkflowTable is **read-only display** — no task completion toggling
- Collapsible state managed client-side (component state)
- Requires `"use client"` directive for interactivity

---

## Section 6: Micro-interactions & Animations

### Animated Numbers

- `framer-motion` counter 0 → value on mount
- Duration: 600ms, `easeOut`
- Stagger: 100ms between cards
- Trigger: `whileInView`

### Live Status Indicators

```css
.pulse-live {
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.4; box-shadow: 0 0 4px var(--primary); }
  50% { opacity: 1; box-shadow: 0 0 12px var(--primary); }
}
```

### Hover Transitions

Global consistency:
- `transition-all duration-200 ease-out`
- Cards: `hover:scale-[1.01] hover:border-primary/20`
- Buttons: `hover:shadow-glow-mint`
- Table rows: `hover:bg-muted/50`

### Skeleton Loaders

shadcn `Skeleton` for loading states:
- Match content dimensions
- Show for metrics, chart, table during fetch

### Reduced Motion

Respect `prefers-reduced-motion`:
- Skip number animations
- Disable pulse effects
- Keep hover states, remove transforms

---

## Section 7: File Structure

### New/Modified Files

```
farmer_vault/
├── app/
│   └── globals.css                    # Dark Editorial CSS variables
│
├── components/
│   ├── ui/                            # shadcn components
│   │   ├── card.tsx                   # ✓ exists
│   │   ├── progress.tsx               # ✓ exists
│   │   ├── badge.tsx                  # ✓ exists
│   │   ├── collapsible.tsx            # ✓ exists
│   │   ├── table.tsx                  # ⊕ ADD
│   │   ├── checkbox.tsx               # ⊕ ADD
│   │   └── chart.tsx                  # ✓ exists
│   │
│   └── Dashboard/
│       ├── index.ts                   # Re-exports
│       ├── AmbientHero.tsx            # ⊕ NEW
│       ├── AnimatedNumber.tsx         # ⊕ NEW
│       ├── MetricCard.tsx             # ⊕ NEW
│       ├── VerificationChart.tsx      # ⊕ NEW
│       ├── WorkflowTable.tsx          # ⊕ NEW
│       └── DossierDownload.tsx        # ✓ exists (styling updates)
```

### Dependencies

**Install commands:**
```bash
# Animation library for AnimatedNumber
npm install framer-motion

# shadcn components (table already includes checkbox dependency)
npx shadcn@latest add table checkbox
```

**Bundle note:** `framer-motion` adds ~30KB gzipped. If bundle size becomes a concern, consider `use-count-up` (~2KB) as a lighter alternative for number animation only.

---

## Section 8: Cleanup

### Code to Remove After Migration

| File | Action |
|------|--------|
| `app/case/[caseId]/page.tsx` | Remove inline `WorkflowChecklist` (~160 lines), `TIER_COLORS`, inline `style={{}}` |
| `components/shared/Card.tsx` | Deprecate or redirect to shadcn Card |
| `globals.css` | Remove redundant `.de-*` classes if fully replaced |

### Validation Before Cleanup

- Grep for imports of old Card from `@/components/shared`
- Ensure no other pages depend on inline patterns
- Full Vault build to catch breaks

---

## Implementation Order

1. **Dependencies & Setup**
   ```bash
   cd farmer_vault
   npm install framer-motion
   npx shadcn@latest add table checkbox
   mkdir -p components/Dashboard
   ```

2. **Update `globals.css`** with Dark Editorial CSS variables (oklch format)

3. **Create component directory structure**
   - `components/Dashboard/index.ts` — Re-exports
   - Ensures clean import paths: `import { MetricCard } from '@/components/Dashboard'`

4. **Build Dashboard components** (order by dependency):
   - `AnimatedNumber.tsx` — No dependencies, pure animation
   - `AmbientHero.tsx` — Uses Badge from shadcn
   - `MetricCard.tsx` — Uses Card, Progress, Tooltip, HoverCard, AnimatedNumber
   - `VerificationChart.tsx` — Uses Chart, Badge
   - `WorkflowTable.tsx` — Uses Table, Collapsible, Progress, Badge, Checkbox

5. **Refactor `page.tsx`** to use new components

6. **Test all interactions**
   - Verify animations respect `prefers-reduced-motion`
   - Check hover states, tooltips, collapsible behavior
   - Run `npm run build` to catch SSR issues

7. **Cleanup old code**
   - Remove inline `WorkflowChecklist` function
   - Remove `TIER_COLORS` constant (use CSS variables)
   - Grep for old Card imports, update as needed

8. **Document patterns** for Vault-wide migration

---

## Future: Full Vault Migration

After dashboard validation, apply same patterns to:
- Document list page
- Entity detail pages
- Graph visualization
- Timeline components
- Sidebar/Header navigation

Use dashboard as reference implementation for consistent styling across Vault.
