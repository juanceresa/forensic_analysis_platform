# CLI Usage Guide

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

## Commands

### Create a New Case

```bash
python farmer_factory/cli.py create-case --id CASE-CERESA --name "Ceresa Family Archive" --family "Ceresa"
```

Creates case directory structure:
```
cases/CASE-CERESA/
  intake/          # Place PDFs here
  preprocessed/    # Auto-generated images
  extractions/     # Auto-generated JSON
  output/          # Final graph_data.json
  metadata.json    # Case information
```

### Process Documents

```bash
# Process all PDFs in case
python farmer_factory/cli.py process CASE-CERESA

# Verbose output for debugging
python farmer_factory/cli.py process CASE-CERESA --verbose
```

**What happens:**
1. PDFs converted to images (300 DPI grayscale)
2. Images preprocessed (deskew, denoise, triage)
3. Entities/relations extracted (OCR + Vision + LLM)
4. Knowledge graph built (auto-deduplication)
5. Graph exported to `graph_data.json`

**Output:**
```
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

### List Cases

```bash
python farmer_factory/cli.py list-cases
```

Shows all cases with status.

## Troubleshooting

### "poppler not found"
Install poppler (see system dependencies above).

### Processing fails on specific PDF
Check `cases/CASE-ID/processing.log` for detailed error messages.

### Low entity extraction
- Verify PDF quality (scanned vs digital)
- Check OCR confidence in extraction JSONs
- Review `processing.log` for warnings

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
- Ready for frontend consumption
- All entities with verification tiers

## Next Steps

After processing:
1. Review graph in frontend (The Vault)
2. Analyst verification (promote TIER_3_AI → TIER_2_ANALYST)
3. Upload to Supabase (coming soon)
