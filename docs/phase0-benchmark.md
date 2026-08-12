# Phase 0 falsification benchmark

Phase 0 tests whether a deterministic scientific-use contract adds measurable value beyond a
strong general Agent with expert instructions. It is a go/no-go experiment, not a launch claim.

## Frozen scope

The first target is `scrna.de_between_conditions/v0`, limited to read-only preflight evidence for a
between-condition comparison within one declared cell population. Phase 0 does not add Seurat,
multi-omics, a web UI, arbitrary script execution, workflow management, or biological-result
judgement.

The first failure families are:

- missing or ambiguous population, condition, donor, or sample metadata;
- donor assigned to more than one condition;
- sample assigned to more than one donor;
- insufficient biological replicates in a declared group;
- absent or non-count-like expression evidence;
- unsupported metadata encodings or safety-limit exhaustion;
- absent execution evidence, which must produce `INDETERMINATE` for postflight claims.

## Corpus and split

Build 40–60 privacy-safe cases from synthetic data and redistributable public-data derivatives.
Each case has a reviewed expected outcome, severity, minimal mutation, rationale, and allowed
ambiguity. Maintain pass, fail, near-miss, ambiguous, decoy, corrupted, and stale cases.

Use separate development and frozen evaluation partitions. Rule authors may inspect the development
partition but must not tune against hidden evaluation labels. Real server datasets remain read-only;
only derived, non-identifying benchmark fixtures and reports may be written under the OmicsRepro
project directory.

## Baselines

Compare the same cases and evidence budget across:

1. Agent with a normal audit prompt;
2. Agent with a reviewed expert audit Skill or equivalent instructions;
3. relevant native validators;
4. OmicsRepro alone;
5. Agent using the OmicsRepro receipt.

Record high-severity recall, precision, silent-error escape rate, run-to-run variance, runtime,
token cost, evidence completeness, abstention quality, and remediation quality. Native validators
are scored only on failure families within their documented scope.

## Internal go/no-go gate

The provisional target for hard or method-contract violations is at least 90% recall and 95%
precision on the frozen set. These are internal product thresholds, not scientific or industry
standards.

Continue past Phase 0 only if OmicsRepro also provides at least one material advantage over Agent +
expert instructions: roughly 15 percentage points higher high-severity recall, at least 50% lower
silent-error escape rate, or a comparably clear advantage in deterministic scale or evidence
completeness. Otherwise stop, narrow, or pivot.

Before promoting a contract from experimental to stable, obtain external confirmation that at least
three real users or groups encountered true issues and changed an analysis or handoff because of
the receipt. Downloads, stars, and raw rule counts are supporting signals, not the primary outcome.

## Promotion boundary

Phase 0 may produce benchmark fixtures, experimental contracts, receipts, and documentation.
It may not market OmicsRepro as certifying scientific correctness. Promotion to stable requires a
reviewed benchmark report, documented false-positive boundaries, known exceptions, versioned test
fixtures, and a maintainer decision recorded in a pull request.
