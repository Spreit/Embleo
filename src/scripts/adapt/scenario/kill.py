import os

def adapt_debug_scenario_kill(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressKill"]

    # ProgressKill
    adapted_entry = {
        "ProgressKillId": scenario_id,
        "EnemyGroupId": condition_entry["EnemyGroupId"],
        "Count": condition_entry["Count"],
        "LimitTime": condition_entry["LimitTime"],
        "Actions": [],
        "NocreateAtContinue": bool(condition_entry["NocreateAtContinue"])
    }

    # class EpisodeEnemyScriptAction
    for action in condition_entry["EnemyScriptActions"]:
        new_action = {
            "Type": action["Type"],
            "Rate": action["Rate"],
            "Event": {}
        }

        new_action["Event"] = {
            "Flag": 0,
            "TriggerType": 1,  # Where do I get this?
            "ActionType": action["ActionType"],
            "ScriptPath": action["ScriptPath"],
            "Param": "",
            "Drop": {
                "Id": action["EventDropInfo"]["ID"]
            }
        }

        adapted_entry["Actions"].append(new_action)

    return adapted_entry