
def adapt_secret_missions_for_episode_layout(debug_data):
    secret_missions = []

    for entry in debug_data["Datas"]:
        layout_entry = {
            "EpisodeSecretMissionId": entry["_id"],
            "SecretMissionId": entry["_masterID"],
            # "IsOpenOnly": True, # ???
            "ScenarioNo": [entry["_startScenarioNo"], entry["_endScenarioNo"]]
        }

        secret_missions.append(layout_entry)

    return secret_missions
