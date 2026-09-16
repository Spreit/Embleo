# StaticItems (PB-stones, Apple Gummies)

def adapt_static_items_for_episode_layout(debug_data):
    static_items = []

    for entry in debug_data["Datas"]:
        layout_entry = {
            "EpisodeStaticItemId": entry["_id"],
            "Type": 0,
            # "ItemDropMethod": 0,
            "DropResourceId": entry["_masterID"],
            "ScenarioNo": [entry["_startScenarioNo"], entry["_endScenarioNo"]]
        }

        # PB Stones
        if entry["_masterID"] == "CorrectCoin":
            layout_entry["Type"] = 1
            layout_entry["ItemDropMethod"] = 0
        # Apple Gels from Pac-Man secret mission
        elif entry["_masterID"] == "AppleGumi":
            layout_entry["Type"] = 2
            layout_entry["ItemDropMethod"] = 0

        # layout_entry = {}

        static_items.append(layout_entry)

    return static_items