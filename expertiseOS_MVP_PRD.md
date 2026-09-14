# expertiseOS — MVP Product Requirements Document

**Date:** September 14, 2026  
**Status:** Product specification for implementation and validation  
**Audience:** Product, engineering, learning design, and evaluation  
**Release scope:** Personal, local-first learning extension for supported local Codex and Claude Code environments

## 1. Product definition

**expertiseOS helps individuals develop expertise while working with an AI assistant.** It turns human–AI work into opportunities to generate, collect, organize, recall, and apply knowledge. The person controls what is retained and participates in learning before support is reduced with demonstrated mastery.

The same approved knowledge also helps the assistant perform future work more accurately and consistently. Improving the assistant and developing the person are related but distinct outcomes.

The core loop is:

**Work → detect new or conflicting knowledge → reach a safe conversational checkpoint → obtain a storage decision → save only approved material → optionally reflect and organize → recall and apply later → update evidence of mastery → adjust scaffolding.**

Task execution and learning are separate workflows. They may share the host model and conversation; the product does not require two models, two autonomous agents, or simultaneous model inference.

### 1.1 Primary user and problem

The primary user is an individual who uses an AI assistant for real work and wants the experience to build personal expertise, not only produce better deliverables. The user may be non-technical. Initial examples span analysis, programming, design, professional writing, and other knowledge work; the knowledge model is not restricted to coding.

A useful work interaction can produce an observation, correction, explanation, or exception. expertiseOS helps the user decide whether to retain it, connect it to prior knowledge, and use it in a later situation. It does not equate an excellent AI-assisted output with the user's independent understanding.

### 1.2 Product outcomes

| Outcome | What success means |
|---|---|
| Personal learning | The user develops reusable knowledge and can later recognize, explain, apply, and transfer it with less assistance. |
| Better task assistance | The host assistant uses the user's approved knowledge appropriately, with its conditions, evidence, and uncertainties. |
| User ownership | The user can inspect, correct, export, and delete personal knowledge and learning records. |
| Sustainable participation | Learning effort stays within user-controlled limits without preventing completion of the underlying work. |

The long-term hypothesis is that a junior's high-level knowledge can approach that of an unaided senior within a defined domain. This is an evaluation target, not an MVP performance guarantee or a claim about equivalent titles, authority, or experience.

## 2. Scope and settled decisions

| Area | MVP requirement |
|---|---|
| User | One individual; personal ownership. |
| Hosts | Both local Codex and Claude Code adapters, sharing one behavioral specification and one personal repository. |
| Activation | Automatically active in supported sessions after installation and onboarding consent; no repeated manual skill invocation. |
| Intelligence | The user's current host LLM performs detection, comparison, reflection, organization, and interpretation. |
| Deployment | Local expertiseOS service, local knowledge backend, local learner-state database, and local retrieval indexes. |
| Model setup | No expertiseOS cloud account, separate generative-model configuration, or additional LLM API key. |
| Knowledge backend | Basic Memory, behind a replaceable adapter; no deep fork or multiple competing memory engines. |
| Collection | User approval of the proposed content before persistence. |
| Interaction | Chat-native Save / Edit / Skip; optional host-native controls are conveniences, not a required separate application. |
| Timing | Earliest safe conversational checkpoint; never interrupt an atomic tool operation. |
| Learning | Reflection, organization, retrieval practice, and transfer exercises can be postponed or skipped. |
| Mastery | Per knowledge object, separate from knowledge category, validity, and task success. |
| Learning controls | User-configurable daily or weekly reflection target, effort limit, and fatigue-rest interval. |
| Collaboration | Not in the MVP. Preserve an exportable structure for future selected sharing and review. |

**Host naming:** “Claude” in this implementation scope means Claude Code's local agent environment. Standard Claude chat, browser-only hosts, remote Codex workers, and other surfaces are not automatically covered. Engineering must publish exact tested host surfaces, versions, operating systems, and permission modes before release. This is a compatibility test obligation, not a new user configuration decision.

**Meaning of local-first:** expertiseOS-controlled storage, indexing, state, and service execution remain local. The selected host model may still be provider-hosted. Knowledge returned to that model is processed under the host's configuration. The product must not claim that all inference is offline or that recalled content never leaves the device.

### 2.1 Explicit non-goals

The MVP does not include team administration, organization-wide monitoring, manager access, organizational merge workflows, cloud synchronization, a new general-purpose chat client, autonomous background transcript harvesting, automatic retention of inferred personal profiles, model fine-tuning, or a single global “seniority score.” It does not build six different databases for the six knowledge categories.

