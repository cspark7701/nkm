# Milestone 24 — Task 03a: SynapticTrack Style Read the Docs Webpage Theme Integration

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

Task 03a was updated to adopt the exact Read the Docs CSS stylesheet specification from `/home/cspark/Work/simulation_codes-working/synapticTrack/docs/site/style.css`.

The NKM project website (`docs/index.html`) and custom stylesheet (`docs/style.css`) now feature the exact dark-slate fixed sidebar navigation, blue header brand accents (`#2980b9`), search container, version pill badge, download buttons, page tools breadcrumbs, source note callouts, code blocks, and data tables defined by the synapticTrack documentation design.

## 2. Work Completed

1. **Stylesheet Integration (`docs/style.css`)**:
   - Extracted and integrated `/home/cspark/Work/simulation_codes-working/synapticTrack/docs/site/style.css`.
   - Applied root color variables (`--rtd-sidebar: #343131`, `--rtd-green: #2980b9`, `--rtd-code-bg: #f8f8f8`, `--rtd-content-bg: #ffffff`, `--rtd-font: "Lato", sans-serif`, `--rtd-mono: monospace`).
2. **HTML Layout Standardization (`docs/index.html`)**:
   - Implemented standard layout grid (`.layout` with 320px fixed header and TOC menu).
   - Constructed `.rtd-brand` banner, `.rtd-search` filter, `.rtd-version` badge, `.rtd-downloads` grid, and author `.byline` block.
   - Built fixed TOC navigation (`nav#TOC`) with real-time scroll highlighting (`a.current`) for active sections.
   - Applied `.page-tools` breadcrumb headers, `.source-note` callouts, code block styling, and data tables.
3. **Metadata & Attribution**:
   - Prominently included author Chong Shik Park and Korea University affiliation across sidebar byline and page tools headers.

## 3. Protected Files Status

- Protected scientific input files (`NKM_radia.ipynb`, `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, etc.) verified unchanged.

## 4. Verification & Results

- Verified CSS loading and layout rendering across viewports.
- Rule compliance: zero remote pushes, zero remote GitHub Actions checks, 100% local operation.
