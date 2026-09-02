# Adaptive Quantile Flexibility (AQF)

Conference paper code and artifacts.

Standalone research code, independent of the production `pyntlp` package (plain
numpy/pandas/scipy, no Spark). If AQF proves out, its estimator logic will be
ported into `src/pyntlp/` as a separate, later effort — nothing here is imported
by the production package.

## The problem

Aggregate metered load at a single timestamp mixes two things that a planner
needs to tell apart: the **backbone**, the level demand would have sat at with
no flexible response, and the **candidate flexibility** stacked on top of it.
Only the total is observed. Estimating the backbone as a fixed quantile of the
across-day distribution — a single hand-picked `q` applied everywhere — is the
common practice, and it is biased by an amount that depends on how often
flexible events occur and how large they are.

## The model

A synthetic-only study of a fixed-timestamp mixture, with `D = 365` days at one
timestamp:

```
L = B + Z*A + eps      Z ~ Bernoulli(p)      eps ~ N(0, sigma^2)      kappa = A / sigma
```

`p` is the **event frequency**, `kappa` the **event size** relative to ordinary
day-to-day variability. Candidate flexibility is recovered as the positive
residual above the estimated backbone, `F_hat = max(L - B_hat, 0)`.

The central relation is that for a backbone taken as the `q`-th quantile, the
normalised bias `b` satisfies `q = (1-p)*Phi(b) + p*Phi(b - kappa)`. Setting
`b = 0` and solving gives the **bias-minimising quantile**

```
q* = (1-p)/2 + p*Phi(-kappa)
```

which is the whole idea: the right quantile is not a preference, it is a
quantity computable from how often events happen and how big they are.

## Scope

The experiment compares three backbone-estimation strategies over a 10x10 grid
of `(p, kappa)`, 20 replicates per cell:

1. **fixed-q** — a single hand-picked quantile applied everywhere
   (`config.FIXED_QS`), the practice AQF is measured against.
2. **oracle-AQF** — `q*` computed from the *true* `p, kappa`. Called *oracle*
   because it is handed the true parameters rather than estimates, which no real
   deployment can do. It is deliberately **not** an upper bound or a ceiling: `q*`
   still takes an empirical quantile of 365 days, so estimated-AQF beats it on
   backbone error in parts of the grid. The paper refers to this variant as
   *oracle-q*; the code and the CSV outputs use `oracle_aqf`.
3. **estimated-AQF** — `q*` computed from data-estimated `p_hat, kappa_hat`
   (2-component Gaussian mixture with tied variance, fitted by EM), with an
   identifiability check and a soft blend toward a default quantile when the two
   modes are too poorly separated to trust. This is the method as it would
   actually be deployed.

Separation is gated on `D = kappa / sqrt(2)` against `config.D_THRESH = 2.0`
(see `estimators.identifiability_diagnostic`), a bimodality bar in the spirit of
Ashman's D. Note that `D` here is Ashman's statistic rescaled by `1/sqrt(2)`, so
gating at `D >= 2` is the stricter bar `kappa >= 2.83`.

## Layout

```
src/            reusable modules (config, synth, estimators, metrics, experiment, plotting)
notebooks/      thin orchestration notebooks that call into src/
data/1_bronze/  raw per-day simulated ground truth per scenario/replicate (gitignored, regenerable)
data/2_silver/  per-scenario/replicate scalar estimates and metrics
data/3_gold/    publication-ready aggregated tables (CSV) and figures (PNG)
```

## Reproducing all artifacts

Use a fresh virtual environment. The versions in `requirements.txt` are pinned
to those the committed artifacts were produced with, so an unpinned install may
not reproduce the numbers exactly.

```powershell
python -m venv .venv-aqf
.venv-aqf\Scripts\Activate.ps1
pip install -r requirements.txt

python src\experiment.py      # writes data/1_bronze and data/2_silver, aggregates to data/3_gold/tables
python src\plotting.py        # writes data/3_gold/figures, then verifies each printed width
```

`python src\experiment.py tables` rebuilds only the gold tables from the
existing recoverability summary, without re-simulating.

All seeds are fixed and derived deterministically from `config.BASE_SEED`, so a
matching environment reproduces the committed CSVs exactly. All grid values,
seeds, and thresholds are defined once in `src/config.py`. Every number quoted
in the paper must be read directly from `data/3_gold/tables/*.csv` — never
hand-typed.

Figures are authored at their final printed width for a two-column page
(`config.FIG_COL_W_IN`, `config.FIG_FULL_W_IN`) and saved without a tight
bounding box, so nothing rescales them on insert and the point sizes set in the
figure are the ones that reach the page. `plotting.check_widths()` asserts this
and runs as part of `python plotting.py`.