## 3. Knowledge model

### 3.1 Three knowledge subjects

Knowledge may concern **the domain**, **the user**, or **AI**. A record may involve more than one subject. Knowledge about the user must be framed as a revisable, scoped observation rather than a permanent personal diagnosis. Knowledge about AI must retain relevant model, tool, task, and date context when available.

### 3.2 Six knowledge categories

| Category | Stored content | Example of a learning prompt |
|---|---|---|
| 1. Declarative | Facts, concepts, observations, definitions, and explicit claims. | “What is the claim, and what supports it?” |
| 2. Structural & procedural | Relationships, dependencies, and ways of carrying out work. | “How does this change the sequence or dependencies of the work?” |
| 3. Conditional & boundary | Applicability conditions, exceptions, and cues that distinguish cases. | “When would the usual approach stop working?” |
| 4. Causal / mechanistic | Explanations, mechanisms, and intervention hypotheses. | “Why might this happen, and what evidence would distinguish the explanations?” |
| 5. Episodic & tacit experiential | Experiences, observations, salient cues, decisions, and outcomes, including examples that are not fully verbalized. | “What did you notice here that you might otherwise have missed?” |
| 6. Goal, metacognitive & normative judgment | Objectives, uncertainty, reasoning limitations, evidence standards, and trade-offs. | “What matters in this situation, and what would make you verify, escalate, or reconsider?” |

Categories guide representation, linking, and scaffolding. They are not mandatory developmental steps, a ranking of all knowledge, or a rule that higher-numbered categories are always more valuable. The user decides what is worth learning.

### 3.3 Objects, relationships, and evidence

Store separate but linked objects when claims have different meanings or evidence. An episode, a boundary principle derived from it, and a causal hypothesis need not be merged into one note. A single object may use more than one category when separation would be artificial.

A newly approved item may remain uncategorized until the user chooses to organize it. Classification is not a prerequisite for saving. Suggested classifications and meaningful relationships are shown to the user for confirmation, potentially in the same approval as the item.

Relations can include `derived_from`, `supports`, `contradicts`, `explains`, `example_of`, `applies_when`, and `depends_on`. A relationship also needs traceability; adding it can be a substantive knowledge change.

**Permission to store, evidential status, and mastery are independent.** A saved hypothesis can remain uncertain, and a correct saved principle can remain unfamiliar to the user.

## 4. Two-workflow operating model

### 4.1 Work workflow

The host continues to own the task goal, plan, tools, permission checks, and results. expertiseOS may supply approved knowledge, but it does not become a replacement task orchestrator.

### 4.2 Learning workflow

The learning workflow observes context already available within the authorized host session. It detects candidates, requests collection decisions, offers optional learning, and manages approved learning records.

“Whole working context” includes user messages, assistant responses, artifacts, files the host actually accessed, tool results, errors, decisions, and outcomes. It does not authorize device-wide scanning, unrelated historical-session ingestion, independent browsing of private files, or access to hidden model reasoning. An event unavailable to the host adapter is not claimed to have been observed.

### 4.3 Safe checkpoints and pending candidates

A safe checkpoint is a point at which the host can present a learning interaction without leaving an atomic operation incomplete or interfering with an urgent task obligation. Examples include a completed tool call with a stable result, the end of a bounded multi-tool operation, or a normal conversational handoff.

A candidate detected earlier stays in volatile memory until that checkpoint. It must not be written to temporary files, durable queues, transcripts owned by expertiseOS, embeddings, or background summaries.

At the checkpoint, present the storage decision before moving substantially beyond the insight. Do not delay all collection until the end of a task. Related simultaneous candidates may appear in one concise, itemized proposal; batching must not hide an already available decision opportunity.

The product never requires a reflection answer or learning-target completion to continue work. A pending collection decision blocks that write, not unrelated authorized task steps. The user may skip or ignore it and continue. The host may nevertheless require another conversational turn to proceed; separate workflows do not imply independent execution while the host itself is awaiting input.

## 5. Functional requirements

**Priority convention:** P0 is required for MVP release. P1 is an improvement that must not delay P0 validation. All numbered requirements below are P0 unless explicitly marked otherwise.

### FR-01 — Onboarding and automatic activation

Provide a guided setup for both supported hosts. It detects prerequisites, registers the shared local service and adapter, preserves existing host configuration, and runs a health check. Users must not manually configure Python, databases, embeddings, or model endpoints.

Onboarding explains observation scope, local-storage boundaries, host-model processing, consent, learning-state storage, and pause controls. Only after confirmation does automatic activation begin. Existing host subscriptions and host permission prompts remain applicable.

