def adapt_debug_stage_option_gimmick_master_data(debug_data):
    # 💀, save unadapted data
    return debug_data

    # Get all area ids
    stage_option_gimmick_data = debug_data["Datas"]

    stage_option_area_gimmicks = {}

    for area_entry in stage_option_gimmick_data:
        stage_map_id = area_entry["_id"]

        for gimmick in area_entry["infos"]:
            gimmick_id = gimmick["_id"]

            area_gimmick = {
                "StageMapID": stage_map_id,
                "Gimmick": gimmick
            }

            stage_option_area_gimmicks[gimmick_id] = area_gimmick

    return stage_option_area_gimmicks

    for gimmick_id in scenario_gimmick_id_list:
        if gimmick_id in stage_option_area_gimmicks:
            gimmick = adapt_episode_layout_gimmick(stage_option_area_gimmicks[gimmick_id]["Gimmick"])

            # Assign StageMapID, so the gimmick appears where it should.
            gimmick["StageMapID"] = stage_option_area_gimmicks[gimmick_id]["StageMapID"]
            # print(gimmick["StageMapID"], gimmick_id)

            LayoutGroup["Gimmicks"].append(gimmick)
