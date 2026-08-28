"""Grid runner: generate synthetic days, run all estimator variants, and
write Bronze (raw days), Silver (per-scenario/replicate/variant estimates),
and Gold (aggregated recoverability summary + the paper's headline tables).
"""

from __future__ import annotations

import sys

import pandas as pd

import config
import estimators
import metrics
import synth


def _seed_for(p_idx: int, k_idx: int, replicate: int) -> int:
    return config.BASE_SEED + p_idx * 100_000 + k_idx * 1_000 + replicate


def run_scenario(
    p: float, kappa: float, p_idx: int, k_idx: int, replicate: int
) -> tuple[pd.DataFrame, list[dict]]:
    seed = _seed_for(p_idx, k_idx, replicate)
    days_df = synth.generate_days(
        p=p, kappa=kappa, sigma=config.SIGMA, backbone_b=config.BACKBONE_B,
        days=config.DAYS, seed=seed,
    )
    load = days_df["l"].to_numpy()
    f_true = days_df["f_true"].to_numpy()
    b_true = config.BACKBONE_B

    scenario_id = f"p{p_idx:02d}_k{k_idx:02d}"
    silver_rows: list[dict] = []

    def _score(variant: str, q_used: float, backbone_hat: float, extra: dict) -> None:
        f_hat = estimators.residual_estimator(load, backbone_hat)
        row = {
            "scenario_id": scenario_id,
            "p": p,
            "kappa": kappa,
            "replicate": replicate,
            "estimator_variant": variant,
            "q_used": q_used,
            "backbone_hat": backbone_hat,
            "r_f": metrics.recovery_ratio(f_hat, f_true, config.DT_HOURS),
            "mae_b": metrics.backbone_abs_error(backbone_hat, b_true),
        }
        row.update(extra)
        silver_rows.append(row)

    for q in config.FIXED_QS:
        backbone_hat = estimators.fixed_quantile_backbone(load, q)
        _score(f"fixed_q_{q}", q, backbone_hat, {})

    q_star_oracle = estimators.aqf_quantile(p, kappa)
    backbone_hat_oracle = estimators.fixed_quantile_backbone(load, q_star_oracle)
    _score("oracle_aqf", q_star_oracle, backbone_hat_oracle, {})

    fit = estimators.fit_mixture(load, seed=seed + 1)
    d_hat = estimators.identifiability_diagnostic(fit.kappa_hat)
    q_star_hat = estimators.aqf_quantile(fit.p_hat, fit.kappa_hat)
    q_final, weight = estimators.fallback_blend(q_star_hat, config.Q_DEFAULT, d_hat, config.D_THRESH)
    backbone_hat_est = estimators.fixed_quantile_backbone(load, q_final)
    _score(
        "estimated_aqf",
        q_final,
        backbone_hat_est,
        {"p_hat": fit.p_hat, "kappa_hat": fit.kappa_hat, "d_hat": d_hat, "fallback_weight": weight},
    )

    days_df.insert(0, "scenario_id", scenario_id)
    days_df.insert(1, "replicate", replicate)
    days_df.insert(2, "p", p)
    days_df.insert(3, "kappa", kappa)
    return days_df, silver_rows


# =========================================================================
# Gold aggregation for the paper's headline tables
# =========================================================================
ESTIMATOR_LABELS = {
    "oracle_aqf": "Oracle-AQF",
    "estimated_aqf": "Estimated-AQF",
    "fixed_q_0.3": "Fixed q=0.3",
    "fixed_q_0.2": "Fixed q=0.2",
    "fixed_q_0.1": "Fixed q=0.1",
}
FIXED_VARIANTS = [f"fixed_q_{q}" for q in config.FIXED_QS]