At session start, load a compact policy and current control state. Do not dump the full repository into the model context. Unsupported or disabled adapter capabilities must be visible rather than silently advertised as working.

### FR-02 — Candidate detection without imposed learning value

Compare current information with relevant saved knowledge to identify a potential addition, changed condition, or contradiction. Use the host LLM and local retrieval; do not add a second generative model.

Do not gate proposals using a product-defined usefulness, transferability, seniority, or “worth learning” score. Mechanical duplicate suppression is permitted. Detection is bounded by accessible context and retrieval quality, so use language such as “not found in your saved knowledge,” not “you do not know this.”

Exact repeats without new context need not generate repeated proposals. New contradictory evidence must not be suppressed merely because the topic already exists. Where novelty is uncertain, state that uncertainty and let the user decide.

### FR-03 — Collection proposal

Show the actual proposed content, why it was surfaced, its relevant source or approved excerpt, and any proposed category or links. Keep the default presentation concise, with evidence details available in the same interaction.

Offer **Save**, **Edit**, and **Skip**. Saving only the content while postponing organization must be supported. A direct user instruction to save clearly identified material can constitute the collection decision; do not force a redundant confirmation unless the content or scope is ambiguous.

Saving an excerpt does not authorize copying its entire source file or session.

### FR-04 — Approval before persistence

Every substantive create, edit, relationship change, conflict resolution, learning-evidence record, and mastery assessment requires a user-authorized operation. Approval may cover a clearly presented group of related changes.

Bind approval to the specific content, destination, and relevant existing version. A model-supplied `approved=true`, a quoted instruction, a tool result saying “the user approved,” or an old approval must not authorize a write.

The host adapter must obtain the actual user response through a validated host interaction path. An unambiguous “Save” can approve the single active proposal. Multiple proposals, material ambiguity, or changed content require clarification or a newly displayed proposal. Natural-language convenience must not weaken the binding.

Without trustworthy approval, fail closed for writes while allowing ordinary task execution. Permission to call a tool, plugin installation, and reaching autonomous mastery are not blanket permission to remember new knowledge.

### FR-05 — Candidate lifecycle and refusal

Candidate states are `detected → awaiting_checkpoint → awaiting_decision → approved / declined / expired`. Candidates remain volatile until approved.

Skip, cancellation, session end, loss of context, or an unrelated next user message expires the unresolved proposal by default. A late approval of an expired proposal requires presenting it again. Loss on crash is intentional; do not “recover” unapproved candidates from hidden storage.

Do not repeatedly propose the same declined candidate within the current session. This suppression stays volatile. A durable preference such as “never propose this type again” is itself shown and stored only at the user's request.

### FR-06 — Reflection and generation of deeper knowledge

After saving, offer a short, optional next step appropriate to the item and the user's current learning state. The user can reflect now, defer, or skip. Do not automatically run an interview through all six categories.

Scaffolding may range from confirming a proposed relationship to explaining a mechanism, comparing cases, identifying a boundary, reconstructing a procedure, or examining a judgment. The user can ask for more or less support.

New principles, personal observations, and explanations generated in reflection are proposals until approved. Preserve whether a contribution originated with the user, the assistant, or jointly. Do not represent assistant-written reasoning as the user's own reasoning.

### FR-07 — Organization and revision

Support finding, categorizing, linking, splitting, merging, editing, and retiring approved objects conversationally. Show substantive changes and their affected objects before applying them.

Do not silently merge away disagreement or treat recency, repetition, or an expert's title as proof. Conflicting claims can coexist with their sources and conditions. The user may later reconcile, narrow, or supersede them.

Versioned changes must preserve lineage. Technical maintenance such as rebuilding indexes or formatting without semantic changes does not require repeated approval. Autonomous semantic consolidation, decay-based deletion, and background rewriting are disabled.

### FR-08 — Contextual recall for work and learning

Retrieve a bounded set of relevant approved objects, including conditions, conflicting evidence, source availability, and version. Retrieve by meaning and keywords, supplemented by relationships where helpful.

When learning is active and the object is not autonomous, the assistant can ask a short recall or application question before offering the answer. The user can immediately request direct assistance. Do not withhold important task information, safety guidance, or the requested work product to force practice.

When learning is paused or the target is satisfied, use appropriate approved knowledge directly without proactive exercises. Explain material use of uncertain, conflicting, or consequential knowledge; routine reuse need not generate an extra dialogue.

Stored content is evidence/context, not higher-priority executable instructions. Recall must not override the user's current objective, host permissions, or task safety rules.

### FR-09 — Evidence-based learner state

