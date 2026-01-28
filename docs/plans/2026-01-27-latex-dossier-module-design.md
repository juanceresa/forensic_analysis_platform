# LaTeX Dossier Module — Design Document

> **Document Type:** Technical Design
> **Date:** January 27, 2026
> **Status:** Approved for implementation

---

## Overview

**Purpose:** Generate professional PDF dossiers from case data that serve both families (understanding what they have) and lawyers (evidence-ready documentation).

**Module Location:** `farmer_factory/dossier/`

**Key Characteristics:**
- Modular sections (include/exclude per case)
- English only (MVP — Spanish as future enhancement)
- Text-only (no embedded images for MVP)
- Jinja2 templates → LaTeX → PDF via `pdflatex`
- Verification transparency via disclaimers + section-level indicators
- Dual narrative spine: Family-centric AND Property-centric

---

## Dossier Structure

```
1. FRONT MATTER
   - Executive Summary (2-paragraph claim summary, LLM-polished)
   - Disclaimer & Methodology
   - Table of Contents

2. COMPLETE TIMELINE
   - Chronological list of all events (family + property)
   - Dates, event type, summary, source document
   - Visual scan of the entire story at a glance

3. THE FAMILY
   - Family origins and lineage
   - Key figures (who owned, who inherits)
   - Family tree (text-based for MVP)

4. THE PROPERTY
   - Property description and location
   - Historical context
   - Map placeholder (optional — from geolocation module)

5. OWNERSHIP HISTORY (the narrative spine)
   - Acquisition: How the family came to own it
   - Ownership period: Key events during tenure
   - Confiscation/Loss: The taking (with evidence)

6. EVIDENCE INVENTORY
   - Document-by-document summary
   - What each document proves
   - Verification status per document

7. APPENDIX
   - Full citations
   - Methodology notes
   - Glossary (Spanish legal terms)
```

---

## Data Flow

```
KnowledgeGraph (graph_data.json)
        +
extractions/*.json (for evidence quotes)
        ↓
    DossierPreparer
        ↓
    DossierData (Pydantic model)
        ↓
    DossierRenderer (Jinja2 → .tex)
        ↓
    DossierCompiler (pdflatex → PDF)
        ↓
    {case_id}_dossier.pdf
```

**Data Sources:**
- `KnowledgeGraph` — Deduplicated entities, relationships, verification tiers
- `extractions/*.json` — Richer evidence quotes, OCR text
- `ConstellationAnalyzer` — Groups related entities (from narrative module)

---

## Module Structure

```
farmer_factory/dossier/
├── __init__.py           # Public API: generate_dossier()
├── models.py             # DossierData and section sub-models
├── preparer.py           # Assembles DossierData from case artifacts
├── renderer.py           # Jinja2 → LaTeX rendering
├── compiler.py           # pdflatex compilation
├── templates/
│   ├── main.tex.j2              # Document skeleton
│   ├── sections/
│   │   ├── front_matter.tex.j2  # Title, disclaimer, TOC
│   │   ├── timeline.tex.j2      # Chronological events table
│   │   ├── family.tex.j2        # Family tree and lineage
│   │   ├── property.tex.j2      # Property description
│   │   ├── ownership.tex.j2     # Ownership history narrative
│   │   ├── documents.tex.j2     # Evidence inventory table
│   │   └── appendix.tex.j2      # Citations, glossary
│   └── partials/
│       ├── verification_badge.tex.j2
│       ├── citation.tex.j2
│       └── event_row.tex.j2
└── styles/
    └── civictable.sty           # Custom LaTeX style
```

---

## Data Models

