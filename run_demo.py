"""
Demo / driver for the Aircraft Maintenance & Diagnostic Expert System.

Runs three sample sensor-alert scenarios through forward chaining
(the main diagnostic mode), then shows one backward-chaining query
("is it specifically a fluid leak?").

Run:
    python run_demo.py
"""

from expert_system import forward_chain, backward_chain, explain

SCENARIOS = [
    {
        "label": "Scenario A -- Hydraulics alert",
        "subsystem": "Hydraulics",
        "facts": {
            "pressure_psi": 2400,   # below 2800 -> low
            "fluid_level_pct": 55,  # below 70 -> low
            "fluid_temp_c": 60,
        },
    },
    {
        "label": "Scenario B -- Engine alert",
        "subsystem": "Engine",
        "facts": {
            "egt_c": 910,            # above 850 -> high
            "oil_pressure_psi": 65,  # normal
            "vibration_mm_s": 2,
            "rpm": 90,
        },
    },
    {
        "label": "Scenario C -- Electrical alert",
        "subsystem": "Electrical",
        "facts": {
            "bus_voltage_v": 21,     # below 24 -> low
            "battery_temp_c": 40,
            "current_draw_a": 180,   # above 120 -> high
        },
    },
]


def main():
    for scenario in SCENARIOS:
        print("=" * 70)
        print(scenario["label"])
        print("Sensor facts:", scenario["facts"])
        print("-" * 70)
        diagnoses = forward_chain(scenario["facts"], subsystem_name=scenario["subsystem"])
        print(explain(diagnoses))
        print()

    # Backward-chaining example: confirm a specific hypothesis
    print("=" * 70)
    print("Backward-chaining query: 'Is Scenario A a fluid_leak?'")
    result = backward_chain(SCENARIOS[0]["facts"], "fluid_leak")
    if result:
        print(f"CONFIRMED via [{result.rule_name}] confidence={result.confidence:.2f}")
        print(f"  reason: {result.explanation}")
    else:
        print("Not supported by current facts.")


if __name__ == "__main__":
    main()
