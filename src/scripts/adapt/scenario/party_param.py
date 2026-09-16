import os

def adapt_debug_scenario_party_param(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressPartyParam"]

    adapted_entry = {
        "ProgressPartyParamId": scenario_id,
        "Flags": [],
        "Params": condition_entry["Params"]
    }

    for flag in condition_entry["Flags"]:
        progress_flag = {
            "FlagType": flag["FlagType"],
            "Value": bool(flag["Value"])
        }

        adapted_entry["Flags"].append(progress_flag)

    return adapted_entry