```python
# farmer_factory/dossier/models.py

from datetime import datetime
from pydantic import BaseModel
from farmer_factory.structure.schema import VerificationTier


class TimelineEvent(BaseModel):
    """Single event in the chronological timeline."""
    date: str | None                    # ISO date or "circa 1950s"
    date_sortable: str | None           # For ordering
    event_type: str                     # ACQUISITION, BIRTH, DEATH, CONFISCATION, etc.
    summary: str                        # One-line description
    entities_involved: list[str]        # Entity names
    source_doc_id: str | None           # Document proving this
    verification_tier: VerificationTier


class FamilyMember(BaseModel):
    """Person in the family tree."""
    entity_id: str
    name: str
    relation_to_claimant: str | None    # "grandfather", "mother", etc.
    birth_date: str | None
    death_date: str | None
    roles: list[str]                    # "owner", "heir", "witness"
    verification_tier: VerificationTier


class FamilyTreeData(BaseModel):
    """Section: The Family."""
    primary_claimant: FamilyMember
    members: list[FamilyMember]
    lineage_summary: str                # Generated narrative of family line


class PropertyData(BaseModel):
    """Section: The Property."""
    entity_id: str
    name: str | None
    property_type: str | None
    address: str | None
    location_description: str           # "Holguín, Oriente Province, Cuba"
    area: float | None
    area_unit: str | None
    registry_info: str | None           # Folio, cadastral, etc.
    description: str | None             # Historical context
    map_image_path: str | None          # Optional — from geolocation module
    verification_tier: VerificationTier


class EvidenceCitation(BaseModel):
    """Citation for a specific claim."""
    doc_id: str
    doc_title: str | None
    page: int | None
    quote: str | None
    verification_tier: VerificationTier


class OwnershipPeriod(BaseModel):
    """Single period of ownership in the chain."""
    period_type: str                    # ACQUISITION, OWNERSHIP, CONFISCATION
    start_date: str | None
    end_date: str | None
    owner_names: list[str]
    narrative: str                      # What happened during this period
    evidence: list[EvidenceCitation]    # Supporting documents


class DocumentSummary(BaseModel):
    """Single document in the evidence inventory."""
    doc_id: str
    title: str | None
    document_type: str
    date: str | None
    page_count: int
    what_it_proves: str                 # One-line summary
    key_entities: list[str]             # Entities mentioned
    verification_tier: VerificationTier
    verification_confidence: float | None  # Pass-through from graph if available
    extracted_from: list[str] | None        # Source artifacts, if known


class VerificationStats(BaseModel):
    """Aggregate verification statistics."""
    total_data_points: int
    tier_distribution: dict[str, int]   # {"TIER_3_AI": 45, "TIER_2_ANALYST": 5}
    overall_confidence: float           # Weighted average
    section_breakdown: dict[str, dict[str, int]]  # {"timeline": {"TIER_3_AI": 10, ...}, ...}


class DossierData(BaseModel):
    """Complete prepared data for dossier generation."""

    # Metadata
    case_id: str
    case_title: str                     # "Ceresa Family Property Claim"
    generated_at: datetime

    # Executive Summary (LLM-generated with template constraints)
    executive_summary: str

    # Section data
    timeline: list[TimelineEvent]
    family: FamilyTreeData
    property: PropertyData
    ownership_history: list[OwnershipPeriod]
    documents: list[DocumentSummary]

    # Verification
    verification_stats: VerificationStats
    disclaimer_text: str                # Standard legal disclaimer
```

---

## Preparer Logic

```python
# farmer_factory/dossier/preparer.py

class DossierPreparer:
    """Assembles DossierData from case artifacts."""

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.case_path = Path(f"cases/{case_id}")

    def prepare(
        self,
        focal_property_id: str,
        focal_family_member_id: str,
    ) -> DossierData:
        """
        Build complete DossierData for PDF generation.

        Args:
            focal_property_id: The property being claimed
            focal_family_member_id: Primary claimant or family representative
        """
        # 1. Load graph
        graph = KnowledgeGraph.load(self.case_path / "output/graph_data.json")
        # validate IDs exist
        self._assert_entity_exists(graph, focal_property_id, expected_type="PROPERTY")
        self._assert_entity_exists(graph, focal_family_member_id, expected_type="PERSON")

        # 2. Load extraction files (for richer evidence quotes)
        extractions = self._load_extractions()

        # 3. Build timeline (all events, sorted chronologically)
        timeline = self._build_timeline(graph)

        # 4. Build family section
        family = self._build_family_tree(graph, focal_family_member_id)

        # 5. Build property section
        property_data = self._build_property(graph, focal_property_id)

        # 6. Build ownership history (the narrative spine)
        ownership_history = self._build_ownership_chain(
            graph, extractions, focal_property_id
        )

        # 7. Build document inventory
        documents = self._build_document_inventory(graph)

        # 8. Calculate verification stats
        verification_stats = self._calculate_verification_stats(graph, timeline, ownership_history, documents)

        # 9. Generate executive summary (hybrid: template + LLM polish)
        executive_summary = self._generate_executive_summary(
            family, property_data, ownership_history
        )

        return DossierData(
            case_id=self.case_id,
            case_title=self._derive_case_title(family, property_data),
            generated_at=datetime.now(),
            executive_summary=executive_summary,
            timeline=timeline,
            family=family,
            property=property_data,
            ownership_history=ownership_history,
            documents=documents,
            verification_stats=verification_stats,
            disclaimer_text=STANDARD_DISCLAIMER,
        )
```

