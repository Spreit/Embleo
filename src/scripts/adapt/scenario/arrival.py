import os

def adapt_debug_scenario_arrival(debug_condition, scenario_id):
    condition_progress = debug_condition["ProgressArrival"]

    adapted_entry = {
        "ProgressArrivalId": scenario_id,
        "LayoutPointId": condition_progress["PointId"],
        "Event": {}
    }

    adapted_entry["Event"] = {
        "Flag": condition_progress["Flag"],
        "ScriptPath": condition_progress["ScriptPath"],
        # "TriggerType": 1,  # Where do I get this?
        # "ActionType": 2,  # Where do I get this?
        # "Param": "",
        "Drop": {
            "Id": condition_progress["EventDropInfo"]["ID"]
        }
    }

    return adapted_entry