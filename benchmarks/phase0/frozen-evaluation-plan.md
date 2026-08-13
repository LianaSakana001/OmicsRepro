# Frozen evaluation recruitment and custody plan

Status: protocol only. No frozen cases, labels, identifiers, or private paths are stored in this
repository.

## Target composition

Recruit 24 frozen candidates to complement the 16 visible development cases. The custodian should
target the following minimum coverage before freezing:

| Case class | Target | Purpose |
|---|---:|---|
| valid controls and decoys | 6 | estimate false-positive behavior |
| hard mapping or completeness failures | 6 | test donor/sample/condition invariants |
| matrix evidence failures | 4 | test absent, incompatible, or misleading representations |
| near-miss or ambiguous cases | 4 | test warnings and abstention quality |
| corrupted or unsupported encodings | 2 | test fail-closed evidence handling |
| realistic public-data derivatives | 2 | test transfer beyond hand-written tiny fixtures |

These are recruitment quotas, not labels disclosed to rule authors. Cases should vary population
prevalence, replicate count, cell count, metadata encoding, column naming, ordering, and distractor
evidence. No single mutation should identify the expected answer by filename or case ID.

## Roles

- **Case contributors** provide a minimal case and rationale without exposing private identifiers.
- **Scientific reviewers** approve the task relevance and label; they must not be the case author.
- **Evaluation custodian** stores cases and labels, assigns opaque IDs, freezes hashes, and runs or
  releases evidence to baseline operators.
- **Rule authors** receive only the declared evidence budget and may not inspect labels or custody
  metadata during the round.
- **Baseline operators** run the frozen protocol without changing instructions or model settings.

One person may hold more than one role only when that does not reveal labels to rule authors. At
least one scientific reviewer and the evaluation custodian must be independent of the rule change
being evaluated.

## Eligible evidence

Frozen cases may be fully synthetic or redistributable, non-identifying derivatives of public data.
Access-controlled human data, real donor/sample identifiers, credentials, and machine-specific
paths are ineligible. If a real failure cannot be redistributed, create a synthetic surrogate and
exclude the private source from independently reproducible scoring.

The source dataset root remains read-only. Derivation occurs only in an approved project staging
directory. The final case must be tested for identifier leakage before custody.

## Freeze procedure

1. Complete independent scientific, outcome, severity, and privacy review.
2. Replace descriptive filenames with opaque case IDs unrelated to class or failure family.
3. Generate a manifest containing artifact hashes, contract hash, case-schema version, allowed
   tools, and expected attempt count.
4. Store artifacts, labels, and the manifest outside the development checkout with access limited
   to the custodian.
5. Sign or timestamp the manifest hash before baseline runs begin.
6. Record exact Agent/model/provider versions, inference settings, native tool versions, and
   OmicsRepro commit.
7. Reject any case changed after the freeze; a change requires a new round and manifest.

## Run and unblinding

The custodian supplies each baseline the same opaque case, contract, and evidence budget. Agent
baselines receive five independent attempts; deterministic baselines run once. Operators return
only records conforming to `baselines/output-schema.json`.

Labels remain hidden until all planned attempts are complete, environment metadata is recorded,
and exclusions are locked. Exclusions after unblinding require a public rationale and both original
and sensitivity-analysis scores.

## Publication and stop decision

After unblinding, publish the protocol, frozen manifest, aggregate results, exclusions, uncertainty,
and every redistributable fixture/label. Do not report only favorable failure families or only the
best Agent run. If the predefined Go/No-Go advantage is absent, record STOP, NARROW, or PIVOT in a
reviewed pull request before adding new contract scope.

This document deliberately does not designate the current maintainer or Codex as the independent
reviewer or custodian. Those roles require a real person or group that meets the independence rule.
