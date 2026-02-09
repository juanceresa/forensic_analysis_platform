# Contributing

Thanks for contributing.

## Development Setup

From repository root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r farmer_factory/requirements.txt
```

For frontend development:

```bash
cd farmer_vault
npm install
```

## Demo Data

Install synthetic local demo data:

```bash
bash scripts/install_demo_case.sh
```

This writes `cases/DEMO-SYNTHETIC` locally (ignored by git).

## Running

Factory CLI example:

```bash
python -m farmer_factory.cli --help
```

Vault:

```bash
cd farmer_vault
npm run dev
```

## Tests

Python tests:

```bash
pytest tests/
```

Vault tests:

```bash
cd farmer_vault
npm test
```

## Pull Requests

1. Keep changes focused.
2. Include tests when behavior changes.
3. Document user-visible changes in `README.md` or relevant docs.
4. Do not commit secrets or real case data.
