def adapt_debug_item_master_data(debug_data):
    adapted_entries = []

    entries = debug_data["Datas"]

    for entry in entries:
        renamed_entry = {}

        renamed_entry["ItemId"] = entry["_id"]
        renamed_entry["Category"] = entry["_category"]
        renamed_entry["Rarity"] = entry["_rarity"]
        # renamed_entry["Number"] = 1

        renamed_entry["ResultValue"] = entry["_resultValue"]

        renamed_entry["LikeCharacter"] = entry["_likeCharacter"]
        renamed_entry["NotLikeCharacter"] = entry["_notLikeCharacter"]

        renamed_entry["Recipe"] = []
        renamed_entry["RecipeNum"] = []
        renamed_entry["SubCategory"] = 0

        renamed_entry["BuffLike"] = entry["_buffLike"]
        renamed_entry["BuffNotLike"] = entry["_buffNotLike"]
        renamed_entry["BuffUsually"] = entry["_buffUsually"]

        adapted_entries.append(renamed_entry)

    return adapted_entries
