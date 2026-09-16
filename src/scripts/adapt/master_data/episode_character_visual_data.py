visual_base = {
	"VisualId": "",
	"CharacterId": "",
	"VisualEquipment": []
}

def fill_base_dict_with_debug_data_if_same_keys(basedata, debugdata):
    result = dict.copy(basedata)

    for key in basedata.keys():
        if key in debugdata:
            result[key] = debugdata[key]

    return result

def adapt_debug_episode_character_visual_master_data(DebugMasterData):
    AdaptedMasterData = []

    for debug_entry in DebugMasterData["Datas"]:
        AdaptedEntry = fill_base_dict_with_debug_data_if_same_keys(visual_base, debug_entry)

        AdaptedEntry["VisualId"] = debug_entry["ID"]

        AdaptedMasterData.append(AdaptedEntry)

    return AdaptedMasterData
