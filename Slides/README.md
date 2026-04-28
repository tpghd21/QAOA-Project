# QAOA for MaxCut — Beamer Presentation

Rebuilt presentation source. Compiles to a 16:9 PDF using the
[Metropolis](https://github.com/matze/mtheme) Beamer theme.

## Files

- [qaoa_presentation.tex](qaoa_presentation.tex) — slide source
- figures are pulled from `../Theory/figures/`, `../Implementation/figures/`,
  `../Motivation/figures/`, `../Results/figures/`, and `../Implementation/exp_graphs.png`

## Compile

### Easiest: Overleaf
Upload the whole repo (or just `Slides/` plus the `figures/` folders it references)
to Overleaf. Metropolis is preinstalled.

### Local (TeX Live / MiKTeX)
```bash
cd Slides
latexmk -pdf qaoa_presentation.tex
```
or twice with `pdflatex`:
```bash
pdflatex qaoa_presentation.tex
pdflatex qaoa_presentation.tex
```

If Metropolis is missing:
```bash
tlmgr install beamertheme-metropolis
```

## What changed from the original PDF

1. **Notation fixed.** Two MaxCut groups are now $S$ and $\bar S$ everywhere
   (the original used $S$ for both).
2. **New: approximation-ratio definition slide** — every chart later in the
   deck is reported in this metric, so the definition appears up front.
3. **New: crossover analysis slide** — the most informative noise result
   (when $p=1$ overtakes $p=3$) was missing from the original.
4. **Measurement results compressed** from four near-identical slides to
   one summary slide.
5. **References moved before** the closing slide (was orphaned after
   "Thanks for your attention").
6. **Typos fixed** ("haven't proof" → "have not yet proven", math rendering
   in the noise-channel slide).
7. **Page numbering unified** via Beamer's native `frame X / total Y`.

## Slide count

~22 frames (down from 33), with denser content per slide.
