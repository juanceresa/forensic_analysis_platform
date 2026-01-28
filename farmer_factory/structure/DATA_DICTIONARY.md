# Farmer House Forensic Intelligence Platform — Data Dictionary

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.0.0
> **Last Updated:** 2026-01-21
> **Status:** Spanish Legal Terminology Reference

---

## Overview

This document provides terminology definitions, OCR error patterns, and contextual information for processing historical Cuban property documents (1940s-1960s).

**Purpose:**
- Aid LLM entity extraction with domain-specific vocabulary
- Document common OCR errors for Spanish text
- Provide historical context for ambiguous terms
- Standardize terminology across the system

---

## Spanish Legal Terminology

### Property Types

| Spanish Term | English | Description | Typical Size | Context |
|--------------|---------|-------------|--------------|---------|
| **Central** | Sugar mill | Industrial sugar processing facility with lands | 500-5,000 hectares | Primary wealth unit in pre-revolutionary Cuba |
| **Ingenio** | Sugar mill | Synonym for Central (older term) | Same as Central | Often used interchangeably with Central |
| **Colonia** | Colony | Farming community/lands within a Central | 50-500 hectares | Subordinate to a Central, provides cane |
| **Finca** | Farm/Estate | General agricultural property | 10-500 hectares | Catch-all term for rural property |
| **Hacienda** | Estate | Large agricultural estate (general) | 200-2,000 hectares | Implies wealth and status |
| **Sitio** | Plot | Small agricultural plot | 1-20 hectares | Modest rural property |
| **Estancia** | Ranch | Cattle ranch or large estate | 500-5,000 hectares | Primarily livestock |
| **Potrero** | Pasture | Grazing land | Variable | Often part of larger property |
| **Cafetal** | Coffee plantation | Plantation for coffee cultivation | 50-500 hectares | Common in mountainous regions |
| **Vegas** | Tobacco lands | Land for tobacco cultivation | 5-50 hectares | Specialized crop, valuable |
| **Solar** | Urban lot | City/town building plot | <1 hectare | Urban property |
| **Edificio** | Building | Urban building/structure | N/A | Commercial or residential urban property |

### Legal Documents

| Spanish Term | English | Purpose | Typical Signatories |
|--------------|---------|---------|---------------------|
| **Escritura** | Deed | Formal property transfer document | Notary, buyer, seller |
| **Título** | Title | Ownership title document | Registry official |
| **Testamento** | Will | Last will and testament | Testator, notary, witnesses |
| **Declaratoria de herederos** | Declaration of heirs | Legal determination of rightful heirs | Court, heirs |
| **Certificado de dominio** | Certificate of ownership | Registry-certified ownership proof | Registry official |
| **Acta notarial** | Notarial act | Notarized legal act/event | Notary, parties |
| **Poder** | Power of attorney | Legal authorization document | Grantor, attorney-in-fact, notary |
| **Hipoteca** | Mortgage | Property lien document | Lender, borrower, notary |
| **Embargo** | Lien/Seizure | Legal claim on property | Court, creditor |
| **Resolución de confiscación** | Confiscation decree | Government seizure order | Government official (INRA, etc.) |
| **Ley de Reforma Agraria** | Agrarian Reform Law | Legal basis for confiscations | Government |
| **Certificado de tradición** | Chain of title certificate | Historical ownership record | Registry official |

### Legal Roles & Titles

| Spanish Term | English | Role | Authority |
|--------------|---------|------|-----------|
| **Notario** | Notary | Certifies legal documents | Legal certification authority |
| **Registrador** | Registrar | Maintains property registry | Official record keeper |
| **Escribano** | Scribe/Notary | Older term for notary | Same as Notario |
| **Testigo** | Witness | Attests to legal act | Corroborating presence |
| **Propietario** | Owner | Property owner | Ownership rights holder |
| **Heredero** | Heir | Inheritor of estate | Inheritance rights |
| **Causante** | Decedent | Person whose death triggers inheritance | N/A (deceased) |
| **Albacea** | Executor | Estate administrator | Manages estate distribution |
| **Tutor** | Guardian | Legal guardian (minors) | Court-appointed |
| **Apoderado** | Attorney-in-fact | Agent with power of attorney | Delegated authority |
| **Interventor** | Inspector/Administrator | Government-appointed overseer | State authority |
| **Juez** | Judge | Court official | Judicial authority |

### Legal Actions

