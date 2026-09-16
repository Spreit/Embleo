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

def adapt_episode_enemies_for_episode_layout(master_data):
	enemies = []

	# yeah, that's a lot of data
	for entry in master_data["Datas"]:
		layout_entry = {
			"EpisodeEnemyId": entry["_id"],
			"EnemyId": entry["_individualID"],
			"RoleType": entry["_enemyType"] + 1,  # 0 is Unknown and breaks enemy
			"Flags": 0,

			"AppearanceNum": entry["_appearanceNum"],
			"MaxAppearanceNum": entry["_appearanceNum"],

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
			"Params": [entry["_appearanceParam1"]]
		}

		# EpisodeEnemyChild
		layout_entry["Child"] = {
			"Ids": entry["_childEnemyData"]["EnemyIds"],
			"Formation": entry["_childEnemyData"]["FormationId"],
			# "FormationPadding": SerVec2toVec2({"x": 0, "y": 0})
		}

		# EpisodeEnemySummonRule
		layout_entry["SummonRule"] = {
			"EpisodeEnemyId": entry["_summonEnemyData"]["EnemyId"],
			"InitialAppearNum": entry["_summonEnemyData"]["_initialAppearNum"],
			"MinLimitNum": entry["_summonEnemyData"]["_minLimitNum"],
			"TotalNum": entry["_summonEnemyData"]["_totalNum"],
			"Offset": SerVec2toVec2(entry["_summonEnemyData"]["Offset"]),
			"Range": SerVec2toVec2(entry["_summonEnemyData"]["Range"]),
			"AppearPointName": entry["_summonEnemyData"]["AppearPointName"],
			"DieWithChild": bool(entry["_summonEnemyData"]["DieWithChild"]),
			"InitRotateAngle": entry["_summonEnemyData"]["InitRotateAngle"],
			"OffsetAdd": SerVec2toVec2(entry["_summonEnemyData"]["OffsetAdd"]),
			"RangeAdd": SerVec2toVec2(entry["_summonEnemyData"]["RangeAdd"]),
			"InitRotateAngleAdd": entry["_summonEnemyData"]["InitRotateAngleAdd"]
		}

		enemies.append(layout_entry)

	return enemies
