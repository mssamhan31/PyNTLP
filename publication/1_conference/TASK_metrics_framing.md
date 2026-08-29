# TASK — fix the results framing, then regenerate

> STATUS 2026-08-29: implemented. The median/identifiable-region framing, the
> win-count reporting, `KAPPA_IDENTIFIABLE`, and the docx updates below are all
> in place, and the noise floor is additionally characterised in closed form in
> the paper. Kept for the reproduce-snippet and the historical rationale.

Written 2026-08-28. Deadline for ISGT Asia submission: **10 Sep 2026**.

## The problem

`table3_results_summary.csv` ranks estimators by the **mean** of |R_F - 1| across the
(p, kappa) grid. That mean is dominated by the low-persistence cells where R_F reaches
30-50 because of the noise-floor effect (`F_hat = max(L - B_hat, 0)` counts truncated
noise on non-event days as flexibility). The noise floor is a *separate* phenomenon that
the paper already identifies as not attributable to the estimator — so the headline metric
is mostly measuring the thing the paper says is not the estimator's fault.

Consequence: estimated-AQF (1.54) appears merely tied with fixed q=0.3 (1.55), which
badly undersells the method.

## What the data actually shows

Recomputed from `data/3_gold/tables/recoverability_summary.csv` (not hand-typed; see
snippet below to reproduce):

| Estimator | mean abs(R_F-1) | median abs(R_F-1) |
|---|---|---|
| Oracle-AQF | 0.834 | 0.196 |
| Estimated-AQF | 1.537 | 0.260 |
| Fixed q=0.3 | 1.554 | 0.598 |
| Fixed q=0.2 | 2.081 | 0.636 |
| Fixed q=0.1 | 3.004 | 0.862 |

Restricted to the identifiable region kappa >= 2.83 (i.e. Ashman's D >= D_thresh = 2.0),
median abs(R_F - 1):

- Oracle-AQF 0.105, Estimated-AQF 0.114, best fixed-q 0.538

Restricted further to kappa >= 2.83 AND p >= 0.3:

- Oracle-AQF 0.0657, Estimated-AQF 0.0659 (statistically indistinguishable)

Mean MAE_B (uncontaminated by the noise floor):

- Oracle 0.099, Estimated-AQF 0.257, fixed q=0.2 0.752, q=0.3 0.812, q=0.1 0.924

Head-to-head cell win counts for estimated-AQF:

- vs fixed q=0.1: 95/100
- vs fixed q=0.2: 89/100
- vs fixed q=0.3: 58/100
- vs best-in-hindsight fixed q: 44/100

## The headline claims this supports

1. On the median, estimated-AQF is ~2.3x closer to perfect recovery than the best fixed
   quantile.
2. **Where the method's own identifiability test says the fit is trustworthy, estimated-AQF
   performs indistinguishably from the oracle that knows the true p and kappa.** This is
   the strongest available claim and it makes the identifiability check earn its place.
3. On backbone accuracy (MAE_B), estimated-AQF is ~3x better than the best fixed quantile.
4. Report the win counts against *all three* fixed quantiles, not just q=0.2. Quoting only
   the 89/100 figure looks like baseline shopping. Make the correct argument instead: a
   practitioner cannot know in advance which fixed q is right, so "best fixed q chosen in
   hindsight" is itself an oracle, not an available baseline.

## Plan (agreed, not yet implemented)

1. Add `KAPPA_IDENTIFIABLE = sqrt(2) * D_THRESH` to `config.py` so the trustworthy region
   is defined once and cannot drift from the fallback rule.
2. Add one aggregation function in `experiment.py` writing a new headline table with mean
   and median abs(R_F - 1), mean MAE_B, and the region-restricted medians.
3. Add a head-to-head win-count table (vs each fixed q, and vs best-in-hindsight fixed q).
4. Leave `table3_results_summary.csv` untouched so `build_docx.py` keeps working; add new
   files alongside it, then update `build_docx.py` to cite the new table.
5. Re-run `experiment.py` and `plotting.py` on Windows (Arial required for figures).

## Reproduce the numbers above

```python
import pandas as pd
g = pd.read_csv('data/3_gold/tables/recoverability_summary.csv')
piv = g.pivot_table(index=['p','kappa'], columns='estimator_variant', values='r_f_mean')
dev = (piv - 1).abs()
print(dev.mean().sort_values(), dev.median().sort_values())
idx = piv.index.to_frame()
print(dev[(idx['kappa'] >= 2.83).values].median().sort_values())
```

## Other open items (from the earlier handoff, still outstanding)

- Verify the Word draft still has the 2-column IEEE layout after `build_docx.py` edits.
- Make all bullets much shorter (~5-10 words), telegraphic, not prose.
- Three-line table borders (top rule, under-header rule, bottom rule only) via OXML.
- Re-do the 8 equations as numbered, professional objects (matplotlib mathtext images plus
  a Word tab stop for the number is the pragmatic path; python-docx has no OMML API).
- Put notation immediately below each equation, not in one distant list.
- Add a paragraph pre-empting the obvious reviewer question: if a mixture is already fitted,
  why not use its lower-component mean as the backbone instead of a quantile?
