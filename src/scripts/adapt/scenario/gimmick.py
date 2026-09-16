import os

def adapt_debug_scenario_gimmick(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressGimmick"]

    adapted_entry = {
        "ProgressGimmickId": scenario_id,
        "Gimmicks": []
    }

    for operation in condition_entry["GimmickOperations"]:
        adapted_entry["Gimmicks"].append(operation)

    return adapted_entry