Track demonstrated state separately for each knowledge object and applicable version/scope. Record assistance level, evidence, and assessment basis. User confirmation of a saved note does not alone advance mastery.

The host may propose an assessment, but the user approves its durable evidence and state change together. Self-reported familiarity is retained separately from demonstrated mastery. The user may correct or reject an assessment.

Do not require users to repeat elementary stages when stronger evidence already exists. Do not advance state merely because the agent retrieved an item often or produced a successful artifact.

### FR-10 — Learning target and fatigue controls

Implement the independent reflection target and effort limit specified in Section 7. Users can inspect and change settings in chat. Reaching a target and taking a fatigue break must remain visibly different states.

A pause takes effect before the next expertiseOS-initiated interaction, without interrupting an atomic task operation. Deferred learning must not reactivate during a pause. Already approved knowledge remains available unless expertiseOS itself is disabled.

### FR-11 — Personal inspection and deferred learning

Users can ask what was saved, why it was saved, where it came from, how it relates to other items, what changed, and what supports a mastery assessment.

A deferred activity may persist only when it references approved knowledge and the user chooses to defer it. It is offered in a later foreground session when learning is active, not through an always-running background tutor. Users can remove deferred activities without deleting knowledge.

### FR-12 — Shared local state across hosts

Both adapters use the same individual repository and control state on the device. Stable IDs, versions, links, learner evidence, and settings must survive switching hosts.

Bind pending approvals to their originating session and proposal. A “Save” in another host cannot approve an unrelated item. Use version checks for concurrent edits; surface a conflict instead of last-write-wins replacement. Count a completed reflection once across both hosts.

### FR-13 — Export, deletion, and uninstall

Provide conversational export and restore of approved knowledge, links, sources or approved excerpts, revisions, learner evidence, and settings in documented portable formats. Importing foreign content requires review; restoring a user-selected expertiseOS export is an explicit user-authorized operation.

Support retiring knowledge separately from deleting it. Deletion removes content from active files, derived indexes, retained expertiseOS revisions, and learning-evidence excerpts as requested. Explain consequences for linked objects and mark unavailable provenance rather than fabricating replacements.

Previously exported copies, OS backups, and host transcripts are outside automatic deletion. Do not promise forensic erasure from physical storage. Uninstall removes integrations and stops the service; keeping or deleting the local repository is an explicit choice.

### FR-14 — Failure handling and recoverability

An unavailable backend or failed learning hook must not prevent the host from completing normal work. Failed writes must not produce a “Saved” message. A retry must not duplicate an approved item or reflection event.

Approved content is durable before success is reported. It must be readable by ID immediately; search-index readiness is a separate status. Index failures preserve the approved source and trigger a bounded repair path. Startup recovery uses only previously approved material.

## 6. Learner-state policy

The ordered labels are **new → recognized → explained → applied → transferred → autonomous**. These are product-level evidence summaries, not validated psychometric stages or estimates of a person's entire ability.

| State | Minimum meaning | Insufficient evidence |
|---|---|---|
| New | Approved knowledge exists; stronger demonstrated familiarity is not established. | Saving alone does not imply understanding. |
| Recognized | The user identifies a relevant concept or cue in a suitable recognition task. | “Yes, save it.” |
| Explained | The user gives a materially correct explanation in their own contribution. | Accepting an explanation written entirely by the assistant. |
| Applied | The user uses the knowledge in a relevant task; the assistance level is known. | A correct artifact with unknown user contribution. |
| Transferred | The user applies or adapts it in a meaningfully different case and handles relevant boundaries. | Repeating the same example with superficial wording changes. |
| Autonomous | Repeated independent use and transfer support reduced scaffolding within a stated scope. | A single successful response or frequent retrieval by the agent. |

For MVP implementation, each evidence event must identify the task, criterion, outcome, assistance level, scope, object version, and user-approved evidence. Outcomes include pass, partial, fail, and insufficient evidence. “Insufficient evidence” must not be converted into failure.

**Initial autonomy heuristic, adjustable during pilot:** at least two approved independent successful demonstrations on distinct tasks in separate sessions, including at least one meaningful transfer; no unresolved relevant contradiction; and explicit user agreement to reduce scaffolding. This is a conservative product heuristic, not a scientific validation threshold.

An uncertain model judgment can be proposed for review but must not silently count as success. A host change, knowledge revision, or new boundary case may make past evidence inapplicable; retain its original scope and flag the need to review rather than erasing history or automatically claiming universal mastery.

Autonomous state reduces instructional participation. New storage and substantive changes still require user permission. The user can request practice again at any state.

