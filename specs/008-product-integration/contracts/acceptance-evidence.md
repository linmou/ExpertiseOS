# Contract: Acceptance Evidence

**Intent**: Make each component acceptance result reproducible and suitable for the integration owner's machine-validated coverage manifest.

## Required Fields

Each AT run records:

```text
schema_version
at_id
tested_sha
command
exit_code
started_at
finished_at
environment
fixture_versions
producer_consumer_edges
edge_artifacts
result
output_path
```

`result` is `pass`, `fail`, or `not_applicable`. `not_applicable` requires an explicit host/capability reason and cannot be used to hide a required P0 case.

The integration review records the later mapping from `tested_sha` to a promotion SHA only after post-test audit and smoke gates pass. The test-run evidence does not require or predict that promotion SHA.

## Handoff Proof

For every declared producer-consumer edge, evidence identifies the actual upstream artifact and downstream observation from the same test/run. A fake may drive host events where specified, but it cannot replace the promoted upstream service at the boundary being proved.

## Safety

Evidence must not persist unapproved candidate payloads, unrelated prompts, secrets, or complete vault content. Marker-token negative tests record only the marker identity and audit result after the audited locations are checked.

## Verdict Rule

Any applicable consent, privacy, or state-integrity failure blocks promotion. Model-behavior scores, misses, and false proposals are reported separately and cannot offset deterministic failures.