def _cell_pivots(gold: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Per-cell |R_F - 1| and MAE_B, one column per estimator variant.

    The (p, kappa) index is returned separately as a frame so region masks can
    be built from it without repeatedly unstacking.
    """
    dev = (gold.pivot_table(index=["p", "kappa"], columns="estimator_variant",
                            values="r_f_mean") - 1.0).abs()
    mae = gold.pivot_table(index=["p", "kappa"], columns="estimator_variant",
                           values="mae_b_mean")
    idx = dev.index.to_frame(index=False)
    return dev, mae, idx


def build_headline_tables(gold: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Write the two tables the Results section actually argues from.

    table3_results_summary.csv ranks estimators by the MEAN of |R_F - 1|, which
    is dominated by the low-persistence cells where the truncation noise floor -
    not the estimator - inflates R_F. These tables report the median and the
    identifiable-region restriction alongside that mean, plus MAE_B, which the
    noise floor does not contaminate at all.
    """
    if gold is None:
        gold = pd.read_csv(config.GOLD_TABLES_DIR / "recoverability_summary.csv")
    dev, mae, idx = _cell_pivots(gold)

    identifiable = (idx["kappa"] >= config.KAPPA_IDENTIFIABLE).to_numpy()
    robust = identifiable & (idx["p"] >= config.P_ROBUST).to_numpy()

    headline = pd.DataFrame(
        [
            {
                "estimator": label,
                "mean_abs_rf_dev": dev[variant].mean(),
                "median_abs_rf_dev": dev[variant].median(),
                "median_abs_rf_dev_identifiable": dev.loc[identifiable, variant].median(),
                "median_abs_rf_dev_robust": dev.loc[robust, variant].median(),
                "mean_mae_b": mae[variant].mean(),
                "mean_mae_b_identifiable": mae.loc[identifiable, variant].mean(),
            }
            for variant, label in ESTIMATOR_LABELS.items()
        ]
    ).sort_values("median_abs_rf_dev").reset_index(drop=True)
    headline.to_csv(config.GOLD_TABLES_DIR / "table3_headline_results.csv", index=False)

    # Head-to-head cell wins. "Best fixed q" takes the per-cell minimum over the
    # three fixed quantiles, i.e. a quantile chosen in hindsight for each cell.
    # That is itself an oracle, not a baseline a practitioner could deploy.
    best_fixed = dev[FIXED_VARIANTS].min(axis=1)
    n_cells = len(dev)
    wins = pd.DataFrame(
        [
            {
                "opponent": ESTIMATOR_LABELS[v],
                "available_in_advance": "Yes",
                "cells_won": int((dev["estimated_aqf"] < dev[v]).sum()),
                "cells_total": n_cells,
            }
            for v in FIXED_VARIANTS
        ]
        + [
            {
                "opponent": "Best fixed q, per-cell hindsight",
                "available_in_advance": "No",
                "cells_won": int((dev["estimated_aqf"] < best_fixed).sum()),
                "cells_total": n_cells,
            }
        ]
    )
    wins["win_rate"] = wins["cells_won"] / wins["cells_total"]
    wins.to_csv(config.GOLD_TABLES_DIR / "table4_win_counts.csv", index=False)
    return headline, wins


def build_factors_table() -> pd.DataFrame:
    """Compact experiment-factors table, grouped so it reads as a paper table
    rather than a dump of the config module."""
    factors = pd.DataFrame(
        [
            {"factor": "Scenario grid (p × κ)",
             "value": f"{config.P_GRID.min()}–{config.P_GRID.max()} × "
                      f"{config.KAPPA_GRID.min()}–{config.KAPPA_GRID.max()} "
                      f"({len(config.P_GRID)}×{len(config.KAPPA_GRID)} cells)"},
            {"factor": "Days, replicates, seed",
             "value": f"D = {config.DAYS}; {config.N_REPLICATES} replicates; seed {config.BASE_SEED}"},
            {"factor": "Backbone B, noise σ",
             "value": f"{config.BACKBONE_B:g} kW, {config.SIGMA:g} kW"},
            {"factor": "Fixed quantiles compared",
             "value": ", ".join(f"q = {q}" for q in config.FIXED_QS)},
            {"factor": "Fallback quantile q_def", "value": f"{config.Q_DEFAULT}"},
            {"factor": "Identifiability threshold",
             "value": f"D_th = {config.D_THRESH:g}  (κ ≥ {config.KAPPA_IDENTIFIABLE:.2f})"},
            {"factor": "Interval length Δt", "value": f"{config.DT_HOURS} h"},
        ]
    )
    factors.to_csv(config.GOLD_TABLES_DIR / "experiment_factors.csv", index=False)
    return factors


def run_all() -> None:
    config.ensure_dirs()

    bronze_frames: list[pd.DataFrame] = []
    silver_rows: list[dict] = []

    for k_idx, kappa in enumerate(config.KAPPA_GRID):
        for p_idx, p in enumerate(config.P_GRID):
            for replicate in range(config.N_REPLICATES):
                days_df, rows = run_scenario(p, kappa, p_idx, k_idx, replicate)
                bronze_frames.append(days_df)
                silver_rows.extend(rows)

    bronze = pd.concat(bronze_frames, ignore_index=True)
    silver = pd.DataFrame(silver_rows)

    bronze.to_parquet(config.BRONZE_DIR / "bronze_synthetic_days.parquet", index=False)
    silver.to_csv(config.SILVER_DIR / "silver_estimates.csv", index=False)

    gold = silver.groupby(["p", "kappa", "estimator_variant"], as_index=False).agg(
        r_f_mean=("r_f", "mean"),
        r_f_std=("r_f", "std"),
        mae_b_mean=("mae_b", "mean"),
        mae_b_std=("mae_b", "std"),
        fallback_weight_mean=("fallback_weight", "mean"),
    )
    gold.to_csv(config.GOLD_TABLES_DIR / "recoverability_summary.csv", index=False)

    build_headline_tables(gold)
    build_factors_table()

    print(f"Bronze rows: {len(bronze):,}  Silver rows: {len(silver):,}  Gold rows: {len(gold):,}")


if __name__ == "__main__":
    # "python experiment.py tables" re-derives the Gold tables from the existing
    # recoverability summary, without re-running the 10,000 simulations.
    if len(sys.argv) > 1 and sys.argv[1] == "tables":
        build_headline_tables()
        build_factors_table()
        print(f"Gold tables rewritten in {config.GOLD_TABLES_DIR}")
    else:
        run_all()