| Spanish Term | English | Meaning | Context |
|--------------|---------|---------|---------|
| **Compraventa** | Sale/Purchase | Property sale transaction | Voluntary transfer |
| **Donación** | Gift/Donation | Transfer without payment | Often family transfers |
| **Permuta** | Exchange | Property swap | Barter transaction |
| **Adjudicación** | Adjudication | Court-ordered assignment | Inheritance, debt settlement |
| **Sucesión** | Succession | Inheritance process | Death of owner |
| **Partición** | Partition | Division of estate among heirs | Multiple heirs |
| **Usufructo** | Usufruct | Right to use property | Temporary ownership rights |
| **Servidumbre** | Easement | Right of way/use | Access rights |
| **Confiscación** | Confiscation | State seizure | Revolutionary government |
| **Nacionalización** | Nationalization | State takeover | Socialist policy |
| **Intervención** | Intervention | State control/administration | Government oversight |
| **Expropiación** | Expropriation | Forced sale to state | With compensation (in theory) |
| **Inscripción** | Registration | Recording in official registry | Creates legal effect |
| **Cancelación** | Cancellation | Removal from registry | Ends legal status |

### Cuban Geographic Terms

| Spanish Term | English | Description |
|--------------|---------|-------------|
| **Provincia** | Province | Top-level administrative division (6 in 1950s) |
| **Municipio** | Municipality | County-level division |
| **Barrio** | Ward/District | Subdivision of municipality |
| **Término municipal** | Municipal district | Jurisdiction of a municipality |
| **Pueblo** | Town | Small settlement |
| **Ingenio** | Mill town | Settlement around sugar mill |
| **Batey** | Mill compound | Central living/working area of sugar mill |

### Cuban Provinces (1950s)

1. **Pinar del Río** — Western tobacco region
2. **La Habana** — Capital and surroundings
3. **Matanzas** — Sugar and agricultural
4. **Las Villas** — Central region
5. **Camagüey** — Largest province, cattle and sugar (Ceresa family location)
6. **Oriente** — Eastern region, sugar and tobacco

---

## Measurement Units

### Land Area

| Spanish Unit | Abbreviation | Metric Equivalent | Imperial Equivalent |
|--------------|--------------|-------------------|---------------------|
| **Caballería** | cab. | ~13.4 hectares | ~33.2 acres |
| **Hectárea** | ha. | 1 hectare | 2.47 acres |
| **Cordel** | — | ~0.39 hectares | ~0.97 acres |
| **Vara cuadrada** | v² | 0.698 m² | 7.5 sq ft |
| **Metro cuadrado** | m² | 1 m² | 10.76 sq ft |

**Note:** Caballería is the most common unit in Cuban property documents. Originally the amount of land a cavalry horse could patrol.

### Currency

| Term | Period | Notes |
|------|--------|-------|
| **Peso cubano** | Pre-1959 | Roughly equal to USD 1:1 |
| **Dólar** | All periods | U.S. dollar, common in valuations |
| **Centavos** | All periods | 1/100 of peso |

### Conversion Notes

When extracting measurements:
- 1 caballería ≈ 13.4 hectares (store as hectares in schema)
- If "40 caballerías" appears, store as {"value": 536, "unit": "hectares"} with note about original unit
- Valuations often in pesos (pre-1959) — note currency and date for inflation adjustment

---

## OCR Error Patterns (Spanish)

### Accented Characters

OCR frequently misreads Spanish accents:

| Correct | Common OCR Error | Context |
|---------|------------------|---------|
| **ñ** | n, fi | "año" → "ano" or "afio" |
| **á, é, í, ó, ú** | a, e, i, o, u | Lost accents very common |
| **ü** | u, ii | "güey" → "guey" or "giiey" |
| **Á** (uppercase) | A | Lost in uppercase text |

**Mitigation:** LLM should interpret "ano" as "año" in date contexts, "propietario" even if OCR says "propietario" (missing accent).

### Easily Confused Characters

| Correct | OCR Confusion | Example |
|---------|---------------|---------|
| **rn** | m | "gobierno" → "gobiemo" |
| **cl** | d | "incluye" → "induye" |
| **ll** | U, H | "calle" → "caUe" |
| **ti** | ü | "título" → "tíülo" |
| **fi** | ñ, A | "finca" → "Anca" |
| **vv** | w | (rare in Spanish) |
| **1** (one) | l, I | "1958" → "l958" or "I958" |
| **0** (zero) | O | "1950" → "195O" |

### Faded Ink Patterns

When ink fades, certain letters become ambiguous:

| Letter | Fades to | Why |
|--------|----------|-----|
| **e** | c, o | Top loop disappears |
| **a** | o | Opening closes |
| **o** | c | Gap closes |
| **s** | (illegible) | Thin strokes disappear |
| **z** | 2 | Similar shape |

### Common Word Errors

| Intended | Typical OCR | Frequency |
|----------|-------------|-----------|
| **año** | ano, afio | Very high |
| **señor** | senor, seflor | High |
| **número** | numero, niimero | High |
| **título** | titulo, ütulo | Medium |
| **escribano** | escnbano | Medium |
| **cláusula** | clausula | Medium |
| **María** | Marfa, Maria | High |
| **José** | Jose, Josd | High |

