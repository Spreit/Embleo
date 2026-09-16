def adapt_npcs_for_episode_layout(debug_data):
    npcs = []

    for entry in debug_data["Datas"]:

        layout_entry = {
            "EpisodeNpcId": entry["_id"],
            "ResourceId": entry["_masterID"],
            "TalkEvents": [],
            "ScenarioNo": [entry["_startScenarioNo"], entry["_endScenarioNo"]]
        }

        # Fill TalkEvents
        # print(entry["_id"])
        for talk_event in entry["EventInfos"]:
            episode_talk_event = {
                "EpisodeEvent": {},
                "Flag": talk_event["Flag"],
                "TalkCount": talk_event["ExecCount"],
                "ScenarioNo": [talk_event["StartScenarioNo"], talk_event["EndScenarioNo"]]
            }

            episode_talk_event["EpisodeEvent"] = {
                "Flag": talk_event["TalkFlag"],

                "ScriptPath": talk_event["ScriptPath"],
                "TriggerType": talk_event["Trigger"],
                "ActionType": talk_event["Execute"],
                "Param": talk_event["EventParam"],

                "Drop": {
                    "Id": talk_event["EventDropInfo"]["ID"]
                }
            }

            layout_entry["TalkEvents"].append(episode_talk_event)

        npcs.append(layout_entry)

    return npcs