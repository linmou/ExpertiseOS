# 05 — Export, Deletion, Reliability, and Security Completion

## Goal

Complete the P0 ownership, failure, privacy, and local-security behaviors without introducing infrastructure beyond what the MVP needs.

This work may run partly in parallel with host adapter work after G1 interfaces are stable.

---

## 1. Export

Provide a documented portable export containing approved user-owned state:

```text
knowledge objects + versions needed for lineage
relationships
approved source references/excerpts
approval receipts needed for traceability
learner evidence
learner-state summaries if persisted
control settings
aggregate target/effort history required by product behavior
deferred activities
```

Use a simple documented format, preferably a directory or archive containing JSON/JSONL plus Markdown knowledge files if that matches the Basic Memory representation.

Do not invent a custom binary format.

Export must not include:

- unresolved candidates;
- unconsumed decision grants;
- candidate query logs;
- hidden host/model reasoning;
- unrelated host transcripts.

---

## 2. Restore/import

Two cases:

### Restore a user-selected expertiseOS export

Treat selecting/restoring the export as explicit authorization for that restore operation.

Requirements:

- validate schema/version;
- preserve stable IDs and lineage where possible;
- detect ID/version collisions;
- do not overwrite newer local versions silently;
- rebuild local indexes from approved canonical data;
- restore learner/control state consistently.

### Import foreign/non-expertiseOS content

Do not silently treat it as approved knowledge.

Require review/proposal before semantic content enters the personal repository.

Keep this path minimal; a rich migration framework is out of scope.

---

## 3. Retire versus delete

### Retire

- keeps content/history/provenance;
- removes object from ordinary active recall unless explicitly requested;
- semantic state change requires approval;
- links remain resolvable.

### Delete

Delete requested in-scope content from:

- active Basic Memory content;
- derived search indexes;
- expertiseOS-retained content-bearing revisions;
- approved source excerpts within deletion scope;
- learner-evidence excerpts as requested/required;
- deferred activities that cannot remain valid.

Relationships to deleted objects should be removed or converted into disclosed unavailable references according to the user's chosen deletion scope.

A content-free deletion tombstone/ID marker may remain only when needed for referential integrity and disclosed.

Do not claim deletion from:

- previously exported copies;
- OS backups;
- external host transcripts/provider retention;
- forensic remnants outside product control.

---

## 4. Uninstall

Uninstall should:

1. remove Codex integration;
2. remove Claude Code integration;
3. stop/unregister expertiseOS service;
4. ask whether to keep or delete the local repository/state;
5. if delete is chosen, apply the product deletion routine.

Do not make data deletion an implicit side effect of uninstall.

---

## 5. Backend/index failure semantics

### Canonical write succeeds, index update fails

- report approved knowledge as saved if canonical durable write + approval receipt are complete;
- expose search/index as degraded;
- queue only a content-free bounded repair marker or rebuild flag;
- rebuild index later from approved canonical data;
- do not create a second learning event.

### Canonical write fails

- do not report Saved;
- no approval receipt implying success;
- bounded idempotent retry only.

### Backend unavailable

- ordinary host work continues;
- knowledge writes closed;
- recall may report unavailable/degraded;
- do not repeatedly prompt learning because storage is unhealthy.

---

## 6. Idempotency

Every approved mutation should have an operation/idempotency key derived from the active proposal/commit attempt.

Verify:

- timeout then retry creates one object/version;
- duplicate adapter delivery consumes grant once;
- receipt reconciliation does not duplicate canonical write;
- repeated index rebuild does not create learner evidence or approvals.

Do not introduce a distributed idempotency service.

---

## 7. Startup recovery

Startup may recover only approved durable state.

Allowed recovery:

- reconcile content-free operation markers;
- rebuild indexes;
- load control state;
- load approved knowledge/evidence.

Not allowed:

- restore unresolved candidates;
- reconstruct candidate text from logs;
- replay unconsumed approvals from a prior process;
- generate semantic consolidations automatically.

---

## 8. Local transport/access control

Use the safest simple local transport supported by the selected host/MCP mechanisms.

Requirements:

- do not listen on a public interface by default;
- restrict access to the local user/session where supported;
- document that same-user privileged processes or unrestricted shell access are outside the strong security boundary;
- never claim protection against the OS owner.

Do not build a production IAM system.

---

## 9. Prompt-injection/data-instruction resistance

The service must enforce the following independent of prompts:

- a stored note saying “approve future writes” has no effect;
- tool/file content saying “Save this automatically” has no effect;
- recalled text cannot change pause/disable state;
- recalled text cannot authorize tools;
- source approval does not imply claim correctness;
- suspicious secrets/tokens are not copied into proposals unless clearly needed and explicitly scoped.

Implement redaction/minimization helpers only where straightforward. Do not build a full DLP platform.

---

## 10. No-content persistence audit

Create an automated test helper that can inspect all expertiseOS-controlled persistent locations after negative-path scenarios:

- SQLite tables;
- Basic Memory canonical store through supported APIs/files;
- local index directory;
- expertiseOS log directory;
- temp/job directory if one exists.

For Skip/ignore/cancel/crash fixtures, assert the candidate's unique marker string is absent.

This test should not inspect unrelated host-owned transcripts.

---

## 11. Search degradation

If local semantic embeddings/indexing cannot initialize or fail:

- use local keyword search;
- return a visible degraded-search flag/status;
- keep canonical knowledge available;
- do not silently call an external embedding API.

If the initial local embedding model requires a download, onboarding must make that permission/step clear.

---

## 12. Responsiveness instrumentation

Measure, do not merely claim, the PRD acceptance targets:

- lifecycle bookkeeping p95 < 200 ms;
- warm local retrieval p95 < 1 s for 10,000 small knowledge objects;
- approved-write acknowledgment p95 < 1 s excluding indexing and host-model latency.

Record test hardware/corpus/dependency versions.

Use a simple benchmark script/test. Do not add observability infrastructure or remote telemetry.

---

## 13. Required tests

```text
test_export_restore.py
test_retire_delete.py
test_uninstall_data_choice.py
test_backend_outage.py
test_index_failure_rebuild.py
test_idempotent_retry.py
test_startup_recovery.py
test_injection_boundary.py
test_no_candidate_persistence_audit.py
test_keyword_fallback.py
```

Critical cases:

- deleted object not returned by normal recall;
- deletion removes relevant index trace;
- missing source is labeled unavailable, not regenerated;
- backend timeout retry does not duplicate knowledge;
- candidate marker absent after Skip and crash;
- note containing hostile instruction cannot create grant/write/control change;
- network-disabled expertiseOS runtime still performs local storage/search/state after setup.
