import os

def adapt_debug_scenario_demo(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressDemo"]

    adapted_entry = {
        "ProgressDemoId": scenario_id,
        "ResourcePath": condition_entry["ResourcePath"]
    }

    return adapted_entry