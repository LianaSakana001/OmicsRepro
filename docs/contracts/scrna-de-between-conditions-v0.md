# `scrna.de_between_conditions/v0`

Status: experimental Phase 0 contract.

This contract asks whether one H5AD artifact contains the minimum inspectable preflight evidence
for a declared between-condition differential-expression task within one cell population. It does
not run differential expression.

## Declaration

```yaml
schema_version: 1
contract: scrna.de_between_conditions/v0
input_id: primary
population:
  value: Microglia
condition:
  column: disease
  case: AD
  control: Control
replicate:
  concept: donor
  min_per_group: 2
max_observations: 2000000
max_categories: 100000
max_entities: 100000
```

The input should use the `scrna-basic` or `scrna-publication` profile so donor, sample, cell type,
and count evidence can be resolved. `population.column` may override the profile's cell-type column.
The replicate floor is a declared minimum for this contract; passing it is not a power calculation
or a claim that the study is adequately powered.

Run the experimental contract:

```bash
omicsrepro verify PROJECT --contract-file de-contract.yml
```

The command writes a deterministic JSON receipt to stdout. Exit code `1` means a demonstrated
contract failure, `2` means invalid configuration or I/O, and `3` means the receipt is
`INDETERMINATE`. A fully artifact-level preflight currently remains `INDETERMINATE` overall because
v0 deliberately abstains from claims about the executed model and results.

## False-positive and exception boundary

The contract does not require pseudobulk as the only acceptable method. Mixed models or other
methods may account for within-donor dependence. Future postflight checks must compare the declared
method with actual execution evidence rather than impose one method universally.

Conflicting donor/condition or sample/donor mappings are blocking only within the selected
population and inspected artifact. Longitudinal, crossover, paired, multi-condition, or deliberately
nested designs may need a future contract with a different mapping model; they should not bypass
this v0 rule by relabeling data.
