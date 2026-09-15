# Basic Memory License Review

**Intent**: State the distribution boundary for the pinned backend before product packaging depends on it.

- Reviewed component: Basic Memory `0.23.2`
- Installed license file: `basic_memory-0.23.2.dist-info/licenses/LICENSE`
- License: GNU Affero General Public License v3 or later (`AGPL-3.0-or-later`)
- Runtime/startup: separately installed local Python process or public CLI; expertiseOS does not vendor or modify Basic Memory in this slice
- Captured: `2026-09-14T18:57:38Z`

Private local evaluation and development may run the unmodified package under AGPL section 2. Distribution of a combined package, modification, or offering a modified network service can trigger source-code and corresponding-source obligations; process separation alone is not treated as removing those obligations.

Pilot status: approved for private local feasibility and internal showcase use where no copy is conveyed outside the organization and no modified network service is offered. Public or customer distribution is blocked pending a concrete packaging review and legal confirmation of the source-offer, notices, installation information, and network-source obligations for the chosen topology.

Result: `limited`; the technical pilot may proceed, but public release cannot pass on this evidence alone.
