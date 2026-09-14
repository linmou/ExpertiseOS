# 08 — Requirement Traceability Matrix

## Purpose

Use this file to prevent scope drift. Every P0 PRD requirement has an implementation owner and a validation path.

If an agent proposes new architecture that does not help satisfy one of these rows, it is probably out of scope.

## Functional requirements

| Requirement | Minimal implementation | Primary plan/work packet | Primary validation |
|---|---|---|---|
| FR-01 Onboarding and automatic activation | Guided setup, supported host registration, consent, health check, compact policy/control load, capability reporting | `01_g0_feasibility_and_repo_bootstrap.md`, WP5, WP6 | AT-01, host contract tests |
| FR-02 Candidate detection | Host-model retrieval/comparison, exact duplicate suppression, no usefulness score, uncertainty-safe language | `03_g2_retrieval_learning_and_controls.md`, WP3, WP8 | AT-02, model-behavior fixtures |
| FR-03 Collection proposal | Exact content + reason + source scope + optional category/links, Save/Edit/Skip; narrow same-event direct-save for clearly identified material | WP2, WP5, WP6, shared skill + WP8 | AT-02, AT-04, AT-07 |
| FR-04 Approval before persistence | Volatile proposal + host-originated one-use decision grant + exact digest/version binding + guarded commit | `02_g1_core_consent_and_storage.md`, WP2, WP5, WP6 | AT-04, AT-06 |
| FR-05 Candidate lifecycle/refusal | In-memory state machine, session expiry, unrelated-message expiry, session-only decline suppression | WP1, WP5, WP6 | AT-05, AT-06 |
| FR-06 Reflection/deeper knowledge | One optional prompt, contribution origin, separate derived proposals | `03_g2_retrieval_learning_and_controls.md`, WP4, WP8 | AT-07, AT-08, AT-09 |
| FR-07 Organization/revision | Guarded categorize/link/split/merge/edit/retire operations composed from the same approval/version primitives, lineage, conflict coexistence | WP2, WP3 | AT-08, AT-12, AT-14 |
| FR-08 Contextual recall | Bounded approved retrieval with conditions/conflicts/provenance/version/learner state, direct assistance allowed | WP3, WP8 | AT-02, AT-11, recall tests |
| FR-09 Learner state | Approved evidence per object/version/scope; deterministic state summary; self-report separate | WP4 | AT-09, mastery tests |
| FR-10 Target/fatigue controls | Daily/weekly target, effort accounting, rest interval, explicit pause precedence | WP4 | AT-10, AT-11 |
| FR-11 Inspection/deferred learning | Inspect saved/provenance/links/evidence; minimal deferred refs to approved objects | WP4, WP8 | inspection tests, deferred tests |
| FR-12 Shared local state across hosts | One service/repository, session-scoped proposals, version conflicts, global reflection counts | WP5, WP6, WP8 | AT-12 |
| FR-13 Export/deletion/uninstall | Portable export/restore, retire/delete, index cleanup, explicit uninstall data choice | `05_export_delete_reliability_security.md`, WP7 | AT-14 |
| FR-14 Failure/recoverability | Fail-open work, no false Saved, idempotency, canonical-before-success, index repair from approved data | WP2, WP3, WP7 | AT-13 |

## Learner-state policy

| Policy | Minimal implementation | Owner | Validation |
|---|---|---|---|
| `new → recognized → explained → applied → transferred → autonomous` | Enum + deterministic evidence summary | WP4 | mastery transition tests |
| Save does not imply understanding | Save creates/retains `new` only | WP4 | AT-07, AT-09 |
| User contribution required for explanation | Evidence parser/proposal must identify user contribution | WP4, WP8 | AT-09 |
| Unknown contribution is insufficient | `insufficient_evidence`, no upward state | WP4 | AT-09 |
| Autonomous heuristic | 2 independent successes, distinct tasks/sessions, >=1 transfer, no relevant contradiction, explicit user agreement | WP4 | autonomy heuristic test |
| Revised/new boundary may invalidate applicability | retain evidence scope/version; flag review, do not erase history | WP4 | version/evidence tests |

## Learning target/control policy

| Policy | Minimal implementation | Owner | Validation |
|---|---|---|---|
| Daily/weekly reflection target | persisted settings + period counters | WP4 | target tests |
| Qualifying reflection counted once | explicit reflection event ID + one count per completed approved activity | WP4 | reflection counting test |
| Effort units 0.25/1/2 | deterministic highest-category accounting per user response | WP4 | effort tests |
| Six-unit default limit | configurable setting | WP4 | effort-limit test |
| 60-minute default rest | configurable rest interval | WP4 | fatigue tests |
| Target satisfied != fatigue | distinct state/precedence | WP4 | AT-10 |
| Pause keeps approved recall | control resolver | WP4, WP8 | AT-11 |
| Disable stops expertiseOS recall | control resolver/tool guard | WP4, WP8 | pause/disable test |

