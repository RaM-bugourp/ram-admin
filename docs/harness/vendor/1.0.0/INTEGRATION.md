# Technical integration handoff

As of 2026-11-14. The normative machine contract is [FORMAT](spec/FORMAT.md); start human adoption at [START-HERE](docs/START-HERE.md). This package is a generic offline validator, not a deployed product policy.

## Runtime and commands

Python 3.10+ standard library, no installation, network, or third-party dependencies required. From the package root:

```console
python -m unittest discover -s tests -v
python tools/harness.py --help
python tools/harness.py lint --root examples/demo --manifest harness.json
python tools/harness.py resolve --root examples/demo --manifest harness.json --task tasks/hybrid.json
python tools/harness.py evidence --root examples/demo --manifest harness.json --task tasks/hybrid.json --records evidence/records.json --now 2026-11-14T10:00:00Z
```

Expected exits: tests/help/lint/resolve = 0; sample evidence = 2 with aggregate `not-run`, deliberately not a product pass. Profiles `plugin`, `web`, `app`, `hybrid` are files under `examples/demo/tasks/`; all use one shared manifest. Hybrid unions three routes and five pages. The sample target is explicitly simulated; all three sample result states are not-run and enforcement remains proposed.

CLI emits JSON except argparse help/errors. Exit 1 invalid input/schema/ref; 2 fail/blocked/not-run (also argparse usage); 3 I/O errors. `lint` proves only declared shape/reference validity. No CLI mode executes commands, mutates inputs, reads credentials, inspects Git, or modifies remote protections. `tools/build_assets.py` is a separate **writing maintainer generator** for schemas and synthetic fixtures, not a validation command.

## Stable adapter boundaries

- Strict JSON schemas: `schemas/manifest.schema.json`, `task.schema.json`, `evidence.schema.json`, `route.schema.json`, `rule.schema.json`. See FORMAT for the exact supported keyword subset and additional semantic checks.
- Resolve consumes root-relative task/manifest paths and outputs sorted multi-route context union, applicable rules, explicit conflicts/stopped actions, and `routing_digest`. Unknown/null conditional facts, uncovered dimensions and out-of-approved paths block rather than N/A. Approval is an input declaration, never granted by this tool.
- Evidence consumes the same manifest/task plus records. Every record carries resolve's exact `routing_digest` and nine invalidation triggers including `routing`. The fingerprint includes complete task+manifest and content hashes of all declared context/source pages. Context, facts, diff expansion or declarations changing require rerouting and new evidence.
- Records bind source/dirty/environment/target/artifacts/rule/executor/scope/change/time. Files and SHA-256 are checked. Historical status is retained; stale current status becomes not-run. A missing historical artifact is an invalid input (exit 1), not silently accepted history.
- N/A requires a concrete rule-excluding scope dimension and current excluded values. Capability/environment absence is blocked, not N/A. Applicable required records cannot use N/A.
- State and enforcement are independent. Aggregate precedence fail > blocked > not-run > pass; no required checks yields not-applicable with scope basis.
- Positive unit fixtures model internally consistent nonsimulated declarations solely to test envelope acceptance. The checker cannot authenticate those declarations and they are **not** real product execution evidence.

## Maintainer verification and limitations

The implementation test suite includes union routing, rule scope/closure/conflicts, unknown facts, path authorization/globs/traversal, artifact integrity, evidence freshness, digest changes, wrong target/source/environment, all states, N/A proofs, fake pass rejection, CLI exits/read-only behavior and no manifest shell execution. It tests complete schema-tree traversal, including optional absent properties, empty items and additional-property schemas.

Native symlink escape test may skip on Windows if symlink privilege is unavailable (WinError 1314); the skip is disclosed, not converted to a pass. A separate mock verifies the resolved-path escape guard without claiming native symlink coverage. Test counts and actual command outputs are recorded in the owner's final handoff; rerun the suite rather than treating a historical count as current.

This is a bounded v1 consistency checker, not a general JSON Schema implementation, test runner, signature/identity verifier, authorization engine, prose conflict solver, CI installer, remote required-check verifier, or real-product acceptance system. `performed`, target authenticity, approved scope, source revision, environment declarations, provenance and enforcement must be independently collected/attested by an authorized adapter and validated on the actual target. Only explicit shared constraint-key contradictions are detected. Artifact/file reading does not provide race-free filesystem snapshots.

The package directory may be an unversioned checkout: local `git status` reported not-a-git-repository during implementation, so no clean working-tree or diff claim is made. Existing product architecture/plans were not migrated by these tools.