### Normalization Rules

Post-OCR, apply these corrections:

```python
OCR_CORRECTIONS = {
    # Accents
    r'\bano\b': 'año',           # "ano" → "año" (word boundary)
    r'\bsenor\b': 'señor',
    r'\bnumero\b': 'número',
    r'\btitulo\b': 'título',

    # Character substitutions
    r'gobiemo': 'gobierno',      # rn→m error
    r'caUe': 'calle',            # ll→U error
    r'fio\b': 'ño',              # Common pattern in años, señor

    # Common names
    r'Jose\b': 'José',
    r'Maria\b': 'María',
    r'Raul\b': 'Raúl',
}
```

**Caution:** Only apply in context — "ano" meaning "anus" is valid in medical documents. Use heuristics.

---

## Historical Context (1940s-1960s Cuba)

### Key Organizations

| Acronym | Spanish | English | Role | Time Period |
|---------|---------|---------|------|-------------|
| **INRA** | Instituto Nacional de Reforma Agraria | National Institute of Agrarian Reform | Executed confiscations | 1959-1976 |
| **FCSC** | Foreign Claims Settlement Commission | — | U.S. body certifying confiscation claims | 1964-1972 |
| **ORI** | Organizaciones Revolucionarias Integradas | Integrated Revolutionary Organizations | Early communist party | 1961-1963 |

### Important Dates

| Date | Event | Impact on Documents |
|------|-------|---------------------|
| **May 17, 1959** | First Agrarian Reform Law | Legal basis for confiscations |
| **October 13, 1960** | Urban Reform Law | Nationalized rental properties |
| **October 14, 1960** | Nationalization of 382 companies | Mass industrial confiscations |
| **1961-1968** | Continuing confiscations | Various decrees and actions |
| **1964** | FCSC opens claims period | U.S. citizens file claims |

### Confiscation Terminology

Documents may use various terms for the same action:

| Term | Implication | Legal Basis |
|------|-------------|-------------|
| **Confiscación** | Outright seizure | Agrarian Reform Law |
| **Nacionalización** | State takeover | Revolutionary decrees |
| **Intervención** | State administration (may precede confiscation) | Administrative decree |
| **Expropiación** | Forced purchase (compensation implied, rarely paid) | Various laws |

### Common Document Phrases

| Spanish Phrase | English | Context | Interpretation |
|----------------|---------|---------|----------------|
| **comparece Don/Doña** | "appears Mr./Mrs." | Beginning of notarial act | Identifies party to transaction |
| **otorga poder** | "grants power" | Power of attorney | Delegation of authority |
| **declara bajo juramento** | "declares under oath" | Sworn statement | Legal testimony |
| **inscrito en el Registro** | "registered in the Registry" | Property registration | Creates legal effect |
| **con arreglo a derecho** | "in accordance with law" | Legal compliance | Formulaic phrase |
| **cédula de identidad** | "identity card" | Personal ID | Cuban national ID number |
| **vecino de** | "resident of" | Domicile | Person's legal residence |
| **mayor de edad** | "of legal age" | Age declaration | Over 21 (or 18 post-1940) |
| **en pleno uso de sus facultades** | "in full use of faculties" | Competence | Legally capable |
| **finca número** | "property number" | Registry reference | Official property ID |
| **folio** | "folio" | Page in registry book | Physical location in registry |
| **tomo** | "volume" | Registry book number | Volume in registry series |
| **causante** | "decedent" | Deceased whose estate is being settled | Inheritance context |

---

## Name Patterns

### Spanish Naming Conventions

**Full name structure:** [Given name(s)] [Paternal surname] [Maternal surname]

**Example:** María del Carmen Pérez García
- Given names: María del Carmen
- Paternal surname: Pérez
- Maternal surname: García (often omitted)

**Married women:** May add "de [husband's surname]"
- María Pérez García de Ceresa

### Common Titles & Abbreviations

| Spanish | Abbreviation | English | Usage |
|---------|--------------|---------|-------|
| **Don** | D. | Mr. (formal) | Respect for men, not legally significant |
| **Doña** | Dña. | Mrs. (formal) | Respect for women |
| **Señor** | Sr. | Mr. | Standard address |
| **Señora** | Sra. | Mrs. | Married woman |
| **Señorita** | Srta. | Miss | Unmarried woman |
| **Doctor** | Dr. | Doctor | Professional title |
| **Ingeniero** | Ing. | Engineer | Professional title |
| **Licenciado** | Lic. | Graduate/Lawyer | Professional title |

**Note:** "Don/Doña" are honorifics, not part of legal name. "Don Mario Ceresa" and "Mario Ceresa" refer to same person.

### Common Cuban Names (1940s-1960s)

