# Single-cell delivery profiles

Profiles convert common delivery expectations into deterministic checks while allowing different
projects and consortia to use different column names. Profile definitions are versioned separately
from the manifest. Run `omicsrepro profiles` to inspect the installed definition.

## `scrna-basic`

Designed for internal handoff and routine reuse. It requires:

- a donor semantic field in `obs`;
- a sample semantic field in `obs`;
- a cell-type semantic field in `obs`;
- a shape-compatible, count-like matrix in `raw` or a conventional layer such as `counts` or
  `UMIs`.

## `scrna-publication`

Designed as a publication/public-deposition preflight. It includes `scrna-basic` expectations and
also requires:

- a batch semantic field in `obs`;
- stable gene identifiers in `var`;
- an observation-compatible UMAP, t-SNE, or PCA representation in `obsm`.

Passing the profile does not prove that biological annotations are correct or that a paper's
figures can be regenerated. It proves that the declared H5AD contains the minimum structural and
semantic material specified by the profile.

## Semantic aliases

OmicsRepro matches built-in names exactly before applying case/punctuation-insensitive matching.
For example, `donor_id`, `Donor ID`, and `donor-id` can represent the donor concept. Projects can
append aliases but cannot silently replace the built-ins:

```yaml
profile: scrna-publication
checks:
  semantic_aliases:
    donor: [participant_code]
    sample: [biospecimen]
    cell_type: [final_annotation]
    batch: [chemistry_batch]
    gene_id: [ensembl_gene]
```

## Severity

- Missing required semantic concepts, raw counts, or embeddings are `FAIL` because the declared
  profile contract is not satisfied.
- Missing values, a single observed category, a scan limit, or excessive cardinality are `WARN`.
- Use `--fail-on-warning` when a delivery gate must reject warnings.

## Privacy and bounded inspection

Metadata quality evidence contains only the selected column name, number of rows, missing count,
missing fraction, and category count. Category values, donor identifiers, and sample identifiers
are never included in the report.

Categorical columns are scanned in bounded chunks. Non-categorical columns are scanned only when
their row count is within `max_column_values`; otherwise OmicsRepro emits a warning. Sparse raw
counts are sampled from stored nonzero values without densification. Count evidence is structural
and numeric, not a proof of biological provenance.
