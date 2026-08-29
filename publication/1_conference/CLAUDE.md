# CLAUDE.md — PyNTLP

Guidance for Claude Code working in this repository.

## Two independent codebases in one repo

1. `src/pyntlp/` — the **production** package. Spark-native (PySpark), implements the
   Solar Sharer Offer tariff-to-load-profile model (`compute_pma_sso`). Currently uses a
   hand-picked `s_segment` constant for the shiftable share.
2. `publication/1_conference/` — **standalone research code** for the IEEE PES ISGT Asia
   2026 paper on Adaptive Quantile Flexibility (AQF). Plain numpy/pandas/scipy/sklearn/
   matplotlib. **No Spark.** Nothing here is imported by the production package, and
   `src/pyntlp/` must not be modified as a side effect of paper work.

The long-term intent is that AQF eventually replaces the hand-picked `s_segment` with a
data-calibrated estimate. That port has not been done and is out of scope for the paper.

## Working conventions

- `publication/1_conference/src/config.py` is the **single source of truth** for every
  grid value, seed, and threshold. Add new constants there rather than inline.
- Every number quoted in the paper must be read from `data/3_gold/tables/*.csv`.
  Never hand-type a result into the manuscript.
- Data tiers: `1_bronze` raw simulated days (gitignored, regenerable) -> `2_silver`
  per-scenario/replicate estimates -> `3_gold` aggregated tables and figures.
- `build_docx.py` edits an external Word file on OneDrive and always writes a timestamped
  backup first. Keep that behaviour.
- Figures use Arial. Arial is installed on this Windows machine; do not change the font
  stack in `plotting.py`.
- Figures are authored at their FINAL printed width (`config.FIG_COL_W_IN` / `FIG_FULL_W_IN`,
  which `build_docx.py` also derives its `COL_W` / `FULL_W` from) and saved with
  `layout="constrained"` and **no** `bbox_inches="tight"`. Tight bboxes crop the canvas, so
  Word rescales the image on insert and every point size in the figure silently changes.
  `plotting.check_widths()` asserts this and runs as part of `python plotting.py`.
- `table3_results_summary.csv` is legacy: it ranks by the mean of |R_F - 1|, which the noise
  floor dominates. The paper prints `table3_headline_results.csv`; `table4_win_counts.csv`
  is quoted in prose. `python experiment.py tables` rebuilds the Gold tables without
  re-simulating.
- The paper has a HARD four-page limit including references. python-docx cannot paginate,
  so `preview.py` drives the installed Word to export a PDF, reports the real page count,
  and rasterises each page for inspection. Check it after any content change.
- Two layout facts worth knowing before trying to shorten the paper: text placed BEFORE a
  full-width figure island cannot shorten the tail (it only widens the gap at the foot of
  the previous page), and the template's `equation` style ships in the Symbol font, which
  renders <m:nor/> runs as Greek ("Bern" -> Bern in Greek letters). `fix_equation_font`
  resets it to Cambria Math; do not remove that call.
- The pristine IEEE template is vendored at `assets/ieee_template.docx`. It used to be read
  from a timestamped backup beside the draft on OneDrive, which broke when those were tidied
  into an archive folder. Override with $ISGT_TEMPLATE if needed.
- Figure, table and equation numbers are Word SEQ fields, and in-text references are REF
  fields pointing at bookmarks, so inserting an item in the middle renumbers everything on
  refresh (Ctrl+A, F9). Write cross-references in body text as `{{fig:key}}`, `{{tab:key}}`
  or `{{eq:key}}`; document order is fixed by FIGURE_ORDER / TABLE_ORDER / EQUATION_ORDER in
  build_docx.py, so add the key there when adding an item.
- Citations are grouped numeric ([9, 10], [9-11]) and the document's Zotero style is set to
  Vancouver to match, so refreshing fields in Zotero does not revert the grouping.
- Reference-list titles are normalised to IEEE sentence case at RENDER time
  (`_sentence_case` in references.py); the CSL/RIS data keeps publisher casing, so
  Zotero imports stay faithful. Protected proper nouns live in `_PROTECTED`.
- Sentence dashes in the manuscript are spaced en dashes (" – "); build_docx.py
  content strings use them directly. Never use a spaced hyphen as a dash.
- `picture()` sets keep-with-next on the image paragraph so a figure can never be
  separated from its caption by a page break. Layout consequence: a full-width island
  moves as one block, so the text that fills the previous page's tail must be placed
  BEFORE the island in document order (the "Fig. 4 shows where..." paragraph is
  deliberately before the fig4 island for this reason).
- Terminology is unified as: "event frequency p" (never persistence), "event size kappa",
  "backbone", "candidate flexibility", "oracle-q". Oracle-q is deliberately NOT called an
  upper bound or ceiling - it takes an empirical quantile of D days, so AQF beats it on
  backbone error wherever kappa >= 4 (32 of 100 cells). The paper states this.
- The intro carries the production MVP equation E_shift = s*k*a*E_day (equation key "mvp",
  omml index 8) and the conclusion ties back to replacing s. Keep the two in sync.
- fallback_blend in estimators.py clips the blended quantile at 0.5. Provably a no-op for
  the current q* form (empirical max q_used = 0.4875 over all 10,000 runs), so results are
  unchanged; it backs the paper's "capped at the median" claim.

## Regenerating everything

```powershell
cd publication\1_conference\src
python experiment.py    # -> bronze, silver, gold tables
python plotting.py      # -> 5 figures (checks each PNG's printed width)
python build_docx.py    # -> writes the Word draft (backs it up first)
python preview.py "<docx>" <outdir>   # true page count + page images
```

## Current task

See `publication/1_conference/TASK_metrics_framing.md`.

## Model recap (for orientation)

Fixed timestamp, D=365 days: `L = B + Z*A + eps`, `Z ~ Bernoulli(p)`, `eps ~ N(0, sigma^2)`,
`kappa = A/sigma`. Backbone estimated as a quantile of L. AQF picks the bias-minimising
quantile `q* = (1-p)/2 + p*Phi(-kappa)` from EM-estimated `p_hat, kappa_hat`, with an
Ashman's D identifiability check (`D = kappa/sqrt(2)`, threshold 2.0) and a soft blend
toward `q_default = 0.2` when separation is weak.