**Male Given Names:**
- Mario, José, Carlos, Juan, Pedro, Luis, Rafael, Francisco, Manuel, Antonio

**Female Given Names:**
- María (very common, often compound: María del Carmen, María Teresa)
- Carmen, Ana, Rosa, Isabel, Elena, Teresa, Josefa, Dolores

**Common Surnames:**
- García, Rodríguez, Fernández, López, Martínez, González, Pérez, Sánchez, Ramírez, Cruz

**Family clusters:** Multiple people with same surname in documents likely related.

---

## Date Formats

### Written Dates (Spanish)

| Format | Example | Notes |
|--------|---------|-------|
| **Day-Month-Year** | "15 de marzo de 1958" | Most common in legal docs |
| **Abbreviated** | "15-III-1958" | Roman numerals for month |
| **Long form** | "quince de marzo de mil novecientos cincuenta y ocho" | Formal documents |

### Month Names (Spanish)

| Spanish | English | Abbreviation |
|---------|---------|--------------|
| enero | January | I, ene. |
| febrero | February | II, feb. |
| marzo | March | III, mar. |
| abril | April | IV, abr. |
| mayo | May | V |
| junio | June | VI, jun. |
| julio | July | VII, jul. |
| agosto | August | VIII, ago. |
| septiembre | September | IX, sep., sept. |
| octubre | October | X, oct. |
| noviembre | November | XI, nov. |
| diciembre | December | XII, dic. |

**Extraction rule:** Convert all dates to ISO 8601 (YYYY-MM-DD) with precision indicator.

---

## Normalization Guidelines

### Entity Name Normalization

| Original Variations | Normalize To | Rule |
|---------------------|--------------|------|
| Don Mario Ceresa, Mario Ceresa, M. Ceresa | Mario Ceresa | Remove title, expand initials |
| Central Santa Maria, Ingenio Santa Maria | Central Santa Maria | Prefer "Central" over "Ingenio" |
| La Habana, Habana | La Habana | Keep article for major cities |
| INRA, I.N.R.A. | INRA | Remove periods from acronyms |

### Location Normalization

| OCR Output | Normalize To | Reason |
|------------|--------------|--------|
| Florida, Camagüey | Florida (Camagüey) | Municipality (Province) |
| Habana | La Habana | Proper name |
| Oriente | Oriente Province | Province name |

### Amount Normalization

| Original | Normalize To | Notes |
|----------|--------------|-------|
| $2,000.00 | 2000.00 USD | Remove formatting, note currency |
| 40 caballerías | 536 hectares | Convert to standard unit, log original |
| dos mil pesos | 2000 CUP | Parse text amounts, note currency |

---

## Glossary Quick Reference

### Top 50 Terms for LLM Context

Provide these in entity extraction prompts:

1. **Central** — Sugar mill complex
2. **Ingenio** — Sugar mill (synonym)
3. **Finca** — Farm/estate
4. **Escritura** — Deed
5. **Título** — Title
6. **Notario** — Notary
7. **Propietario** — Owner
8. **Heredero** — Heir
9. **Confiscación** — Confiscation
10. **INRA** — Agrarian Reform Institute
11. **Caballería** — Land unit (~13.4 hectares)
12. **Registro** — Registry
13. **Testamento** — Will
14. **Compraventa** — Sale/purchase
15. **Sucesión** — Inheritance/succession
16. **Provincia** — Province
17. **Municipio** — Municipality
18. **Folio** — Registry folio/page
19. **Tomo** — Registry volume
20. **Inscripción** — Registration
21. **Cancelación** — Cancellation
22. **Hipoteca** — Mortgage
23. **Don/Doña** — Honorific title (ignore in matching)
24. **Señor/Señora** — Mr./Mrs.
25. **Testigo** — Witness
26. **Vecino de** — Resident of
27. **Adjudicación** — Court-ordered assignment
28. **Albacea** — Executor
29. **Causante** — Decedent
30. **Partición** — Partition of estate
31. **Nacionalización** — Nationalization
32. **Interventor** — Government administrator
33. **Reforma Agraria** — Agrarian Reform
34. **Certificado** — Certificate
35. **Declaración** — Declaration
36. **Poder** — Power of attorney
37. **Acta** — Official act/record
38. **Juez** — Judge
39. **Tribunal** — Court
40. **Resolución** — Resolution/decree
41. **Ley** — Law
42. **Decreto** — Decree
43. **Colonia** — Colony (farming community)
44. **Hacienda** — Large estate
45. **Sitio** — Small plot
46. **Solar** — Urban lot
47. **Hectárea** — Hectare
48. **Metro cuadrado** — Square meter
49. **Peso** — Cuban peso (currency)
50. **Año** — Year

---

*This dictionary should be updated as new terminology is encountered during document processing. Maintain a living glossary.*
