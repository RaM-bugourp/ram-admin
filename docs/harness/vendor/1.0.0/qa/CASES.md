# Independent acceptance cases

Synthetic fixtures prove tool behavior only, not authentic product execution. The runner will use a temporary directory and write a bounded machine-readable result to qa/results.json; fixture evidence is never promoted into product proof.

## Structural rejection

- unknown manifest fields; duplicate JSON keys; duplicate owner/rule/route/executor/record IDs; wrong types and state aliases; dangling owner/rule/executor/check refs; orphan rules; missing context/source files; path traversal, absolute/drive/UNC/backslash and symlink escape.
- Cross-check valid and invalid instances through shipped schema evaluator and CLI; explicitly distinguish schema shape rejection from semantic reference rejection.

## Positive and negative semantic pairs

- Hybrid task must preserve route union, stable deduplication, all applicable hard rules and deterministic output. Reorder arrays only where order is semantically irrelevant.
- Conditional fact true adds context, false does not; absent/null produces UNKNOWN and blocks.
- Exact approved directory boundary: src/a does not authorize src/ab; ** matches zero and multiple segments; scope dimensions are AND, entries in each dimension OR.
- Unmatched task produces diagnostic blocked/invalid rather than empty pass. Conflicting applicable constraint keys stop affected actions, compatible values do not.
- Route-only evidence requirements cannot disappear silently; rule checks/executors missing from route must reject.
- Valid concrete current record can be locally consistent. Stale/foreign target/changed dirty digest/changed environment/changed rule or executor/altered artifact must no longer count pass.
- Five canonical result states retain aggregation precedence; all N/A and zero-check cases carry an explicit scope reason. Applicable rule N/A fails; genuinely excluded rule has a reachable justified path (or documented conservative limitation).
- proposed/advisory status never claims enforcement; fabricated nonsimulated/performed flags remain untrusted assertions. No CLI can prove real execution by accepting those fields.
- Place a shell payload in evidence.execution.command; read-only validation must neither execute nor create its sentinel. Command strings are data even when status is pass and exit_code is zero.

## Integration checks

Run documented Quickstart and all shipped tests with real exit codes; inspect all Markdown internal targets/anchors/reference links (excluding fenced code and disclosed dynamic placeholders); validate shipped JSON examples and compare format contract to implementation. No network/product/CI mutation. Final README must expose new adoption, legacy integration, and platform extension without requiring history.
