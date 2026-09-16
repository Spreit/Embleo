
def adapt_defense_targets_for_episode_layout(debug_data):
    defense_targets = []

    for entry in debug_data["Datas"]:
        layout_entry = {
            "Id": entry["_id"],
            "Hp": entry["_hp"],
            "TargetType": entry["_type"],
            "TargetId": entry["_targetID"],
            "HatePoint": entry["_hatePoint"],
            "ScenarioNo": [entry["_startScenarioNo"], entry["_endScenarioNo"]]
        }

        defense_targets.append(layout_entry)

    return defense_targets
