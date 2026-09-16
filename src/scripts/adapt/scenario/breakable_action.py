import os

def adapt_debug_scenario_breakable_action(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressBreakableAction"]

    adapted_entry = {
        "Id": scenario_id,
        "Objects": []
    }

    for breakable_object in condition_entry["BreakableObjects"]:
        adapted_object = {
            "Id": breakable_object["ObjectId"],
            "Count": breakable_object["Count"]
        }

        adapted_entry["Objects"].append(adapted_object)

    return adapted_entry