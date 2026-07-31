# Milestone 23 — Task 03a: Read the Docs (Sphinx / Wyrm) Project Webpage Style

**Author**: Chong Shik Park  
**Affiliation**: Department of Accelerator Science and Center for Accelerator Research, Korea University, Sejong, 30019 Republic of Korea

---

## 1. Executive Summary

Task 03a converted the NKM project documentation webpage (`docs/index.html`) into the standard **Read the Docs** (Sphinx / Wyrm / WarpX documentation) theme style.

The updated webpage matches the layout, navigation tree, typography, callout admonition boxes (`.. note::`, `.. tip::`, `.. warning::`, `.. important::`), data tables (`wy-table`), and breadcrumb bars inspired by Read the Docs sites like [WarpX Read the Docs](https://warpx.readthedocs.io/en/latest/index.html).

## 2. Work Completed

1. **Read the Docs Theme Architecture (`docs/index.html`)**:
   - **Sidebar Navigation Pane (`wy-nav-side`)**: Project title header, version badge pill (`v0.1.0 (latest)`), live search filter input (`Search docs...`), categorized multi-level TOC tree, and Korea University footer.
   - **Top Breadcrumbs Bar (`wy-breadcrumbs`)**: Interactive path navigation (`Docs » POHANG 4GSR » NKM`), GitHub view link, PDF report download button, and instant Theme Switcher (Dark / RTD Classic Light Mode).
   - **Sphinx Admonition Boxes**: Applied `wy-admonition` styles for Note (Author & Affiliation block), Tip (Production script & dry-run commands), Warning, and Important (Cryptographic SHA-256 data provenance).
   - **Data Tables (`wy-table`)**: Styled module subsystem tables and SHA-256 data checksum tables matching Sphinx Wyrm border and alternate row shading rules.
   - **Typography & MathJax**: Used `Lato`, `Roboto Slab`, and `Fira Code` webfonts with MathJax LaTeX equation rendering.
   - **Header Anchor Links (`headerlink`)**: Hover `¶` permalink anchors on all section headings.
   - **Footer (`wy-nav-footer`)**: Copyright attribution to Chong Shik Park (Korea University) and Read the Docs theme credits.

2. **Full Content Preservation**:
   - Preserved all 6 simulation steps, physics equations, rigidity formulas, module subsystems, tolerance budgets, MOGA Pareto optimization details, literature references, and PDF download links.

## 3. Protected Files Status

- `NKM_radia.ipynb`: Unchanged
- `NKM_radia_y=0.ipynb`: Unchanged
- `nlk.py`: Unchanged
- `storage_ring.ipynb`: Unchanged
- `By.txt`, `kickmap_file.txt`, `K4GSR_HBIv4-1.mat`, `nkm_field.xlsx`: Unchanged
- All protected scientific source files verified unmodified via `git status` and `git diff`.

## 4. Verification & Results

- `docs/index.html` passes HTML5 validation, supports responsive mobile drawers, and features live dark/light mode toggling.
- Rule compliance verified: zero remote pushes, zero remote GitHub Actions checks, 100% local operation.