## Data/traceability requirements

| Record | Implementation home | Validation |
|---|---|---|
| Knowledge object | Basic Memory adapter + domain model | exact-write/provenance/read tests |
| Relationship | backend adapter + guarded semantic change | relationship round-trip/approval tests |
| Source reference | knowledge metadata/provenance mapping | provenance tests |
| Approval record | SQLite `approval_receipts` | AT-04/AT-06 |
| Learning evidence | SQLite learner evidence | AT-09 |
| Control state | SQLite control state/counters | AT-10/AT-11 |

## Non-functional requirements

| Requirement | Minimal implementation | Owner | Validation |
|---|---|---|---|
| NFR-01 No unapproved content persistence | in-memory candidate/grants; no candidate logs/index/temp; persistent-store marker audit | WP1, WP2, WP7 | AT-05, no-candidate-persistence audit |
| NFR-02 Minimal data exposure | local service, bounded retrieval, no content telemetry/cloud sync, persisted simple scope exclusions enforced by adapters/retrieval | WP3, WP4, WP5, WP6, WP7 | AT-01, AT-16, scope-exclusion/retrieval tests |
| NFR-03 Safe stored knowledge | untrusted retrieval contract, service-enforced approval/control rules, minimal secret handling | WP7, WP8 | AT-15 |
| NFR-04 Fail open for work / closed for writes | adapter/service error handling, write health guard | WP2, WP5, WP6, WP7 | AT-13 |
| NFR-05 Responsiveness/scale | simple benchmark, no per-event LLM call, bounded retrieval | WP3, WP7 | performance checks |
| NFR-06 Non-technical usability | guided setup/chat-native controls/export/uninstall, clear errors | WP5, WP6, WP7, WP9 | AT-01, AT-14, final pilot readiness |

## Architecture constraints

| Constraint | Implementation decision |
|---|---|
| Shared skill + thin host adapters | one `skill/SKILL.md`, host translation only under `hosts/` |
| Local expertiseOS service | one local process; no cloud expertiseOS backend |
| Basic Memory behind adapter | `KnowledgeBackend` contract + `backends/basic_memory.py` |
| No unrestricted backend write tool | only guarded knowledge service is host-facing |
| No second generative model | semantic interpretation stays with current host LLM |
| Local retrieval | Basic Memory/local index + keyword fallback |
| No candidate embeddings | only approved data enters index |
| Versioned writes | optimistic expected-version checks |
| Shared host state | both adapters use same service/repository |
| Same-user OS caveat | document threat model; do not claim hostile-process isolation |

## Acceptance tests to work packets

| Acceptance test | Main work packets |
|---|---|
| AT-01 | WP0, WP5, WP6, WP9 |
| AT-02 | WP3, WP8 |
| AT-03 | WP5, WP6, WP8 |
| AT-04 | WP2, WP3, WP5, WP6 |
| AT-05 | WP1, WP2, WP7 |
| AT-06 | WP2, WP5, WP6, WP8 |
| AT-07 | WP2, WP4, WP8 |
| AT-08 | WP2, WP3, WP4, WP8 |
| AT-09 | WP4, WP8 |
| AT-10 | WP4, WP8 |
| AT-11 | WP4, WP5, WP6, WP8 |
| AT-12 | WP2, WP5, WP6, WP8 |
| AT-13 | WP2, WP3, WP5, WP6, WP7 |
| AT-14 | WP3, WP7 |
| AT-15 | WP2, WP7, WP8 |
| AT-16 | WP0, WP3, WP7, WP8 |

## Delivery gates

| PRD gate | Plan completion condition |
|---|---|
| G0 Host/license feasibility | `01_g0_feasibility_and_repo_bootstrap.md` exit criteria satisfied |
| G1 Consent/storage | WP1-WP3 core approval + canonical storage negative-path tests green |
| G2 Learning behavior | WP4 + shared skill learning/control tests green |
| G3 Cross-host reliability | WP5-WP6 live contract + WP8 cross-host acceptance green |
| G4 Non-technical pilot | install/core-loop/pause/export/uninstall usable without developer intervention; burden/outcome collection documented |

## Drift check

Before accepting a new task or module, ask:

1. Which FR/NFR/AT row does it satisfy?
2. Is the behavior already covered by an existing module?
3. Does it introduce cloud, extra models, background autonomy, team features, or a new UI that the PRD explicitly excludes?
4. Does it weaken exact user approval to simplify integration?
5. Does it persist anything before approval?
6. Does it conflate saved knowledge with learner mastery?

If the task cannot answer question 1, leave it out of the MVP unless a newly discovered feasibility constraint requires it.