## 7. Learning target, effort limit, and control states

### 7.1 Two independent measures

**Reflection target:** a daily or weekly target for user-participatory, organized higher-level reflection.

**Effort limit:** a ceiling on learning interaction effort before a rest interval. It is a fatigue-management proxy, not a direct measurement of cognitive load or proof of learning.

The user may stop before either threshold. The product must not shame, lock out, or create compulsory catch-up work for an unmet target.

### 7.2 Qualifying organized reflection

A reflection qualifies when it contains a meaningful user contribution, develops a reusable relationship/procedure/condition/mechanism/experiential interpretation/judgment, connects to approved evidence or existing knowledge, and is saved with user approval.

An uncertain explanation can qualify as reflective work when explicitly labeled and organized as a hypothesis. That does not make it true or establish mastery. A raw event log, relabeling a note as “high-level,” repeated paraphrases, and agent-only output do not qualify by themselves.

Count the completed reflection activity once, even when it produces several linked knowledge objects. A lightweight confirmation is valid participation and consent but, without a meaningful cognitive contribution, does not independently satisfy the reflection target.

### 7.3 Initial configurable defaults

These are editable pilot defaults introduced to make implementation concrete, not established measures or immutable product requirements.

| Setting | Initial default |
|---|---|
| Target period | Daily, using the device's local timezone. A weekly alternative is available. |
| Reflection target | One qualifying organized reflection per day; three per week when the weekly preset is selected. |
| Effort accounting | 0.25 unit for a simple collection/organization decision; 1 unit for a brief recall, explanation, or application response; 2 units for a substantial multi-step reflection response. Use only the highest applicable category per response. |
| Effort limit | Six units in the active learning block. Ordinary task activity and model output alone do not count. |
| Rest interval | Sixty minutes after the effort limit or a fatigue request without a specified duration. |
| Resume | At the next safe foreground checkpoint after the rest interval. An indefinite user pause requires explicit resumption. |

The user can report fatigue at any point. Do not ask one more exercise merely because the remaining effort budget would allow it. Changing the period or target does not erase history or retroactively create mastery.

Persisting minimal aggregate counters and explicit control settings is covered by a transparent onboarding choice. This is not permission to retain unapproved content, detailed behavioral profiles, or per-item assessment evidence.

### 7.4 Behavior by state

| State | Candidate collection | Proactive learning | Task use of approved knowledge |
|---|---|---|---|
| Active | Propose at the earliest safe checkpoint; save only with permission. | Offer appropriate scaffolding; allow defer/skip. | Enabled. |
| Target satisfied | Continue collection decisions while collection is enabled. | Stop proactively initiating exercises for the period. | Enabled, favoring direct assistance. |
| Fatigue rest / learning paused | Suspend detection prompts and discard unresolved candidates. | Suspended. | Enabled. |
| expertiseOS disabled | No observation, collection, or expertiseOS recall. | Suspended. | Disabled; the host's ordinary work continues. |

Control precedence is **explicit disable/pause → active fatigue rest → target-satisfied behavior → ordinary active learning**. A new target period does not cancel an existing pause. Target attainment is not fatigue, and fatigue does not mark the target satisfied.

“Pause learning” suspends collection and instructional interactions but preserves recall for task assistance. “Disable expertiseOS” also stops its recall. A user request for a one-off explanation while paused does not automatically resume collection or background prompts.

## 8. Data and traceability requirements

Use one shared knowledge representation across all six categories. Technical storage formats may differ for content, operational state, and derived indexes; users see one personal repository.

| Record | Required information |
|---|---|
| Knowledge object | Stable ID; version; content; optional categories/subjects pending organization; applicability scope; evidential status; active/retired state; source references; authorship/contribution attribution. |
| Relationship | Stable source/target IDs and versions where needed; type; explanation/evidence; approval and revision information. |
| Source reference | Host/session/event or artifact reference where available; date; locator and checksum when useful; approved excerpt only; accessibility status. |
| Approval record | Approved operation, object/version, displayed content binding, user-event reference, timestamp, and adapter identity. Store only the minimal approved evidence, not unrelated prompt text. |
| Learning evidence | Object/version; user contribution; assessment criterion; outcome; assistance level; context and transfer conditions; approved state change. |
| Control state | User-selected targets, effort budget, aggregate progress, pause/resume state, and deferred activities referencing approved objects. |

Relationships and provenance must remain valid across renames and exports. Referenced sources can become unavailable; record that limitation. Do not replace missing source evidence with a newly generated explanation.