**Key Methods:**

| Method | Source | Logic |
|--------|--------|-------|
| `_build_timeline()` | Graph nodes + links | Extract all dated events, sort chronologically |
| `_build_family_tree()` | Person entities + relations | Traverse CHILD_OF, SPOUSE_OF links from focal person |
| `_build_property()` | Property entity | Pull fields, check for geolocation map |
| `_build_ownership_chain()` | OWNS, SOLD, INHERITED, CONFISCATED links | Group into periods with narratives |
| `_build_document_inventory()` | Document entities | Summarize what each proves |
| `_generate_executive_summary()` | Assembled sections | Template extracts facts, LLM polishes prose |

---

## Executive Summary Generation (Hybrid Approach)

```python
def _generate_executive_summary(self, family, property_data, ownership) -> str:
    """Generate 2-paragraph executive summary using template + LLM."""

    # 1. Template extracts the facts
    facts = f"""
    Family: {family.primary_claimant.name}
    Property: {property_data.name or property_data.address}
    Location: {property_data.location_description}
    Acquired: {ownership[0].start_date if ownership else 'Unknown'}
    Lost: {ownership[-1].end_date if ownership else 'Unknown'}
    Loss type: {ownership[-1].period_type if ownership else 'Unknown'}
    Document count: {len(self.documents)}
    """

    # 2. LLM polishes into prose (with strict prompt)
    prompt = f"""
    Write a 2-paragraph executive summary for a property restitution dossier.
    Use ONLY the facts provided. Do not add information or make legal conclusions.
    Do not use phrases like "strong case" or "proves ownership."

    Facts:
    {facts}

    Paragraph 1: Who the family is and what they owned.
    Paragraph 2: What happened to the property and current documentation status.
    """

    return llm_generate(prompt, model="haiku", max_tokens=350, temperature=0.3)
```

---

## Renderer

```python
# farmer_factory/dossier/renderer.py

class DossierRenderer:
    """Renders DossierData to LaTeX using Jinja2 templates."""

    TEMPLATE_DIR = Path(__file__).parent / "templates"

    def __init__(self):
        # Use custom delimiters to avoid LaTeX conflicts
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.TEMPLATE_DIR),
            block_start_string='<%',
            block_end_string='%>',
            variable_start_string='<<',
            variable_end_string='>>',
            comment_start_string='<#',
            comment_end_string='#>',
        )
        self._register_filters()

    def render(self, data: DossierData, output_dir: Path) -> Path:
        """Render DossierData to .tex file."""
        template = self.env.get_template("main.tex.j2")
        tex_content = template.render(d=data)

        output_path = output_dir / f"{data.case_id}_dossier.tex"
        output_path.write_text(tex_content)

        # Copy style file
        shutil.copy(
            self.TEMPLATE_DIR.parent / "styles/civictable.sty",
            output_dir / "civictable.sty"
        )

        return output_path

    def _register_filters(self):
        """Custom Jinja2 filters for LaTeX."""
        self.env.filters['latex_escape'] = self._latex_escape
        self.env.filters['format_date'] = self._format_date
        self.env.filters['verification_badge'] = self._verification_badge

    @staticmethod
    def _latex_escape(text: str) -> str:
        """Escape LaTeX special characters."""
        if text is None:
            return ''
        replacements = {
            '\\': r'\textbackslash{}',
            '&': r'\&', '%': r'\%', '$': r'\$',
            '#': r'\#', '_': r'\_', '{': r'\{',
            '}': r'\}', '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        # normalize newlines to LaTeX line breaks
        return text.replace('\n', r'\\')
```

---

## Compiler

