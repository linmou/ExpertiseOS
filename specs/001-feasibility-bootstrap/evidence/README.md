# G0 Evidence Records

**Intent**: Make every external capability claim reproducible and prevent unexecuted checks from appearing as support.

Each evidence record includes:

- evidence ID;
- component and exact version or commit;
- operating system and architecture;
- capability under test;
- exact command or numbered manual steps;
- input fixture and expected output;
- observed output or log path;
- exit status;
- UTC capture time;
- result: `pass`, `limited`, `fail`, or `not_run`;
- limitation and effect on capability reporting.

A capability is supported only when a complete record says `pass`. Limited, failed, and unexecuted checks remain visible and cannot be promoted into support claims.