Revisions are retained deliberately after approval. An append-only history must not make the user's deletion request impossible. Content-bearing revisions and excerpts are within deletion scope; a content-free deletion marker may remain for referential integrity where disclosed.

Use optimistic version checks and idempotency for writes. Separate canonical approved data from regenerable search indexes. An index update must never be interpreted as a new user learning event.

## 9. Architecture and integration constraints

### 9.1 Three main components

| Component | Responsibility |
|---|---|
| Shared expertiseOS skill plus thin host adapters | Behavioral instructions; activation; accessible session events; safe checkpoints; chat interaction; verified user-input handling. |
| Local expertiseOS service | Consent checks; knowledge-operation validation; learner and control state; provenance; export/deletion; backend access. |
| Basic Memory adapter and local backend | Approved note storage, metadata/relationships, indexing, and retrieval. |

Do not expose the backend's unrestricted write interface alongside the controlled expertiseOS interface. Do not adopt stock autonomous capture, sleep-time reflection, semantic consolidation, or deletion routines unchanged.

Basic Memory documents Markdown entities, observations, relationships, MCP access, and local storage. Its configuration supports local embeddings and SQLite, providing relevant building blocks rather than the expertiseOS learning experience. [R5, R6]

### 9.2 Host behavior versus enforceable service rules

Skills guide model behavior; hooks and adapters provide integration points; the service enforces its own state transitions and persistence rules. Neither a skill instruction nor a generic tool-approval permission proves that the person approved the knowledge content.

Current official Codex and Claude Code documentation describes plugins/extensions, MCP, lifecycle hooks, and user-prompt events. These make the proposed integration plausible; they do not prove exact parity, complete event visibility, or a comprehensive security boundary. Codex's hook documentation specifically warns that some tool paths may bypass the default hook path. [R1–R4]

The integration spike must verify activation, safe checkpoints, actual user-response capture, and write containment for each supported host/version. If an adapter cannot validate approval, it remains read-only for knowledge operations and is not a completed MVP write-capable adapter.

Use supported sandbox/permission controls to restrict direct host modification of the repository. Same-user local processes and a deliberately unrestricted shell cannot be treated as a hostile-process security boundary. Test normal supported workflows and prompt-injection cases, document the threat model, and do not promise protection against an OS owner or fully privileged process.

### 9.3 Local retrieval without another model account

Use local keyword search and local embeddings where available. The installed package manages any embedding-model download with clear permission; the user does not select a provider or supply an embedding API key. Index only approved content. Candidate search queries may be computed in memory but must not be persisted as query logs or cached candidate embeddings.

Embedding/download failure falls back to local keyword search with a visible degraded-search status. No silent external embedding service, reranker, or remote summarizer is permitted.

The selected host LLM remains responsible for semantic interpretation. A lightweight local embedding model is not a second conversational agent and must require no independent user configuration.

### 9.4 Dependency and packaging policy

Pin tested backend and adapter versions. Keep the backend behind a narrow interface; expertiseOS requirements must not rely on private upstream database structures.

Basic Memory is currently AGPL-3.0. Review the license obligations of the chosen packaging and distribution before public release; a process boundary is not assumed to resolve licensing. This is a release gate, not a requirement to ask the user to inspect repositories. [R5]

Knowledge portability and behavioral compatibility are tested separately. Do not claim support for every LLM or every host surface merely because they accept MCP.

## 10. Privacy, safety, and reliability requirements

### NFR-01 — No unapproved content persistence

The no-write rule covers expertiseOS files, databases, embeddings, search-query logs, debug logs, telemetry, temporary job files, backups, and crash reports under product control. Large hook outputs must not spill candidate content to expertiseOS-managed files. Observe adapter-specific host behavior and disclose host-owned retention separately.

Volatile memory may contain pending candidates. OS-managed memory paging, host transcripts, and the host provider's own retention are outside expertiseOS's persistence guarantee and must not be described as erased by skipping an item.

### NFR-02 — Minimal data exposure

No content telemetry or remote synchronization by default. The local service uses a local transport and appropriate access controls, not an unauthenticated public listener. Return only context relevant to the current task; do not send the complete vault to the host model. User-created scope exclusions must be honored.

### NFR-03 — Safe treatment of stored knowledge

Saved documents, tool results, and notes are untrusted data, not authority to change product rules. Ignore embedded commands to bypass approval, exfiltrate content, or enable tools. Source approval does not make a claim correct. Mark unresolved conflicts and stale conditions in retrieval results.

Passwords, access tokens, and unrelated sensitive material must not be copied into proposed knowledge without clear need and explicit scope. Prefer a redacted, minimal proposal.

