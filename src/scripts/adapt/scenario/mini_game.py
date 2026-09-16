import os

def adapt_debug_scenario_minigame(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressMiniGame"]

    adapted_entry = {
        "Id": scenario_id,
        "Type": condition_entry["Type"],
        "MiniGameId": condition_entry["MiniGameMasterID"],
        "Options": condition_entry["Options"]
    }

    return adapted_entry