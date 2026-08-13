# Phase 0 baseline protocol

All comparators receive the same case artifact, declared contract, evidence budget, and output
schema. They may not access labels, other baseline outputs, the network, or hidden evaluation
metadata. Runtime, token usage, tool calls, errors, and abstentions are recorded per attempt.

The five approved comparators are:

1. `agent`: a general Agent with the neutral task prompt;
2. `agent_expert_instructions`: the same Agent plus reviewed domain audit instructions;
3. `native_validators`: only validators whose documented scope applies to the case;
4. `omicsrepro`: the deterministic receipt without Agent interpretation;
5. `agent_omicsrepro`: the general Agent receives the OmicsRepro receipt in addition to the common
   evidence budget.

Stochastic Agent baselines run five independent attempts per case. Deterministic tools run once.
Model/provider/version, inference settings, tool versions, hardware class, and timestamps must be
recorded at execution time; they are not silently changed during one frozen round.

`protocol.yml` is machine-checked by the development harness. Instruction files are versioned here
so the comparison is reproducible. The expert baseline is intentionally strong: it is not a
strawman and may inspect the same permitted artifacts with tools.

The initial development corpus is for dry runs only. Do not report comparative product results
until labels are independently reviewed and the evaluation custodian starts a frozen round.
