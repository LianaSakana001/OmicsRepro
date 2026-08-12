# OmicsRepro product charter

Status: Phase 0 product thesis, provisional and falsifiable.

This charter turns the product proposal into a maintained decision document. It states what
OmicsRepro is trying to prove, who it is for, what it will not build yet, and when maintainers must
stop or pivot. It is not a promise that the experimental thesis has already been validated.

## Product thesis

Executing an omics analysis is becoming easier for both researchers and Agents, while verifying
that the execution matched the intended scientific design remains difficult. OmicsRepro tests the
following thesis:

> An independent, deterministic verifier operating on explicit scientific-use contracts and
> inspectable evidence can reduce silent scientific error escape beyond a strong Agent supplied
> with expert instructions.

The intended product is a verification layer, not an analysis generator. A generator—human,
script, workflow, or Agent—produces an analysis and artifacts. OmicsRepro evaluates only the claims
supported by available evidence and produces a versioned receipt.

## Initial users and jobs

Phase 0 focuses on four prospective user groups:

- bioinformaticians handing analyses or processed objects to collaborators;
- single-cell core facilities reviewing deliveries before release;
- research groups reviewing condition-comparison analyses;
- Agent and workflow authors that need deterministic, CI-compatible guardrails.

Their initial job is narrow: detect high-impact, silent design or evidence failures before a
single-cell between-condition result is trusted or handed off. Stars, downloads, and number of
implemented rules are secondary signals; confirmed changes to a real analysis or delivery are the
primary signal.

## Product boundary

OmicsRepro owns:

- explicit, versioned contracts with documented evidence and limitations;
- deterministic checks and fail-closed outcomes;
- privacy-preserving receipts that identify rules and aggregate evidence;
- reproducible benchmark fixtures and comparison protocols.

OmicsRepro does not own:

- generating analyses, selecting research questions, or interpreting biological truth;
- declaring a method universally optimal;
- replacing statistical, biological, ethical, or publication review;
- arbitrary workflow execution, data management, conversion, or provenance platforms;
- a general marketplace for Agent skills.

A `PASS` applies only to implemented checks at the receipt's assurance level. Missing or unsafe
evidence is `INDETERMINATE`, never an inferred pass. The complete responsibility and threat boundary
is in [verification-boundaries.md](verification-boundaries.md).

## Phase 0 wedge

The only approved experimental contract is `scrna.de_between_conditions/v0`. It inspects
artifact-level preconditions for one declared cell population and condition contrast:

- population and design metadata availability and completeness;
- cell-to-sample-to-donor-to-condition consistency;
- a declared biological-replicate floor;
- bounded evidence for a count-compatible matrix.

It does not verify actual aggregation, model observations, design formula, contrast direction,
method execution, result binding, statistical power, or biological interpretation. Those claims
remain `INDETERMINATE` at artifact-inspection assurance.

## Assumptions under test

Phase 0 must test, rather than assume, that:

1. the selected silent failures occur in realistic projects and matter to users;
2. required evidence can be represented without uploading data or exposing identifiers;
3. deterministic contracts improve detection over Agent + expert instructions;
4. false positives and abstentions remain understandable and actionable;
5. at least three external users or groups confirm a real issue and change an analysis or handoff.

## Go, narrow, or stop

The benchmark protocol in [phase0-benchmark.md](phase0-benchmark.md) is the source of truth. The
provisional internal gate for hard and method-contract violations is at least 90% recall and 95%
precision on a frozen evaluation partition.

Continue only if OmicsRepro also demonstrates a material advantage over Agent + expert
instructions: approximately 15 percentage points higher high-severity recall, at least 50% lower
silent-error escape, or a comparable deterministic-scale or evidence-completeness advantage.

If it does not, maintainers must stop, narrow the contract, or pivot. Existing code, effort, stars,
or an application deadline are not reasons to override this gate.

## Expansion rule

Phase 0 may add benchmark fixtures, contract documentation, deterministic receipts, and the minimum
inspection logic needed to test the thesis. Seurat, transfer verification, additional omics,
execution adapters, a web UI, and workflow integrations remain candidates—not scheduled promises.

A candidate expansion requires:

1. documented real failure cases from the target users;
2. evidence that existing native validators do not already solve the problem;
3. a narrow contract and threat model;
4. a development corpus and a frozen evaluation plan;
5. an explicit maintainer decision in a reviewed pull request.

## Decision record

- v0.2 remains the stable artifact-delivery preflight and is not silently redefined.
- Experimental scientific verification uses a separate command and receipt schema.
- The original broad product proposal is accepted as a direction, not as an implementation plan.
- Phase 0 precedes Seurat, multi-omics, execution capture, Agent integration, and UI development.
- Every benchmark round must publish its protocol and, after the decision, enough fixtures and
  results to permit independent scrutiny.
