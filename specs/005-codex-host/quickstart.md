# Quickstart: Verify the Codex Host Adapter

## Prerequisites

1. Check out the promoted integration SHA containing green C001-C004 contracts.
2. Obtain the immutable G0 Codex evidence packet and verify every claimed capability against `contracts/g0-evidence.md`.
3. Use the exact Python, Codex, OS, installation surface, and permission mode recorded by G0.
4. Start the shared local expertiseOS service with its normal component test configuration.

## Component Verification

Run the repository's targeted pytest commands for:

- normalized event and capability contract;
- actual-user decision binding and adversarial negative inputs;
- atomic checkpoint ordering and unknown/unbalanced state;
- session expiry and volatile cleanup;
- service/search/write failure isolation;
- scope exclusion and disabled-state forwarding prevention.

Then run repository lint, static checks, and mypy for the modified adapter/onboarding files.

## Pinned Live-Host Verification

Using the G0-supported harness or reproducible procedure, record complete inputs, outputs, environment metadata, commands, exit results, timestamps, and artifact hashes for:

1. consented onboarding and fresh-session automatic activation;
2. bounded controls/service availability at startup;
3. no proposal during a bounded atomic operation;
4. Save exactly once from actual user input;
5. Edit then re-display then Save;
6. Skip and unrelated-message expiry;
7. model/tool/quoted/cross-session attempts creating no decision;
8. session-end cleanup;
9. ordinary Codex work during service outage;
10. shared approved retrieval and accurate degradation reporting.

## Pass Condition

All component/static checks pass, each live claim has matching evidence, unauthorized-decision fixtures produce zero grants/writes, and outage fixtures preserve ordinary Codex task completion without a false save. Any unproven capability remains false and is reported to integration as a compatibility limitation.
