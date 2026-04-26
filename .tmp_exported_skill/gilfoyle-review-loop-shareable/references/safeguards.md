# Safeguards

Treat a "clean" result with suspicion until it clears these checks.

## Suspected Subagent Failure

If a discovery or review subagent returns very short output, no numbered findings, no file references, or obviously incomplete coverage, treat that as failure rather than cleanliness.

Re-dispatch if:

- the report is empty or nearly empty
- a thorough review covers only a handful of files in a large target
- the report names no `FIND-NN` entries despite real issues nearby
- the report ignores the requested focus axis

## Floor Checks Before Accepting Zero Critical/High

- coverage proof: list the packages or files actually swept
- category proof: show that typing, ownership, control flow, and dependency boundaries were all checked
- density floor: for non-trivial targets, explain why zero or near-zero findings is believable
- diff probe: sample recent change hotspots even during a thorough clean pass
- rotation discipline: ensure the last clean pass did not use the same focus axis
