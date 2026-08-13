# Independent label review

The development-case author proposes labels; a different person approves or rejects their
scientific rationale, expected rule outcomes, severity, and privacy behavior. Regression tests do
not count as independent label review.

Reviewers should inspect the case YAML, contract documentation, and generated aggregate receipt.
They should not approve a case merely because the current implementation matches its expectation.
For each case, answer:

1. Does the evidence actually represent the stated scientific-use failure or control?
2. Is the proposed L1 decision supported at artifact-inspection assurance?
3. Is the severity proportional to the likely scientific impact?
4. Are the expected rule outcomes specific without asserting unobserved execution?
5. Are identifiers synthetic and absent from the receipt?

To approve a label, change all three review fields to `approved`, set `status: approved`, name the
reviewer, add an ISO `YYYY-MM-DD` date, and record any exception in `notes`. The case's
`label_review` block must then be changed to `status: reviewed` with the same reviewer. The harness
rejects partial approval, self-review, missing cases, and metadata disagreement.

The current sheet is a review packet, not evidence that review has occurred. All entries start as
`pending`.
