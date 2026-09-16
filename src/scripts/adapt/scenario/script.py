import os

def adapt_debug_scenario_script(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressScript"]

    adapted_entry = {
        "ProgressScriptId": scenario_id,
        "Event": {},
        "EndWait": bool(condition_entry["EndWait"])
    }

    adapted_entry["Event"] = {
        "Flag": condition_entry["Flag"],
        "TriggerType": 1,  # Where do I get this?
        "ActionType": condition_entry["ActionType"],
        "ScriptPath": condition_entry["ScriptPath"],
        "Param": "",
        "Drop": {
            "Id": condition_entry["EventDropInfo"]["ID"]
        }
    }

    return adapted_entry