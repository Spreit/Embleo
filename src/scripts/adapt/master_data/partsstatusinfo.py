def adapt_debug_parts_status_info_master_data(debug_data):
    adapted_entries = []

    for entry in debug_data["_datas"]:
        adapted_entry = {
            "Index": entry["_id"],
            "DamageRate": entry["_damageRate"]
        }

        adapted_entries.append(adapted_entry)

    return adapted_entries


if __name__ == "__main__":
    debugPartsStatusInfo_path = "../masterdatadebug/PartsStatusInfo.json"
    output_path = "./Adapted MasterData/PartsStatusInfo.json"

    adapted_data = adapt_debug_parts_status_info_master_data(debugPartsStatusInfo_path)

    # CommonJSONFunctions.save_json(output_path, adapted_data)