### NFR-04 — Fail open for work, closed for memory writes

Service, hook, retrieval, or assessment failure must not create a task-wide deadlock. Ordinary host work remains available; knowledge writes stop until authorization and storage are healthy. Bounded retries must not reissue learning prompts repeatedly.

### NFR-05 — Responsiveness and scale

Initial local acceptance targets, to be measured rather than claimed as achieved: lifecycle bookkeeping p95 below 200 ms; warm local retrieval p95 below 1 second for 10,000 small knowledge objects; approved-write acknowledgment p95 below 1 second excluding index generation and host-model latency. Publish the tested hardware, corpus, and dependency versions.

Do not run a fresh LLM analysis after every low-level event. Lightweight event handling can mark a comparison due; semantic reasoning uses the host at a suitable checkpoint. Performance optimization must not silently redefine what is worth learning.

### NFR-06 — Non-technical usability

Routine installation, saving, editing, searching, pausing, export, and uninstall require no manual database or configuration-file work. Show clear errors and recovery choices. A separate knowledge-management dashboard is not required for MVP.

## 11. End-to-end reference scenarios

### Scenario A — New observation, postponed reflection, later boundary knowledge

During a design task, the user and assistant encounter evidence that some users leave checkout when delivery charges appear. After the relevant tool operation completes, expertiseOS proposes saving that observation with its approved evidence scope.

The user says, “Save it; reflect later.” Only the observation and authorized reference are stored. Work continues; no boundary principle is silently generated and committed.

In a later active learning session, the user considers when shortening checkout would not address abandonment. They contribute a conditional principle, approve its wording and link to the observation, and the reflection is counted once. A future task offers an optional application question before direct assistance.

### Scenario B — Conflict without silent replacement

A saved procedure recommends a particular retry strategy. A new task exposes an operation with a consequential side effect. expertiseOS proposes an exception with its context and links it to the saved procedure.

The user can retain both, revise the procedure's scope, or decline collection. The agent does not silently generalize one event into a universal ban or treat an unexplained senior correction as proof.

### Scenario C — Fatigue before the learning target

The user reports fatigue while the reflection target remains unmet. Pending unapproved candidates are discarded, collection and exercises pause, and the rest interval is recorded as a control setting. Work continues using approved knowledge. The target remains unmet without a penalty or forced recovery session.

### Scenario D — Cross-host continuity

The user approves a causal hypothesis in Codex, then begins a related task in Claude Code on the same device. Claude Code retrieves the same object, source links, uncertainty, and learner state. It does not treat switching hosts as evidence of mastery or grant approval to a pending proposal from Codex.

## 12. Acceptance and evaluation plan

### 12.1 Deterministic product acceptance

Run this suite against each supported host/version, then against cross-host operation. All P0 consent, privacy, and state-integrity cases must pass; failures cannot be averaged away by good learning scores.

| ID | Test | Pass condition |
|---|---|---|
| AT-01 | Install and start both hosts | Automatic activation, common local repository, and no separate LLM key or manual database setup. |
| AT-02 | Novel and conflicting fixture | At the earliest eligible checkpoint, the proposal states the addition/conflict without asserting that the user lacks the knowledge. |
| AT-03 | Atomic operation in flight | No operation is interrupted or partially canceled for learning; the proposal appears at the next eligible boundary. |
| AT-04 | Save exact proposal | One authorized version is durable; its metadata, source scope, and receipt match the approved proposal. |
| AT-05 | Skip, ignore, cancel, crash | No candidate content in product-controlled persistent stores, caches, logs, temporary jobs, or indexes; pending RAM state expires. |
| AT-06 | Forged or ambiguous approval | Model flags, quoted approvals, stale IDs, and unrelated “yes” messages do not authorize a write. |
| AT-07 | Save without learning | The user can save and continue work without explaining, categorizing, or meeting a target. |
| AT-08 | Derived claim or conflict revision | No new principle, semantic link, or overwrite persists without the specific approved change. |
| AT-09 | User versus agent learning evidence | Saving, model-only answers, and unknown contribution do not advance demonstrated mastery. |
| AT-10 | Target reached versus fatigue | Target suppresses exercises but not enabled collection; fatigue pauses both and leaves unmet target status intact. |
| AT-11 | Pause while work proceeds | No proactive learning after pause; authorized task work and approved-memory retrieval remain available. |
| AT-12 | Concurrent hosts | IDs and state are shared; stale edits conflict safely; approvals cannot cross-authorize; counts are not duplicated. |
| AT-13 | Backend outage or index failure | No false success or task deadlock; approved data is preserved and retries are idempotent. |
| AT-14 | Export, restore, delete | Portable data preserves lineage; deletion removes in-scope content and retrieval traces; unavailable sources are labeled. |
| AT-15 | Adversarial note/tool content | Embedded instructions cannot bypass the service's approval rules or change learning controls. |
| AT-16 | No network for expertiseOS runtime | Local storage/search/state function after setup without external memory or embedding calls; host inference is assessed separately. |

