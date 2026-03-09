# pyntlp — build plan v0.1

Target: deliver the public pip-installable `pyntlp` package for generic SSO-to-load-profile modelling.

## Chunk 1 — Package scaffold and naming
Scope: establish the public repo and packaging baseline.

Tasks:
- Create the repo structure for `pyntlp`.
- Add `pyproject.toml`, versioning, and minimal dependencies.
- Add a minimal import smoke test.
- Confirm public naming across package, docs, and examples.

Output:
- Installable package skeleton for `pyntlp`.

Done when:
- `import pyntlp` works in a clean Spark-capable environment.

## Chunk 2 — Public contracts and YAML template
Scope: define the generic public interface.

Tasks:
- Finalise required baseline, segment-attribute, and smart-meter input schemas.
- Create the public YAML template with `constants:` and `parameters:`.
- Add validation for required keys and types.
- Keep the template free of any Ausgrid-specific references.

Output:
- Stable public contract plus `load_params(path_or_dict)`.

Done when:
- Invalid YAML fails fast and valid YAML produces a normalised params dict.

## Chunk 3 — Interval and window utilities
Scope: implement reusable time-window logic.

Tasks:
- Convert `window_start` and `window_end` into interval sets.
- Define the start-inclusive / end-exclusive convention.
- Compute donor intervals and interval hours.
- Add deterministic unit tests for boundary cases.

Output:
- `get_window_intervals(params) -> (W, D, interval_hours)`.

Done when:
- Window mapping is fully deterministic and tested.

## Chunk 4 — Segment eligibility engine
Scope: compute segment-level eligibility from normalised inputs.

Tasks:
- Join segment attributes to smart-meter inputs on normalised `nmi`.
- Implement residential pattern, smart-meter, and DER filters from YAML.
- Compute `n_total`, `n_eligible`, and `eligibility_rate` by segment.
- Handle nulls and missing combinations safely.

Output:
- `build_segment_metrics(...)` returning one metrics row per segment.

Done when:
- Eligibility rates match expected outputs on controlled samples.

## Chunk 5 — Adoption and ramp model
Scope: project eligibility into FCY-specific participation.

Tasks:
- Implement `u(segment)` using default + overrides.
- Implement the FCY linear ramp.
- Join segment metrics onto baseline rows.
- Produce row-level `adoption_rate`.

Output:
- Baseline rows enriched with segment metrics and adoption.

Done when:
- Spot checks confirm correct behaviour before, during, and after rollout years.

## Chunk 6 — PMA energy-shift engine
Scope: convert policy parameters into interval deltas.

Tasks:
- Compute daily energy by baseline group.
- Compute `E_shift`, participant cap, and capped shift.
- Allocate flat uplift inside the window and flat donor reduction outside it.
- Convert interval MWh deltas into `pma_sso_mw`.

Output:
- `compute_pma_sso(...)` returning the required output schema.

Done when:
- The engine is energy-neutral within each baseline group and respects the cap.

## Chunk 7 — Validation, tests, and release baseline
Scope: make the public package production-ready.

Tasks:
- Implement `validate_pma(...)`.
- Add unit tests for schema, neutrality, cap binding, and ineligible-zero logic.
- Add a tiny Spark integration test.
- Draft README usage examples and release notes.

Output:
- Public MVP of `pyntlp` ready for release.

Done when:
- A user can install `pyntlp`, load params, run the model on normalised sample DataFrames, and validate the result.
