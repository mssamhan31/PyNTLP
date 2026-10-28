# Adaptive Quantile Flexibility (AQF)

AQF is a separate study. It is not part of the `pyntlp` package and not a stage of its pipeline;
its code lives in
[`publication/1_conference/`](https://github.com/mssamhan31/PyNTLP/tree/main/publication/1_conference)
and nothing there is imported by the package.

## The problem

To estimate how a tariff could move load, a modeller first needs to know how much of an aggregate
load profile is flexible. Metered load shows only a total. A common practice takes a fixed quantile
of the daily readings at each time of day, such as the 10th percentile, as the underlying load (the
backbone) and treats the rest as flexible. The right quantile, however, depends on how
often flexible events happen and how large they are.

## The method

At one time of day over `D` days, the load is modelled as a backbone plus an occasional event:

```text
L = B + Z*A + eps
Z ~ Bernoulli(p),   eps ~ N(0, sigma^2),   kappa = A / sigma
```

`p` is the event frequency and `kappa` the event size relative to ordinary day-to-day variation.
The quantile that lands exactly on the backbone is

```text
q* = (1 - p)/2 + p * Phi(-kappa)
```

AQF estimates `p` and `kappa` from the readings by fitting a two-component Gaussian mixture with a
shared variance (expectation-maximisation), computes `q*` for that timestamp, and takes that
quantile of the readings as the backbone. A separation test checks whether the two components are
far enough apart to trust; where they are not, the quantile is blended toward a default of 0.2.

## The result, on synthetic data

On synthetic data, over a 10 × 10 grid of event frequency and event size with 365 days and 20
replicates per cell, AQF cut the backbone error to about a third of the best fixed quantile's and
about halved the median recovery error. Where the separation threshold is met, its median recovery
error is close to that of oracle-q, which is handed the true `p` and `kappa`.

| estimator | mean \|RF − 1\| | median \|RF − 1\| | median, kappa ≥ 2.83 | MAE of backbone (kW) |
|---|---|---|---|---|
| Oracle-q | 0.834 | 0.196 | 0.105 | 0.099 |
| AQF | 1.537 | 0.260 | 0.114 | 0.257 |
| Fixed q = 0.3 | 1.554 | 0.598 | 0.561 | 0.812 |
| Fixed q = 0.2 | 2.081 | 0.636 | 0.538 | 0.752 |
| Fixed q = 0.1 | 3.004 | 0.862 | 0.556 | 0.924 |

`RF` is the flexible energy recovery ratio, the recovered flexible energy over the true amount
(ideal 1). The table is `table3_headline_results.csv` in
`publication/1_conference/data/3_gold/tables/`, printed to three decimals as in the paper's
Table II. It holds on synthetic data only; AQF has not yet been validated on real meter data.

/// details | Show details
    type: more

## The separation test

The test computes `D = kappa_hat / sqrt(2)` and trusts the fitted quantile where `D >= 2`, that is
`kappa >= 2.83`. It is a bimodality bar in the spirit of Ashman's D, rescaled: for a mixture with
shared variance, Ashman's own statistic equals `kappa`, so this bar is stricter than Ashman's usual
`kappa > 2`. Below the bar, the quantile used is a blend of the fitted `q*` and the default 0.2,
weighted by `w = D / 2`, so the default takes over as the components merge. The result is capped at
the median.

## Oracle-q is not a ceiling

Oracle-q uses the true `p` and `kappa` but still takes an empirical quantile of 365 days, so AQF
can beat it on backbone error in parts of the grid, as it does wherever `kappa >= 4`, on synthetic
data.

## Head to head

On synthetic data, AQF has the lower recovery error in 95, 89 and 58 of the 100 cells against fixed
quantiles of 0.1, 0.2 and 0.3, and in 44 against the best fixed quantile chosen per cell in
hindsight, which no practitioner could choose in advance (`table4_win_counts.csv`).

## Experiment settings

| factor | value |
|---|---|
| scenario grid, `p` × `kappa` | 0.05 to 0.95 × 0.5 to 5.0, 10 × 10 cells |
| days, replicates, seed | 365 days; 20 replicates; seed 42 |
| backbone, noise | 10 kW, 1 kW |
| fixed quantiles compared | 0.1, 0.2, 0.3 |
| fallback quantile | 0.2 |
| separation threshold | `D >= 2`, that is `kappa >= 2.83` |
| interval length | 0.5 h |

## Limitations

The backbone is an estimate of the load present every day, not of the physically non-shiftable
load: a pool pump on a daily timer counts as backbone, and an air conditioner switched on by the
weather counts as flexibility. The synthetic data match the model exactly, with two Gaussian humps;
real load cannot fall below zero and is often right-skewed, which would set the quantile too low
and overstate the flexible load. Validation on real data, and comparison with quantile regression
and customer baseline methods, are future work.

## Reproduce the results

```powershell
cd publication\1_conference
python -m venv .venv-aqf
.venv-aqf\Scripts\Activate.ps1
pip install -r requirements.txt
python src\experiment.py      # simulate, estimate and aggregate to the gold tables
python src\plotting.py        # the figures, with a printed-width check
```

All seeds are fixed, so a matching environment reproduces the committed tables exactly. The
folder's [README](https://github.com/mssamhan31/PyNTLP/blob/main/publication/1_conference/README.md)
has the details.

## Citation

M. S. Samhan, N. Haghdadi, D. Sim, A. Bruce and B. Yildiz, "Adaptive Quantile Flexibility:
Recovering Candidate Flexible Load from Aggregate Profiles for Network Tariff Modelling," accepted
for the 2026 IEEE PES Innovative Smart Grid Technologies Asia (ISGT Asia), Wuhan, China, 30 October
to 1 November 2026. Code: <https://doi.org/10.5281/zenodo.22246960>.

///
