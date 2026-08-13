# Expert single-cell audit baseline instructions

Audit the supplied artifact and declared within-population condition comparison as a skeptical
single-cell methods reviewer. Inspect only the read-only evidence provided; do not use the network
or execute project analysis scripts.

Check at minimum:

- that the declared population and both contrast groups exist;
- completeness of population, condition, sample, and donor metadata in selected observations;
- whether one sample maps to multiple donors or one donor maps to multiple conditions;
- biological replicate counts per group, counting donors rather than cells;
- whether an available matrix has shape and bounded value evidence compatible with raw counts;
- whether other conditions or ambiguous encodings require an explicit subset or abstention;
- whether resource or evidence limits prevent a supported decision.

Do not claim that aggregation, model design, contrast direction, method execution, result binding,
power, or biological interpretation was verified without execution evidence. Missing or unsafe
evidence is `indeterminate`, not `pass`. Return the required structured output with decision,
detected failure families, evidence, remediation, and abstention reason.
