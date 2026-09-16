def adapt_event_items_for_episode_layout(debug_data):
	adapted_entry_list = []

	for entry in debug_data["Datas"]:
		adapted_entry = {
			"EpisodeCheckPointId": entry["_id"],
			"Flag": entry["Flag"],

			"LoadPlayers": entry["LoadPlayers"],
			"LoadLocations": entry["LoadLocations"],
			"LocationGroups": entry["LoadLocationGroupIndexs"],

			"PartyPlayers": entry["PartyPlayers"],
			"PartyFlags": [],  # entry["PartyFlags"],
			"PartyParams": entry["PartyParams"],

			"ScenarioNo": [entry["_startScenarioNo"], entry["_endScenarioNo"]]
		}

		# Adapt PartyFlags
		for flag in entry["PartyFlags"]:
			proper_flag = {
				"FlagType": flag["FlagType"],
				"Value": bool(flag["Value"])
			}

			adapted_entry["PartyFlags"].append(proper_flag)

		adapted_entry_list.append(dict.copy(adapted_entry))

	return adapted_entry_list
