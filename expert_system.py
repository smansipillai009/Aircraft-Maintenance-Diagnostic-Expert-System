"""
Aircraft Maintenance & Diagnostic Expert System
================================================

Unit-II project (Knowledge Representation & Logic).

A rule-based expert system that diagnoses aircraft sub-system faults
(hydraulics, engine, electrical) from sensor alerts, using:

    - Frames        : structured knowledge about each sub-system
                       (sensor slots, normal operating ranges)
    - Predicate-logic-style rules : IF (conditions on sensor facts)
                       THEN (fault conclusion, confidence)
    - Forward chaining : start from known facts (sensor readings),
                       fire every rule whose conditions are satisfied,
                       and keep the diagnoses ranked by confidence.

Why forward chaining (not backward):
    Diagnosis here is DATA-DRIVEN -- we start with a set of sensor
    alerts and want to find out what they imply. That is exactly the
    forward-chaining pattern: known facts -> fire matching rules ->
    derive new facts (candidate faults). Backward chaining would fit
    a different question: "confirm/deny that this SPECIFIC fault is
    present" -- included here as a secondary mode for completeness.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List


# --------------------------------------------------------------------------
# Frames: structured knowledge about each sub-system
# --------------------------------------------------------------------------
@dataclass
class SubsystemFrame:
    """A 'frame' holding what we know about one aircraft sub-system."""
    name: str
    sensors: Dict[str, tuple]     # sensor_name -> (min_normal, max_normal, unit)
    known_faults: List[str] = field(default_factory=list)


HYDRAULICS = SubsystemFrame(
    name="Hydraulics",
    sensors={
        "pressure_psi": (2800, 3200, "psi"),
        "fluid_level_pct": (70, 100, "%"),
        "fluid_temp_c": (10, 90, "C"),
    },
    known_faults=["fluid_leak", "pump_failure", "overheat_fluid"],
)

ENGINE = SubsystemFrame(
    name="Engine",
    sensors={
        "egt_c": (300, 850, "C"),          # exhaust gas temperature
        "oil_pressure_psi": (40, 90, "psi"),
        "vibration_mm_s": (0, 5, "mm/s"),
        "rpm": (55, 102, "% N1"),
    },
    known_faults=["overheat", "oil_starvation", "compressor_stall", "bearing_wear"],
)

ELECTRICAL = SubsystemFrame(
    name="Electrical",
    sensors={
        "bus_voltage_v": (24, 30, "V"),
        "battery_temp_c": (0, 55, "C"),
        "current_draw_a": (0, 120, "A"),
    },
    known_faults=["generator_failure", "battery_overheat", "short_circuit"],
)

SUBSYSTEMS = {f.name: f for f in [HYDRAULICS, ENGINE, ELECTRICAL]}


# --------------------------------------------------------------------------
# Rules: predicate-logic-style "IF conditions THEN fault, confidence"
# --------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    subsystem: str
    # condition: function(facts: dict) -> bool. facts hold sensor readings
    # plus any derived facts (e.g. "pressure_low": True) added during chaining.
    condition: Callable[[dict], bool]
    conclusion: str          # fault name asserted if condition holds
    confidence: float        # 0-1, how strongly this rule implies the fault
    explanation: str         # human-readable reason, for the trace


def below(facts, sensor, frame):
    return sensor in facts and facts[sensor] < frame.sensors[sensor][0]


def above(facts, sensor, frame):
    return sensor in facts and facts[sensor] > frame.sensors[sensor][1]


RULES: List[Rule] = [
    # --- Hydraulics ---
    Rule(
        name="R-HYD-1",
        subsystem="Hydraulics",
        condition=lambda f: below(f, "pressure_psi", HYDRAULICS) and below(f, "fluid_level_pct", HYDRAULICS),
        conclusion="fluid_leak",
        confidence=0.9,
        explanation="Low pressure AND low fluid level together strongly indicate a leak, "
                    "not just a sensor/pump issue.",
    ),
    Rule(
        name="R-HYD-2",
        subsystem="Hydraulics",
        condition=lambda f: below(f, "pressure_psi", HYDRAULICS) and not below(f, "fluid_level_pct", HYDRAULICS),
        conclusion="pump_failure",
        confidence=0.7,
        explanation="Pressure is low but fluid level is normal -- fluid is present, "
                    "so the pump is the likelier suspect.",
    ),
    Rule(
        name="R-HYD-3",
        subsystem="Hydraulics",
        condition=lambda f: above(f, "fluid_temp_c", HYDRAULICS),
        conclusion="overheat_fluid",
        confidence=0.6,
        explanation="Fluid temperature above normal operating range.",
    ),

    # --- Engine ---
    Rule(
        name="R-ENG-1",
        subsystem="Engine",
        condition=lambda f: above(f, "egt_c", ENGINE) and below(f, "oil_pressure_psi", ENGINE),
        conclusion="oil_starvation",
        confidence=0.85,
        explanation="High EGT combined with low oil pressure points to inadequate "
                    "lubrication/cooling rather than a pure thermal fault.",
    ),
    Rule(
        name="R-ENG-2",
        subsystem="Engine",
        condition=lambda f: above(f, "egt_c", ENGINE) and not below(f, "oil_pressure_psi", ENGINE),
        conclusion="overheat",
        confidence=0.65,
        explanation="EGT above range with normal oil pressure -- general overheat condition.",
    ),
    Rule(
        name="R-ENG-3",
        subsystem="Engine",
        condition=lambda f: above(f, "vibration_mm_s", ENGINE) and below(f, "rpm", ENGINE),
        conclusion="compressor_stall",
        confidence=0.75,
        explanation="High vibration with an RPM drop is the classic compressor-stall signature.",
    ),
    Rule(
        name="R-ENG-4",
        subsystem="Engine",
        condition=lambda f: above(f, "vibration_mm_s", ENGINE) and not below(f, "rpm", ENGINE),
        conclusion="bearing_wear",
        confidence=0.55,
        explanation="Elevated vibration with steady RPM suggests mechanical wear rather than a stall.",
    ),

    # --- Electrical ---
    Rule(
        name="R-ELEC-1",
        subsystem="Electrical",
        condition=lambda f: below(f, "bus_voltage_v", ELECTRICAL) and above(f, "current_draw_a", ELECTRICAL),
        conclusion="short_circuit",
        confidence=0.8,
        explanation="Voltage sag with abnormally high current draw is a hallmark of a short circuit.",
    ),
    Rule(
        name="R-ELEC-2",
        subsystem="Electrical",
        condition=lambda f: below(f, "bus_voltage_v", ELECTRICAL) and not above(f, "current_draw_a", ELECTRICAL),
        conclusion="generator_failure",
        confidence=0.7,
        explanation="Voltage sag without excess current draw points to a generation problem, not a load fault.",
    ),
    Rule(
        name="R-ELEC-3",
        subsystem="Electrical",
        condition=lambda f: above(f, "battery_temp_c", ELECTRICAL),
        conclusion="battery_overheat",
        confidence=0.75,
        explanation="Battery temperature above normal operating range.",
    ),
]


# --------------------------------------------------------------------------
# Forward-chaining inference engine
# --------------------------------------------------------------------------
@dataclass
class Diagnosis:
    fault: str
    confidence: float
    rule_name: str
    explanation: str


def forward_chain(facts: dict, subsystem_name: str = None) -> List[Diagnosis]:
    """
    Fire every rule whose condition is satisfied by `facts`.
    If subsystem_name is given, only that subsystem's rules are checked
    (mirrors how a real system would scope diagnosis to the alerting
    sub-system rather than scanning everything).

    Returns diagnoses sorted by confidence, descending -- ties broken by
    rule order (more specific rules are listed first in RULES).
    """
    applicable = [r for r in RULES if subsystem_name is None or r.subsystem == subsystem_name]
    diagnoses = []
    for rule in applicable:
        if rule.condition(facts):
            diagnoses.append(Diagnosis(rule.conclusion, rule.confidence, rule.name, rule.explanation))
    diagnoses.sort(key=lambda d: d.confidence, reverse=True)
    return diagnoses


def backward_chain(facts: dict, hypothesis: str) -> Diagnosis:
    """
    Backward-chaining mode: "is `hypothesis` supported by the facts?"
    Checks only rules that conclude the hypothesis and returns the
    best-supporting one, or None if no rule for it fires.
    """
    candidates = [r for r in RULES if r.conclusion == hypothesis and r.condition(facts)]
    if not candidates:
        return None
    best = max(candidates, key=lambda r: r.confidence)
    return Diagnosis(best.conclusion, best.confidence, best.name, best.explanation)


def explain(diagnoses: List[Diagnosis]) -> str:
    if not diagnoses:
        return "No rule matched the given sensor readings -- no fault diagnosed."
    lines = []
    for d in diagnoses:
        lines.append(f"[{d.rule_name}] {d.fault}  (confidence {d.confidence:.2f})\n    reason: {d.explanation}")
    return "\n".join(lines)