### 12.2 Model-behavior evaluation

Use a small, expert-reviewed fixture set spanning all six knowledge categories, all three subjects, ordinary and boundary cases, explicit corrections, duplicates, and deliberate contradictions. Include non-coding tasks so the host choice does not turn the product into a programming-only tutor.

Score candidate relevance/novelty, handling of uncertain evidence, timing, scaffold usefulness, fidelity to user contribution, appropriateness of recall, and unsupported mastery claims. The product must allow abstention when context or evidence is insufficient.

Pin the behavior specification and tested host-model configuration for reproducibility. Deterministic event delivery is not proof that a model detects every useful insight. Report misses and false proposals rather than promising exhaustive detection.

### 12.3 Product and learning metrics

| Metric | Interpretation |
|---|---|
| Later unassisted application and transfer | Primary evidence of personal development, scoped to the assessed domain. |
| Quality of user-developed higher-level knowledge | Organization, applicability, boundaries, and evidential grounding—not note count alone. |
| Scaffolding needed over time | Whether comparable tasks require less help, controlling for task differences. |
| Task quality with approved memory | Benefit to the assistant, reported separately from human learning. |
| Learning burden | User-reported burden, skips, pauses, and effort estimates; not a direct cognitive-load measurement. |
| Consent and traceability integrity | Unauthorized-write count, exact approval binding, recoverable provenance, and successful deletion. |

Evaluating the junior-versus-senior hypothesis requires common domain tasks, independently reviewed rubrics, comparable assessment conditions, and an unaided senior reference group. To distinguish product effects from ordinary experience and AI assistance, include juniors using the same host without expertiseOS. Evaluate knowledge-structure quality and later unassisted performance separately from AI-assisted work output.

Do not set an arbitrary “matches seniors” percentage in the MVP claim. Pilot evidence should establish task-specific baselines and a meaningful comparison criterion before an efficacy claim is made.

## 13. Delivery gates

| Gate | Required result |
|---|---|
| G0 — Host and license feasibility | Pin candidate versions; validate installation, safe checkpoints, actual user-response capture, local-only retrieval, backend write access, and packaging obligations. |
| G1 — Consent and storage | Exact approval binding; ephemeral candidates; versioned writes; no hidden capture; basic provenance, export, and deletion. |
| G2 — Learning behavior | Six-category scaffolding; user participation; optional reflection; evidence-based mastery; distinct target and fatigue controls. |
| G3 — Cross-host reliability | Both adapters pass the same contract; shared local state; concurrency, failure, pause, and injection tests pass. |
| G4 — Non-technical pilot | Users complete the core loop without developer help; burden is measured; product and learning outcomes are reported separately. |

No further product questionnaire is required before implementation. Failed feasibility checks must be reported as specific implementation constraints; they are not permission to weaken consent, add a separate LLM account, introduce cloud storage, or drop a host silently.

Exact manifests, hook mappings, service endpoints, database migrations, and packaging commands belong in the subsequent technical design and implementation plan. Those documents must trace their behavior to the requirement IDs above.

## 14. Technical references

These primary sources support implementation feasibility and current dependency characteristics. They do not validate expertiseOS's learning hypothesis or imply that the proposed integration has been built. Documentation checked September 14, 2026.

- **R1 — OpenAI, Codex plugins:** https://developers.openai.com/codex/plugins
- **R2 — OpenAI, Codex hooks:** https://developers.openai.com/codex/hooks
- **R3 — Anthropic, Extend Claude Code:** https://code.claude.com/docs/en/features-overview
- **R4 — Anthropic, Hooks reference:** https://code.claude.com/docs/en/hooks
- **R5 — Basic Memory, Technical information:** https://docs.basicmemory.com/reference/technical-information
- **R6 — Basic Memory, Configuration:** https://docs.basicmemory.com/reference/configuration

## 15. Definition of done

The MVP is complete when a non-technical individual can install expertiseOS in both supported local hosts, approve personally useful knowledge during real work, postpone deeper learning, organize and connect what was saved, retrieve it in later work, inspect evidence of their own development, and pause learning without stopping execution—all through one personal local repository, with no unauthorized knowledge persistence and no separate LLM configuration.
