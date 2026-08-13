# Phase 0 falsification benchmark

Phase 0 tests whether a deterministic scientific-use contract adds measurable value beyond a
strong general Agent with expert instructions. It is a go/no-go experiment, not a launch claim.

## Current status

The benchmark is being assembled, not yet reported. The public development partition contains
small synthetic adversarial cases under `benchmarks/phase0/development`. These cases test the
benchmark machinery and known boundaries; scores on them are regression results, not evidence that
the product thesis passed.

The target corpus remains 40–60 reviewed cases. No Phase 0 product claim is permitted until the
protocol, frozen evaluation partition, baseline prompts/instructions, repeated runs, and aggregate
report are complete.

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

During an active round, frozen evaluation definitions and labels are held outside the development
repository with access limited to the evaluation custodian. Rule authors receive only a case ID,
evidence budget, and run interface. After the decision is recorded, maintainers publish the
evaluation protocol, aggregate result, and all fixtures/labels that licensing and privacy permit.
Any non-publishable case must have a publishable synthetic surrogate and a documented exclusion
from independently reproducible scoring.

## Case record

Every case must include:

- a stable ID, partition, class, failure family, and severity;
- a scientific rationale and one minimal mutation from a valid control where possible;
- synthetic or redistributable provenance and an explicit privacy classification;
- expected L1 decision and rule-level outcomes reviewed by a second person;
- known ambiguity, allowed outcomes, and exclusion rationale when a single label is inappropriate.

The development harness derives tiny H5AD fixtures at runtime; binary omics files are not committed.
It also checks that donor and sample identifiers do not enter receipts. Run it with:

```bash
PYTHONPATH=src python benchmarks/phase0/run_development.py
```

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

For the L1 development corpus, `ORV190` is excluded from the artifact-decision score because it is
the expected abstention for unobserved execution. The harness assigns an L1 decision as follows:

1. any artifact-level `FAIL` means fail;
2. otherwise any artifact-level `INDETERMINATE` means indeterminate;
3. otherwise warnings are non-blocking and the L1 decision is pass.

This benchmark-only projection does not change the public receipt verdict or weaken fail-closed
precedence.

The five comparators use a versioned common evidence budget, instruction files, repetition counts,
and output schema under `benchmarks/phase0/baselines`. Development labels have a separate review
packet under `benchmarks/phase0/review`; matching a proposed label in a regression test is not an
independent approval. Recruitment and custody for opaque evaluation cases follow
`benchmarks/phase0/frozen-evaluation-plan.md`.

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
