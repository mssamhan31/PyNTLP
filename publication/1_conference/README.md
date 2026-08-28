# ISGT Asia — Recoverability-Aware Adaptive Quantile Flexibility (AQF)

Standalone research code and artifacts for the conference paper. This is
independent of the production `pyntlp` package (plain numpy/pandas/scipy, no
Spark). If AQF proves out, its estimator logic will be ported into
`src/pyntlp/` as a separate, later effort — nothing here is imported by the
production package.

## Scope

Synthetic-only study of a fixed-timestamp mixture model `L = B + Z*A + eps`.
Compares three backbone-estimation strategies for recovering
shape-identifiable candidate flexibility:

1. **fixed-q** — a single hand-picked quantile applied everywhere.
2. **oracle-AQF** — the bias-minimising quantile `q_t*`, computed from the
   *true* `p, kappa` (upper bound, not achievable in practice).
3. **estimated-AQF** — `q_t*` computed from data-estimated `p_hat, kappa_hat`
   (2-component Gaussian mixture via EM), with an identifiability check and a
   soft-blend fallback to a default quantile when separation is too weak to
   trust.

See the locked PRD in the Obsidian vault
(`1B - PyNTLP method dev.md`, section "ISGT Asia Conference Paper —
Recoverability-Aware Adaptive Quantile Flexibility (AQF)") for the full
theoretical background and MoSCoW scope.

## Layout

```
src/            reusable modules (config, synth, estimators, metrics, experiment, plotting)
notebooks/      thin orchestration notebooks that call into src/
data/1_bronze/  raw per-day simulated ground truth per scenario/replicate
data/2_silver/  per-scenario/replicate scalar estimates and metrics
data/3_gold/    publication-ready aggregated tables (CSV) and figures (PNG)
```

## Reproducing all artifacts

```powershell
pip install -r requirements.txt
python src\experiment.py      # writes data/1_bronze and data/2_silver, aggregates to data/3_gold/tables
python src\plotting.py        # writes data/3_gold/figures
```

All grid values, seeds, and thresholds are defined once in `src/config.py`.
Every number quoted in the paper must be read directly from
`data/3_gold/tables/*.csv` — never hand-typed.
