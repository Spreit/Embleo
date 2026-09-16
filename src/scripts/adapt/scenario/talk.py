import os

def adapt_debug_scenario_talk(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressTalk"]

    adapted_entry = {
        "ProgressTalkId": scenario_id,
        "LayoutNpcId": condition_entry["NpcIds"][0],
        "NpcIds": condition_entry["NpcIds"],
        "TargetCount": condition_entry["TargetCount"]
    }

    return adapted_entry