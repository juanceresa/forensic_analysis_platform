# Property Geolocation Module — Lightweight Design

> **Document Type:** Technical Design (Lightweight)
> **Date:** January 27, 2026
> **Status:** Planned (Future Enhancement)
> **Priority:** After Phase 8A.2 (Dossier Module)

---

## Purpose

Generate map images showing exact property boundaries and location for inclusion in forensic dossiers. Visual evidence of "this is exactly what was taken."

---

## Why Separate Module

- **Dossier independence** — Dossier generates without maps; maps are optional enhancement
- **Different concerns** — API calls, caching, rate limits vs. document rendering
- **Testable isolation** — Can develop/test without touching dossier code
- **Backend logging** — All geolocation requests must be auditable

---

## Module Location

```
farmer_factory/geolocation/
├── __init__.py         # Public API: generate_property_map()
├── models.py           # GeolocationResult, PropertyBounds, MapRequest
├── geocoder.py         # Address → coordinates
├── renderer.py         # Coordinates + bounds → static map image
├── cache.py            # Avoid redundant API calls
└── logging.py          # Audit trail for all requests
```

---

## Data Flow

```
PropertyData (from graph)
    │
    ├── address: "Aguilera 100, Holguín, Oriente"
    ├── cadastral_info: "Folio 234, Tomo 12"
    ├── area: 500
    └── area_unit: "hectares"
        │
        ▼
┌─────────────────┐
│   geocoder.py   │ ──→ Mapping API (Mapbox/Google/OSM)
└─────────────────┘
        │
        ▼
    Coordinates (lat, lng) + confidence
        │
        ▼
┌─────────────────┐
│   renderer.py   │ ──→ Static Maps API
└─────────────────┘
        │
        ▼
    PNG image saved to cases/{case_id}/output/maps/{property_id}.png
        │
        ▼
    Path returned → DossierData.property.map_image_path
```

---

## Key Technical Challenges

### 1. Historical Cuban Addresses
- Modern geocoding APIs may not recognize 1950s address formats
- Province names changed (Oriente → split into multiple provinces)
- Street names may have changed post-revolution

**Potential approaches:**
- Fuzzy matching with modern addresses
- Historical map overlays
- Manual coordinate entry as fallback
- Cadastral record cross-reference

### 2. Property Boundaries
- Need more than a point — need the actual property outline
- Sources: `area` field (size), `cadastral_info`, registry records
- May need to approximate rectangle/polygon from area + location

**Potential approaches:**
- Simple: Pin marker only (no boundary)
- Medium: Approximate rectangle based on area
- Full: Actual boundary from cadastral data (if available)

### 3. API Selection

| API | Pros | Cons |
|-----|------|------|
| **Mapbox Static** | Good customization, reasonable pricing | Requires account |
| **Google Static Maps** | Best geocoding, familiar | Higher cost, usage limits |
| **OpenStreetMap + Nominatim** | Free, open | Less accurate for Cuba |
| **Manual/Offline** | No API dependency | Requires historical map data |

**Decision:** Defer until implementation. Design should support swappable backends.

---

## Backend Logging Requirement

Every geolocation request must be logged for audit:

```python
class MapRequest(BaseModel):
    request_id: str
    case_id: str
    property_id: str
    input_address: str
    timestamp: datetime

class MapResult(BaseModel):
    request_id: str
    success: bool
    coordinates: tuple[float, float] | None
    confidence: float
    api_used: str
    map_path: str | None
    error_message: str | None
    processing_time_ms: int
```

Logs stored in: `cases/{case_id}/output/geolocation_log.jsonl`

---

## Dossier Integration

Templates check for map availability:

```latex
<% if d.property.map_image_path %>
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{<< d.property.map_image_path >>}
\caption{Property location: << d.property.address | latex_escape >>}
\end{figure}
<% else %>
\textit{Map not available. Property located at: << d.property.location_description | latex_escape >>}
<% endif %>
```

---

## CLI Interface

```bash
# Generate map for specific property
python cli.py generate-map CASE-ID --property-id "property_abc123"

# Generate maps for all properties in case
python cli.py generate-map CASE-ID --all

# Options
--api mapbox|google|osm    # Select API backend
--force                    # Regenerate even if cached
--dry-run                  # Show what would be geocoded without calling API
```

---

## Success Criteria

- [ ] Geocodes Cuban addresses with reasonable accuracy
- [ ] Generates static map images (PNG)
- [ ] All requests logged for audit
- [ ] Caching prevents redundant API calls
- [ ] Dossier includes maps when available
- [ ] Graceful degradation when geocoding fails
- [ ] Swappable API backends

---

## Open Questions (Resolve at Implementation)

1. **Which API to use primarily?** — Need to test accuracy on Cuban addresses
2. **How to handle boundary rendering?** — Start with pin only, add boundaries later?
3. **Historical map data sources?** — Any available for 1950s Cuba?
4. **Offline fallback?** — Manual coordinate entry UI needed?

---

## Dependencies

**Python packages (tentative):**
- `httpx` — API calls
- `geopy` — Geocoding abstraction (supports multiple backends)
- `Pillow` — Image processing if needed

**External:**
- Mapping API account (Mapbox, Google, or similar)

---

## Implementation Order (When Ready)

1. `models.py` — Define request/result models
2. `logging.py` — Audit logging infrastructure
3. `cache.py` — Simple file-based cache
4. `geocoder.py` — Start with one API, test on Cuban addresses
5. `renderer.py` — Generate static map images
6. `__init__.py` — Public API
7. CLI integration
8. Dossier template update (conditional map inclusion)

---

*Lightweight design — full technical detail at implementation time*
