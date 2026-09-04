##Aircraft Maintenance & Diagnostic Expert System

## Problem
Diagnose aircraft sub-system faults (hydraulics, engine, electrical) from
sensor alerts, using a rule-based expert system rather than a hardcoded
if/else script.

## Knowledge representation used
- **Frames** (`SubsystemFrame`): one per sub-system, holding sensor names,
  normal operating ranges, and the list of faults that subsystem can have.
  This is *declarative* -- adding a new subsystem means adding a frame,
  not rewriting logic.
- **Rules** (`Rule`): predicate-logic-style `IF condition THEN fault`
  statements, each with a confidence weight and a plain-English
  explanation. Stored as data in a list, so the knowledge base is
  separate from the inference engine.

## Inference
- **Forward chaining** (`forward_chain`) is the primary mode: given sensor
  facts, every rule whose condition holds fires, and results are ranked
  by confidence. This matches the real diagnostic task -- you start with
  alerts and want to know what they imply.
- **Backward chaining** (`backward_chain`) is a secondary mode: given a
  specific fault hypothesis, check whether the facts support it. Useful
  for a maintenance crew confirming a suspicion rather than doing a full
  scan.
- **Explanation trace** (`explain`): every diagnosis reports which rule
  fired and why, not just a label -- expert systems are judged on
  explainability as much as correctness.

## Why rules discriminate rather than just threshold-check
Each subsystem has *pairs* of rules that share a triggering symptom but
diverge on a second symptom, e.g. Engine: high EGT + low oil pressure ->
`oil_starvation`, but high EGT + normal oil pressure -> plain `overheat`.
This mirrors real fault isolation logic, where a single reading is
ambiguous and combinations of readings are what actually discriminate
between root causes.

## Files
- `expert_system.py` -- frames, rules, forward/backward chaining engine.
- `run_demo.py` -- three sample sensor-alert scenarios (hydraulics,
  engine, electrical) plus one backward-chaining query.

## How to extend for later units
- Unit III/IV (ML): replace the hand-tuned confidence weights with
  probabilities learned from historical maintenance-log data, or add
  a classifier that pre-screens which subsystem to scope forward
  chaining to.
- Combined final project: this expert system's fault output could feed
  the UAV path planner from Unit-I as a constraint (e.g. "engine fault ->
  replan path to nearest safe landing zone"), chaining diagnosis into
  decision-making the way a real onboard system would.

## Run it
```bash
python run_demo.py
```