```python
# farmer_factory/dossier/compiler.py

class CompilationError(Exception):
    """Raised when pdflatex fails."""
    def __init__(self, message: str, log_content: str | None = None):
        super().__init__(message)
        self.log_content = log_content


class DossierCompiler:
    """Compiles .tex files to PDF using pdflatex."""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self._verify_pdflatex()

    def _verify_pdflatex(self):
        """Check that pdflatex is available."""
        try:
            subprocess.run(["pdflatex", "--version"], capture_output=True, check=True)
        except FileNotFoundError:
            raise RuntimeError(
                "pdflatex not found. Install TeX distribution "
                "(MacTeX on macOS, TeX Live on Linux)."
            )

    def compile(self, tex_path: Path, output_dir: Path | None = None) -> Path:
        """
        Compile .tex file to PDF.
        Runs pdflatex twice to resolve references/TOC.
        """
        output_dir = output_dir or tex_path.parent
        self._assert_includes(tex_path)

        for pass_num in [1, 2]:
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory", str(output_dir),
                    str(tex_path),
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tex_path.parent,
            )

            if result.returncode != 0:
                log_path = output_dir / tex_path.with_suffix('.log').name
                log_content = log_path.read_text() if log_path.exists() else None
                raise CompilationError(
                    f"pdflatex failed on pass {pass_num}",
                    log_content=log_content,
                )

        pdf_path = output_dir / tex_path.with_suffix('.pdf').name
        if not pdf_path.exists():
            raise CompilationError(f"PDF not generated: {pdf_path}")

        self._cleanup(output_dir, tex_path.stem)
        return pdf_path

    def _cleanup(self, output_dir: Path, stem: str):
        """Remove LaTeX auxiliary files."""
        for ext in ['.aux', '.log', '.toc', '.out', '.fls', '.fdb_latexmk']:
            aux_file = output_dir / f"{stem}{ext}"
            if aux_file.exists():
                aux_file.unlink()

    def _assert_includes(self, tex_path: Path):
        """Ensure style/includes exist before compilation."""
        style_path = tex_path.parent / "civictable.sty"
        if not style_path.exists():
            raise CompilationError(f"Missing style file: {style_path}")
```

---

## Public API

```python
# farmer_factory/dossier/__init__.py

from pathlib import Path
from .preparer import DossierPreparer
from .renderer import DossierRenderer
from .compiler import DossierCompiler


def generate_dossier(
    case_id: str,
    focal_property_id: str,
    focal_family_member_id: str,
    output_dir: Path | None = None,
    engine: str = "pdflatex",  # or "xelatex" if we need UTF-8/spanish
) -> Path:
    """
    Generate PDF dossier for a case.

    Args:
        case_id: Case identifier (e.g., "TEST-CERESA")
        focal_property_id: Entity ID of the property being claimed
        focal_family_member_id: Entity ID of primary claimant
        output_dir: Output directory (defaults to cases/{case_id}/output)

    Returns:
        Path to generated PDF
    """
    output_dir = output_dir or Path(f"cases/{case_id}/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Prepare data (idempotent; rerun after graph changes)
    preparer = DossierPreparer(case_id)
    data = preparer.prepare(focal_property_id, focal_family_member_id)

    # 2. Render to LaTeX
    renderer = DossierRenderer()
    tex_path = renderer.render(data, output_dir)

    # 3. Compile to PDF
    compiler = DossierCompiler(engine=engine)
    pdf_path = compiler.compile(tex_path, output_dir)

    return pdf_path
```

---

## CLI Integration

```bash
# Add to farmer_factory/cli.py

python cli.py generate-dossier TEST-CERESA \
    --property-id "property_abc123" \
    --family-member-id "person_xyz789" \
    --output ./output/
    --engine xelatex
```

---

## Verification Handling

**Approach:** Global disclaimer + per-section indicators (hybrid)

1. **Front matter:** Prominent disclaimer about verification methodology and AI extraction
2. **Section headers:** Badge showing verification distribution (e.g., "Sources: 12 documents, 85% AI-extracted")
3. **Evidence appendix:** Full per-citation verification details for lawyers

**Standard Disclaimer:**

