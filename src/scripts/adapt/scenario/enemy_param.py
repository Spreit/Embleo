import os

def adapt_debug_scenario_enemy_param(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressEnemyParam"]

    adapted_entry = {
        "Id": scenario_id,
        "GroupId": condition_entry["GroupId"],
        "States": condition_entry["States"],
        "Wait": bool(condition_entry["IsWait"]),
        "CancelAtContinue": bool(condition_entry["CancelAtContinue"]),
    }

    return adapted_entry