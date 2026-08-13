# Verification boundaries

This document defines what OmicsRepro may claim, what evidence it may inspect, and where human or
external-tool responsibility begins. It applies to all experimental scientific-use contracts.

## Product responsibility

OmicsRepro is responsible for deterministic conformance checks against an explicit, versioned
contract. Every finding must identify the rule, outcome, inspected evidence, and remediation or
limitation. The same artifact, contract, and OmicsRepro version must produce the same core receipt.

OmicsRepro is not responsible for choosing the research question, proving biological truth,
declaring a method universally optimal, evaluating biological plausibility, or replacing expert
review. A `PASS` means only that the inspected evidence satisfies the implemented contract at the
reported assurance level.

Researchers and analysis owners remain responsible for the scientific intent, cohort definition,
study design, method choice, interpretation, undisclosed transformations, and final claims. Adapter
authors remain responsible for accurately translating native tool or workflow evidence into
OmicsRepro facts.

## Assurance levels

| Level | Receipt value | Evidence | Permitted claim |
|---|---|---|---|
| L1 | `artifact_inspection` | Read-only files and metadata | Artifact-level preconditions only |
| L2 | `declared_evidence` | Structured evidence supplied by a workflow or user | Declared evidence conforms; execution is not independently observed |
| L3 | `instrumented_execution` | Evidence captured by a reviewed execution adapter | The captured execution satisfies implemented checks |
| L4 | `independent_recomputation` | Independently recomputed facts or results | Recomputed properties agree within the contract's stated tolerance |

Higher levels are not implied by lower-level evidence. A receipt must not say an analysis actually
used a matrix, aggregation, design, contrast, or method unless the reported assurance can support
that claim.

## Outcomes

- `PASS`: sufficient inspected evidence satisfies the implemented rule.
- `WARN`: evidence supports a non-blocking risk or review item.
- `FAIL`: sufficient evidence demonstrates a contract violation.
- `INDETERMINATE`: required evidence is absent, unsafe to inspect, unsupported, or beyond a limit.
- `NOT_APPLICABLE`: the rule does not apply to this declared task.

Receipt precedence is `FAIL`, then `INDETERMINATE`, then `WARN`, then `PASS`. Missing evidence is
never converted to `PASS`.

## Safety boundary

The core verifier:

- opens source artifacts read-only;
- does not execute project scripts or notebooks;
- does not upload artifacts or require network access;
- does not write beside source data;
- bounds metadata and matrix sampling;
- reports aggregate counts rather than donor, sample, or cell identifiers; declared population and
  condition labels may be repeated as scientific intent, but undeclared scanned categories are not;
- writes only to stdout or an explicit output path;
- treats external data roots as immutable.

Any future execution capture or independent recomputation must be a separate, opt-in adapter with
its own threat model, sandbox, resource limits, dependency policy, and review. It must not be loaded
or executed by the default artifact-inspection path.

## Experimental contract boundary

`scrna.de_between_conditions/v0` is an L1 preflight experiment. It may inspect whether a declared
population and contrast have complete donor/sample/condition mappings, whether mappings conflict,
whether each group reaches a declared minimum biological-replicate count, and whether a
count-compatible representation was detected.

It cannot verify actual aggregation, model design, contrast direction, statistical method, result
table, input/output binding, power, or biological interpretation. Those postflight claims remain
`INDETERMINATE` until a separately reviewed evidence adapter exists.
