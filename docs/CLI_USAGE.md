# CLI Usage Guide

> **Last Updated:** 2026-01-27

---

## Installation

### System Dependencies

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
Download poppler binaries from: https://github.com/oschwartz10612/poppler-windows/releases
Add to PATH.

### Python Dependencies

```bash
pip install -r farmer_factory/requirements.txt
```

---

## Domain Configuration

All commands support the `--domain` flag to specify which domain configuration to use. Default is `cuban_property`.

```bash
# List available domains
python -m farmer_factory.cli list-domains

# Output:
# Available Domains:
# ----------------------------------------
#   cuban_property: Cuban Property Restitution
```

See `farmer_factory/domains/README.md` for creating custom domains.

---

## Commands

### Create a New Case

```bash
python -m farmer_factory.cli create-case \
    --id CASE-CERESA \
    --name "Ceresa Family Archive" \
    --family "Ceresa" \
    --domain cuban_property
```

**Options:**
- `--id` (required): Case identifier (e.g., CASE-001)
- `--name` (required): Descriptive case name
- `--family` (required): Family name for the case
- `--domain` (optional): Domain configuration (default: cuban_property)

Creates case directory structure:
```
cases/CASE-CERESA/
  intake/          # Place PDFs here
  preprocessed/    # Auto-generated images
  extractions/     # Auto-generated JSON
  output/          # Final graph_data.json
  metadata.json    # Case information (includes domain)
```

---

### Process Documents

```bash
# Basic processing
python -m farmer_factory.cli process CASE-CERESA

# With specific domain
python -m farmer_factory.cli process CASE-CERESA --domain cuban_property

# Verbose output for debugging
python -m farmer_factory.cli process CASE-CERESA --verbose

# Process single PDF file
python -m farmer_factory.cli process CASE-CERESA --file document.pdf

# Force typed path (skip handwritten triage)
python -m farmer_factory.cli process CASE-CERESA --force-typed

# Skip graph validation (faster)
python -m farmer_factory.cli process CASE-CERESA --skip-validation
```

**Options:**
- `CASE_ID` (required): Case identifier
- `--domain` (optional): Domain configuration (default: cuban_property)
- `--verbose` (optional): Enable debug logging
- `--file` (optional): Process only this PDF from intake/
- `--force-typed` (optional): Force OCR path for all documents
- `--skip-validation` (optional): Skip graph_data.json validation

**What happens:**
1. Domain configuration loaded (entity types, relation types, prompts)
2. PDFs converted to images (300 DPI grayscale)
3. Images preprocessed (deskew, denoise)
4. Entities/relations extracted using domain-specific hints
5. Knowledge graph built with auto-deduplication
6. Graph exported to `graph_data.json`

**Output:**
```
2026-01-27 10:00:00 - Domain set to: cuban_property

[1/3] Processing 1960_Mario_Ceresa.pdf...
  Loaded 2 pages
  Page 1/2... ✓
  Page 2/2... ✓

============================================================
Processing Complete!
============================================================
Documents processed: 3
Entities extracted:  47
Entities merged:     12
Relations added:     23

Graph saved to: cases/CASE-CERESA/output/graph_data.json
```

---

### Validate Graph

```bash
python -m farmer_factory.cli validate CASE-CERESA --domain cuban_property
```

**Options:**
- `CASE_ID` (required): Case identifier
- `--domain` (optional): Domain for type validation (default: cuban_property)

Validates `graph_data.json` against schema with domain-specific entity/relation types.

---

### List Cases

```bash
python -m farmer_factory.cli list-cases
```

Shows all cases with status and domain.

---

### List Entities

```bash
# List all entities
python -m farmer_factory.cli list-entities CASE-CERESA

# Filter by type
python -m farmer_factory.cli list-entities CASE-CERESA --type PERSON
python -m farmer_factory.cli list-entities CASE-CERESA --type PROPERTY
```

**Options:**
- `CASE_ID` (required): Case identifier
- `--type` (optional): Filter by entity type (PERSON, PROPERTY, DOCUMENT, ORGANIZATION, LOCATION)

Useful for finding entity IDs for dossier generation.

---

### List Domains

```bash
python -m farmer_factory.cli list-domains
```

Shows all available domain configurations.

---

### Generate Dossier

```bash
python -m farmer_factory.cli generate-dossier CASE-CERESA \
    --property-id "property_abc123" \
    --family-member-id "person_xyz789" \
    --domain cuban_property
```

**Options:**
- `CASE_ID` (required): Case identifier
- `--property-id` (required): Entity ID of focal property
- `--family-member-id` (required): Entity ID of primary claimant
- `--domain` (optional): Domain configuration (default: cuban_property)
- `--output` (optional): Output directory
- `--engine` (optional): LaTeX engine (xelatex, pdflatex)
- `--dry-run` (optional): Generate .tex only, skip PDF compilation

---

### Train Deduplication

```bash
python -m farmer_factory.cli train-deduplication CASE-CERESA \
    --domain cuban_property \
    --entity-type PERSON \
    --num-examples 30
```

**Options:**
- `CASE_ID` (required): Case identifier
- `--domain` (optional): Domain configuration (default: cuban_property)
- `--entity-type` (optional): Train specific entity type
- `--num-examples` (optional): Examples per type (default: 30)

Interactive session for labeling entity pairs as matches or non-matches.

---

### Clean Case

```bash
python -m farmer_factory.cli clean CASE-CERESA --confirm
```

Removes all processed outputs while keeping source PDFs intact.

---

## Troubleshooting

### "poppler not found"
Install poppler (see system dependencies above).

### "Unknown domain"
```bash
# Check available domains
python -m farmer_factory.cli list-domains
```

### Processing fails on specific PDF
Check `cases/CASE-ID/processing.log` for detailed error messages.

### Low entity extraction
- Verify PDF quality (scanned vs digital)
- Check OCR confidence in extraction JSONs
- Review `processing.log` for warnings
- Ensure domain configuration matches document language

---

## File Formats

### Intermediate Outputs

**Preprocessed Images:** `cases/CASE-ID/preprocessed/{pdf_stem}_page_{n}.png`
- 300 DPI grayscale PNG
- Deskewed and denoised

**Extraction JSON:** `cases/CASE-ID/extractions/{pdf_stem}_page_{n}.json`
- Entities with TIER_3_AI verification
- Relations with confidence scores
- OCR text and metadata

### Final Output

**Graph Data:** `cases/CASE-ID/output/graph_data.json`
- Force-graph format (nodes + links)
- Entity/relation types from active domain
- Ready for frontend consumption

**Case Metadata:** `cases/CASE-ID/metadata.json`
```json
{
  "id": "CASE-CERESA",
  "name": "Ceresa Family Archive",
  "family": "Ceresa",
  "domain": "cuban_property",
  "created_at": "2026-01-27T10:00:00",
  "status": "INTAKE"
}
```

---

## Next Steps

After processing:
1. Review graph in frontend (The Vault)
2. Analyst verification (promote TIER_3_AI → TIER_2_ANALYST)
3. Generate dossier PDFs for legal submission
4. Upload to Supabase (coming soon)