> This dossier was prepared using automated document analysis and AI-assisted extraction.
> All data points are classified by verification tier:
> - **TIER_3_AI**: Automatically extracted, not yet verified
> - **TIER_2_ANALYST**: Verified by trained analyst
> - **TIER_2_INSTITUTIONAL**: Verified against institutional records
> - **TIER_1_CERTIFIED**: Certified by licensed professional
>
> This document presents forensic facts, not legal conclusions.
> Consult qualified legal counsel for interpretation and strategy.

---

## Future Enhancements

### Geolocation Module (Separate)

**Location:** `farmer_factory/geolocation/`

**Purpose:** Generate map images showing exact property boundaries and location.

**Why separate module:**
- Keeps dossier module focused on document generation
- Geolocation is optional — dossier degrades gracefully without it
- Different technical concerns (API calls, map rendering, caching)
- Can be developed/tested independently

**Planned capabilities:**
1. **Geocoding** — Convert historical Cuban addresses to coordinates
2. **Boundary rendering** — Paint exact property area/boundaries on map
3. **Static map generation** — Output PNG/PDF images for dossier embedding
4. **Backend logging** — Track all geolocation requests and results

**Technical considerations:**
- Historical Cuban addresses may not exist in modern geocoding APIs
- May need cadastral records or historical maps as reference
- Possible APIs: Mapbox Static Images, Google Static Maps, OpenStreetMap
- Property boundaries from `area`, `cadastral_info`, `registry_number` fields

**Module structure (tentative):**
```
farmer_factory/geolocation/
├── __init__.py
├── models.py           # GeolocationResult, PropertyBounds
├── geocoder.py         # Address → coordinates
├── renderer.py         # Coordinates → map image
├── cache.py            # Cache geocoding results
└── logging.py          # Backend request/result logging
```

**Dossier integration:** Templates include conditional:
```latex
<% if d.property.map_image_path %>
\includegraphics[width=\textwidth]{<< d.property.map_image_path >>}
<% else %>
\textit{Map not available. See property description above.}
<% endif %>
```

**Data flow:**
```
PropertyData (address, cadastral_info, area)
        ↓
    geocoder.py → coordinates
        ↓
    renderer.py → map image (PNG)
        ↓
    Saved to cases/{case_id}/output/maps/
        ↓
    Referenced in DossierData.property.map_image_path
```

### Spanish Language Support

Future enhancement: Add `language` parameter to `generate_dossier()`, with separate Spanish templates or translation layer.

---

## Dependencies

**Python packages:**
- `jinja2` — Template rendering
- `pydantic` — Data models (already in project)

**System dependencies:**
- `pdflatex` (default) or `xelatex` for UTF-8 — install via TeX Live/MacTeX
- CI/dev: document TeX install or provide docker image with TeX preinstalled

---

## Implementation Order

1. **models.py** — Define all Pydantic models
2. **templates/** — Create LaTeX templates (start with main.tex.j2)
3. **renderer.py** — Jinja2 rendering with LaTeX escaping
4. **compiler.py** — pdflatex wrapper
5. **preparer.py** — Data assembly (most complex)
6. **CLI integration** — Add `generate-dossier` command
7. **Test with TEST-CERESA case**

---

*Design approved January 27, 2026*

## Decisions (filled)
- **Date normalization/sort:** Use `date_sortable` when provided (ISO 8601). Else try strict ISO parse on `date`. For year-only dates, normalize to `YYYY-01-01` with a `circa` flag and render label as provided (“circa 1950s”); sort by normalized date with `circa` dates ordered after exact matches within the same year.
- **Template contracts:** Document required fields per template (timeline needs `date_sortable`, `summary`, `entities_involved`; ownership needs `period_type`, `start_date`, `owner_names`, `narrative`, `evidence`; documents need `doc_id`, `what_it_proves`, `verification_tier`). Preparer must supply defaults (empty string/list) and log omissions; renderer should fail fast on missing required keys (StrictUndefined).
- **Missing data policy:** Prefer explicit placeholders (“Unknown”, “Not available”) rather than dropping rows. For optional sections (map, glossary), render conditional blocks. For critical fields (doc_id, period_type) drop the row with a log entry.
- **Encoding defaults:** Default to `xelatex` with UTF-8 and `fontspec` for safe Spanish accents later; allow `pdflatex` fallback with `inputenc`/`fontenc` if `xelatex` unavailable. Document template requirements accordingly.
