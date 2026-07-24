# Active Task — Journal of Instrumentation (JINST) Manuscript Preparation

**Status**: IN PROGRESS  
**Category**: Publication & Documentation  
**Active Plan Location**: `docs/exec-plans/active/jinst_manuscript_preparation.md`  

---

## 1. Task Objective

Prepare, write, refine, compile, and finalize a publication-quality manuscript for submission to **Journal of Instrumentation (JINST)** documenting the design, 2D magnetic field map ingestion, 6D particle injection tracking, single-objective SLSQP optics matching, and NSGA-II multi-objective genetic algorithm (MOGA) optimization of the $4.0\text{ GeV}$ BTS transfer line featuring a Nonlinear Kicker Magnet (NKM).

---

## 2. Key Deliverables & Progress Tracker

- [x] Create dedicated publication folder `docs/jinst-paper/`
- [x] Acquire and configure official JINST LaTeX style `jinstpub.sty`
- [x] Resolve TeX Live 2023 `amssymb` / `\Bbbk` package conflicts
- [x] Move and expand draft manuscript `docs/jinst-paper/paper.tex`
- [x] Build BibTeX reference database `docs/jinst-paper/paper.bib`
- [x] Include high-resolution 300 DPI PNG & vector PDF figures in `docs/jinst-paper/figures/`
- [x] Clean compile manuscript to PDF: [`docs/jinst-paper/paper.pdf`](file:///home/cspark/Work/projects/nkm/docs/jinst-paper/paper.pdf)
- [ ] Author review, co-author feedback, and journal submission submission package packaging

---

## 3. Verification & Compilation Commands

```bash
# Compile JINST manuscript
cd docs/jinst-paper
rm -f paper.aux paper.toc paper.out paper.log paper.bbl paper.blg
pdflatex -interaction=nonstopmode paper.tex
bibtex paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
```
