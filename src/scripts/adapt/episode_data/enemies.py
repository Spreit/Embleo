def SerVec2toVec2(SerializableVector2):
	vector_2 = [
		SerializableVector2["x"],
		SerializableVector2["y"]
	]

	return vector_2


def SerVec3toVec3(SerializableVector3):
	vector_3 = [
		SerializableVector3["x"],
		SerializableVector3["y"],
		SerializableVector3["z"]
	]

	return vector_3

def episode_enemy_individual_ids(master_data):
	"""All placed, parent-child and generator individuals, in source order."""
	ids = []
	seen = set()
	for entry in master_data["Datas"]:
		candidates = [entry["_individualID"],
			*entry["_childEnemyData"]["EnemyIds"],
			entry["_summonEnemyData"]["EnemyId"]]
		for individual_id in candidates:
			if individual_id and individual_id not in seen:
				seen.add(individual_id)
				ids.append(individual_id)
	return ids


def adapt_episode_enemies_for_episode_layout(master_data, *, platoon_master_data=None):
	enemies = []
	external_enemies = []
	used_ids = {entry["_id"] for entry in master_data["Datas"]}
	formations = {entry["_id"]: entry
		for entry in (platoon_master_data or {"Datas": []})["Datas"]}

	# yeah, that's a lot of data
	for entry in master_data["Datas"]:
		layout_entry = {
			"EpisodeEnemyId": entry["_id"],
			"EnemyId": entry["_individualID"],
			"RoleType": entry["_enemyType"] + 1,  # 0 is Unknown and breaks enemy
			# "Flags": 0,

			"AppearanceNum": entry["_appearanceNum"],
			"MaxAppearanceNum": entry["_appearanceNum"] + 10,

			"GroupId": entry["_groupID"],

			"AppearanceRule": {},
			"Child": {},
			"SummonRule": {},

			"VisualId": entry["_charactorVisualId"],  # Yes, charactor
			"SurviveId": entry["_surviveId"],

			"PatrolPoints": entry["_patrolPoints"],
			"PriorityPoint": entry["_priorityPoint"],

			"ScenarioNo": [entry["_startScenarioNo"], entry["_endScenarioNo"]]
		}

		# EpisodeEnemyAppearanceRule
		layout_entry["AppearanceRule"] = {
			"Type": entry["_appearanceID"],
			"Params": [entry["_appearanceParam1"], str(entry["_appearanceIntParam1"])]
		}

		# EpisodeEnemyChild
		formation_id = entry["_childEnemyData"]["FormationId"]
		formation = formations.get(formation_id)
		if formation_id and formation is None:
			raise ValueError("Unknown platoon formation {!r} for episode enemy {!r}".format(
				formation_id, entry["_id"]))
		layout_entry["Child"] = {
			"Ids": entry["_childEnemyData"]["EnemyIds"],
			"Formation": formation["Formation"] if formation else "",
			"FormationPadding": SerVec2toVec2(formation["FormationPadding"])
				if formation else [0, 0]
		}

		summon_data = entry["_summonEnemyData"]

		# EpisodeEnemySummonRule
		layout_entry["SummonRule"] = {
			"EpisodeEnemyId": summon_data["EnemyId"],
			"InitialAppearNum": summon_data["_initialAppearNum"],
			"MinLimitNum": summon_data["_minLimitNum"],
			"TotalNum": summon_data["_totalNum"],
			"Offset": SerVec2toVec2(summon_data["Offset"]),
			"Range": SerVec2toVec2(summon_data["Range"]),
			"AppearPointName": summon_data["AppearPointName"],
			"DieWithChild": bool(summon_data["DieWithChild"]),
			"InitRotateAngle": summon_data["InitRotateAngle"],
			"OffsetAdd": SerVec2toVec2(summon_data["OffsetAdd"]),
			"RangeAdd": SerVec2toVec2(summon_data["RangeAdd"]),
			"InitRotateAngleAdd": summon_data["InitRotateAngleAdd"]
		}

		enemies.append(layout_entry)

		# Release clients do not run the debug-local external-definition builder.
		# These definitions are looked up by child/summon creation, never placed.
		targets = (entry["_childEnemyData"]["EnemyIds"] if entry["_enemyType"] == 1
			else [summon_data["EnemyId"]] if entry["_enemyType"] == 2
			else [])
		for individual_id in dict.fromkeys(targets):
			if not individual_id:
				continue
			external_id = "Ext.{}.{}".format(entry["_id"], individual_id)
			if external_id in used_ids:
				raise ValueError("Duplicate external episode enemy {!r}".format(external_id))
			used_ids.add(external_id)
			external_enemies.append({
				"EpisodeEnemyId": external_id,
				"EnemyId": individual_id,
				"RoleType": 1,
				"Flags": layout_entry.get("Flags", 0) & 8,  # Inherit only the parent's wait state.
				"AppearanceNum": 1,
				"MaxAppearanceNum": 1,
				"GroupId": entry["_groupID"],
				"AppearanceRule": {"Type": 2, "Params": []},
				"Child": None,
				"SummonRule": None,
				"VisualId": "",
				"SurviveId": "",
				"PatrolPoints": [],
				"PriorityPoint": "",
				"ScenarioNo": list(layout_entry["ScenarioNo"]),
			})

	return enemies + external_enemies
