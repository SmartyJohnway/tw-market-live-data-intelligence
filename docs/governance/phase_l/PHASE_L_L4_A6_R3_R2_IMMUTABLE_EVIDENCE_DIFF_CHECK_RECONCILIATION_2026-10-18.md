# L4-A6-R3-R2 — Immutable Evidence Diff-Check Reconciliation

Run: `l4-a6-r3-r2-20261018T005100Z`

L4-A6 already achieved technical PASS. This evidence-only repair does not
convert a failed runtime or test gate to PASS. It reconciles a validator-reporting
ambiguity caused solely by seven hash-bound historical JSON artifacts, each
containing exactly one CRCRLF sequence at EOF. The seven files are listed and
hash-bound in the R3-R2 acceptance run. Their bytes were preserved because
normalizing them would change the historical hash chain.

The full candidate-range `git diff --check` returns exit code 2 with exactly
seven warnings, one for each of those files. No other candidate file is reported.
The semantic current diff check excludes exactly those seven immutable paths and
returns exit code 0. This is a narrowly scoped exception for existing EOF line
formatting only; it is not a general whitespace waiver. New files remain subject
to the ordinary clean diff check.

R3-R1 reported `git_diff_check = PASS` based on its closure working-state check.
Independent candidate-range review later identified the seven immutable evidence
EOF format warnings. R3-R2 supersedes only the interpretation of that validator
field. No R3-R1 technical/resource finding changes.

The R3/R3-R1 integrated gate and all accepted resource findings remain unchanged.
The two TG4 Mode C historical nodes remain governed deselections (not passing,
not repaired); Mode C historical debt is unresolved. L4-A6 remains
`L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS`, pending Owner acceptance.
L4-A7 remains unauthorized.
