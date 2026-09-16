import json


def adapt_debug_buff_master_data(debug_data):
    data = debug_data["_infos"]

    for entry in data:
        entry["ExParam"] = json.dumps(entry["ExParam"])

    return data