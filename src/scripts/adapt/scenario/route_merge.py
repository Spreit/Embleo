import os

def adapt_debug_scenario_route_merge(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressRouteMerge"]

    adapted_entry = {
        "Id": condition_entry["ForkId"],
        # Hmm... Why is it called CheckPointId and not MergeId?
        "CheckPointId": condition_entry["MergeId"]
    }

    return adapted_entry
