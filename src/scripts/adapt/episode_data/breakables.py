def adapt_breakables_for_episode_layout(debug_data):
    breakables = []

    for entry in debug_data["Datas"]:
        layout_entry = {
            "EpisodeBreakableId": entry["_id"],
            "ResourceId": entry["_masterID"]
        }

        breakables.append(dict.copy(layout_entry))

    return breakables
