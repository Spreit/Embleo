def adapt_debug_scenario_route_fork(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressRouteFork"]

    adapted_entry = {
        "Id": scenario_id,  #  condition_entry["MergeCheckPointId"],
        "Routes": condition_entry["Routes"]
    }

    return adapted_entry
