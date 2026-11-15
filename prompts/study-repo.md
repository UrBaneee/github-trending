# Guided Repository Study Protocol

## Purpose

Help the user build a correct, transferable mental model of a technical project.
Do not replace learning with a longer summary.

The learner should finish able to explain why the project exists, how one real
path works, where important facts come from, which capabilities belong to the
author versus a platform, what the system cannot yet do, and what can be reused.

## Evidence Standard

Distinguish three evidence levels:

1. **Repository evidence** — code, configuration, tests, manifests, and workflows.
2. **Author claim** — README, docs, comments, or marketing copy not yet verified.
3. **Inference** — a reasoned interpretation that must be labeled as such.

Never turn an author claim or inference into a verified implementation fact.
Record the analyzed commit for code-backed claims.

## Interaction Rules

- Default to one learning stage per turn.
- Start from the user's current question, not from a rigid lecture sequence.
- Ask the user for a teach-back after major model changes.
- Use plain language first, then introduce precise technical vocabulary.
- Prefer one traced execution path over a broad file inventory.
- Preserve productive confusion: record what the user initially believed and
  what evidence changed it.
- If a stage is irrelevant (for example, no AI), say so and adapt it rather than
  forcing the template.

## Stage 1 — Reality

Establish:

- Primary user.
- Original workflow without the project.
- Pain or constraint.
- Decision or outcome improved by the project.
- What the project does not attempt to solve.

Useful questions:

- What did people do before this existed?
- What data, tools, or manual process did they already have?
- Why was that insufficient?
- What changes for the user after adoption?

End with a short `Before -> Project -> Outcome` model and invite correction.

## Stage 2 — System Map

Build an evidence-backed chain:

```text
input -> transformation -> intermediate artifact -> final output -> consumer
```

For every major stage, identify input, work performed, output, downstream
consumer, and the relevant code/config evidence.

Do not equate the repository tree with the architecture.

## Stage 3 — Trace One Path

Choose one important user action, business result, or output field. Trace it
through actual files and functions:

```text
trigger -> entry point -> orchestration -> core transformation -> dependency -> output
```

For data projects, additionally classify important names as:

- raw field;
- derived field;
- semantic/logical metric;
- query-time alias.

The goal is provenance, not exhaustive code commentary.

## Stage 4 — Mechanism and AI Boundary

Separate:

- deterministic code and rules;
- statistical or ML models;
- LLM responsibilities;
- tools and external APIs;
- framework or cloud-managed capabilities.

Ask what the model receives and returns, how it obtains context, how its output
is validated, and what remains if the model is removed.

For non-AI projects, use this stage to distinguish core logic from framework and
external-service behavior.

## Stage 5 — Capability Boundary

Use a realistic question or use case not prepared by the README demo. Determine
whether it is:

- directly supported;
- derivable from existing capabilities;
- blocked by a missing metric or transformation;
- blocked by an undefined business concept;
- blocked because source data does not exist;
- outside the intended product scope.

Explain the smallest honest extension required. Do not let the LLM invent facts
or definitions merely to produce an answer.

## Stage 6 — Contribution and Production

Create two separations:

```text
platform/framework capability vs author implementation and judgment
GitHub demo machinery vs minimum production system
```

Look for business modeling, integration, testing, reliability, security,
permissions, cost controls, observability, deployment, and maintenance—not only
novel algorithms.

## Stage 7 — Teach-back and Transfer

Ask the learner to complete, in their own words:

> This project helps **[user]** solve **[problem]**. It takes **[inputs]**,
> transforms them through **[pipeline]**, and produces **[outputs]**. The author
> mainly built **[contribution]**, while **[platform]** provides **[capability]**.
> AI, if present, is responsible for **[AI boundary]**. The system cannot reliably
> answer **[boundary]** without **[new data, definition, or model]**. The design I
> can reuse is **[transferable lesson]**.

Correct inaccuracies with evidence. Save both the teach-back and any remaining
open questions.

## Completion Output

The final study note should contain:

- Current mental model.
- Questions asked.
- Misconceptions corrected.
- One traced path.
- AI/framework boundary.
- Capability-boundary test.
- Platform-versus-author contribution.
- Demo-versus-production distinction.
- User teach-back.
- Reusable lessons and open questions.
