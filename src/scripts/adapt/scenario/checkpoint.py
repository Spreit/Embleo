def adapt_debug_scenario_checkpoint(debug_condition, scenario_id):
	condition_entry = debug_condition["ProgressCheckPoint"]

	adapted_entry = {
		"ProgressCheckPointId": scenario_id,
		"LayoutCheckPointId": condition_entry["CheckPointId"],
		"RequestSave": True, # bool(condition_entry["RequestSave"]),  # MUST be true or it will softlock the game
		"IsReload": bool(condition_entry["IsReload"]),
		"IsDarkenRestart": bool(condition_entry["IsDarkenRestart"]),
		"Progress": condition_entry["Progress"]
	}
	
	'''
	if adapted_entry["IsReload"] or adapted_entry["IsDarkenRestart"]:
		adapted_entry["RequestSave"] = True
	'''
	
	return adapted_entry
