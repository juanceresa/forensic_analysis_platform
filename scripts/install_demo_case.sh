#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$ROOT_DIR/examples/demo_case/template/DEMO-SYNTHETIC"
TARGET_DIR="$ROOT_DIR/cases/DEMO-SYNTHETIC"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "Template directory not found: $TEMPLATE_DIR" >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/cases"
mkdir -p "$TARGET_DIR"

# Copy synthetic template files (extractions, OCR, output).
cp -R "$TEMPLATE_DIR"/. "$TARGET_DIR"/

# Ensure intake directory exists with a tiny placeholder image for preview routes.
mkdir -p "$TARGET_DIR/intake"
python3 - "$TARGET_DIR/intake/Demo Deed.png" <<'PY'
import base64
import pathlib
import sys

target = pathlib.Path(sys.argv[1])
png_b64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAoMBgX5f4VoAAAAASUVORK5CYII="
)
target.write_bytes(base64.b64decode(png_b64))
PY

# Minimal metadata files for local case discovery tooling.
cat > "$TARGET_DIR/metadata.json" <<'JSON'
{
  "id": "DEMO-SYNTHETIC",
  "name": "Synthetic Demo Case",
  "family": "Demo",
  "description": "Public synthetic data for repository walkthroughs.",
  "created_at": "2026-02-09T00:00:00Z"
}
JSON

cat > "$TARGET_DIR/manifest.json" <<'JSON'
{
  "case_id": "DEMO-SYNTHETIC",
  "documents": [
    {
      "id": "Demo Deed_page_0",
      "filename": "Demo Deed.png"
    }
  ]
}
JSON

echo "Installed synthetic demo case at: $TARGET_DIR"
echo "Open: /case/DEMO-SYNTHETIC"
