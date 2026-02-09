# Demo Case Package

This folder contains a fully synthetic case package for public demos.

- Case ID: `DEMO-SYNTHETIC`
- Contains only fabricated names, entities, and facts
- Intended for UI walkthroughs and architecture demonstrations

## Install Into Local `cases/`

From repository root:

```bash
bash scripts/install_demo_case.sh
```

The installer creates:

`cases/DEMO-SYNTHETIC`

and writes a tiny placeholder intake image (`Demo Deed.png`) so document preview routes resolve cleanly.

## Safety

- No client files are included here.
- No personally identifying real case data is included.
- Keep real case data under your private local `cases/` directory only.
