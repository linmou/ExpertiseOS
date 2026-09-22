# Research: Learner Evidence and Learning Controls

**Intent**: Record decisions already fixed by the approved MVP plan and remove implementation ambiguity without expanding scope.

## Deterministic Mastery

**Decision**: Derive mastery from approved evidence filtered by knowledge ID, applicable knowledge version, and scope. Only `pass` contributes to advancement. Use explicitly instantiated positive integer pass-count thresholds for the five advancement states, require them to be nondecreasing, and return the evidence IDs supporting the result. Evidence approved at a higher state may satisfy a lower state's count, preserving the plan's higher-quality evidence rule.

**Rationale**: This keeps the result explainable and preserves the separation between saved knowledge and demonstrated learner performance.

**Alternatives considered**: Partial-credit advancement, point scores, confidence probabilities, and global seniority were rejected because the canonical decision permits only pass-count advancement and the MVP excludes psychometric scoring.

## Autonomous Qualification

**Decision**: Evaluate the pilot rule literally: the configured autonomous independent-pass threshold is at least two, demonstrations use distinct tasks and separate sessions, at least one is a meaningful transfer, no relevant contradiction is unresolved, and the user explicitly agrees to reduce scaffolding. Numeric configuration cannot disable or weaken these guards.

**Rationale**: Each condition is independently testable and inspectable.

**Alternatives considered**: Time-based promotion, repeated retrieval, self-report, and weighted scoring were rejected as unsupported behavior.

## Threshold Persistence

**Decision**: Store the five user-owned integer thresholds with control settings through C002's versioned approved state boundary. Instantiate defaults explicitly as `1, 1, 1, 1, 2` for recognized through autonomous; reject zero, negative, decreasing, or autonomous-below-two values.

**Rationale**: This is the smallest adjustable representation, obeys the no-dataclass-default rule, and makes changes inspectable without introducing scoring or a separate configuration system.

**Alternatives considered**: Hard-coded constants are not adjustable; arbitrary weights and per-evidence scores exceed the requested numerical configuration.

## Evidence Applicability

**Decision**: Retain evidence history and filter its mastery contribution by exact knowledge version and compatible scope. A knowledge revision does not delete evidence or silently carry it forward.

**Rationale**: Revision may change the claim or boundary; retaining but not assuming applicability preserves provenance and avoids false promotion.

**Alternatives considered**: Automatic migration to the latest version and deletion of old evidence were rejected because both hide meaning changes.

## Control Resolution

**Decision**: Produce a pure effective-control result with this precedence: disabled, explicit pause, active fatigue rest, target satisfied, ordinary active learning. The result exposes separate permissions for observation, collection prompts, proactive exercises, and approved recall.

**Rationale**: Separate permissions encode the required differences without scattered boolean checks.

**Alternatives considered**: One `learning_enabled` boolean and a generic policy engine were rejected because the first loses distinctions and the second is unnecessary.

## Time Periods and Effort

**Decision**: Calculate daily or weekly period keys in the configured local device timezone. Classify each actual user response once at the highest applicable effort level: 0.25, 1.0, or 2.0. Record one idempotency identifier per evidence, reflection, or effort event.

**Rationale**: This matches the explicit defaults and prevents cross-host/retry duplication.

**Alternatives considered**: Background reset jobs, summing overlapping effort categories, and counting ordinary tool activity were rejected.

## Reflection Counting

**Decision**: Count one approved reflection event if it includes meaningful user contribution, develops reusable knowledge, connects to approved knowledge/evidence, and was saved through approval. Linked output count does not affect progress.

**Rationale**: The activity, not the number of storage objects, represents learner effort.

**Alternatives considered**: Counting each created object, raw interaction length, or assistant-produced content was rejected.

## Persistence Ownership

**Decision**: C004 owns validation/calculation and requests minimal tables through C002's shared state API and migration owner. Omit a learner summary cache initially because evidence volume is small and the summary is regenerable.

**Rationale**: This avoids concurrent edits and duplicate writers while keeping SQLite as the sole learner/control store.

**Alternatives considered**: Direct SQLite access from learning modules, a second database, and a repository layer per table were rejected.

## Deferred Learning

**Decision**: Persist only activity identity, approved object/version references, activity type, creation time, and status after explicit approval. Selection occurs only during a later active foreground session.

**Rationale**: This meets deferment without retaining candidate content or creating background work.

**Alternatives considered**: Free-form activity prompts, notifications, a scheduler, and transcript snapshots were rejected.
