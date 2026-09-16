

def adapt_debug_vehicle_master_data(debug_data):

    adapted_entries = []
    for entry in debug_data["Datas"]:
        adapted_entry = {
            "VehicleId": entry["_id"],

            "InitialSpeeds": [],
            "MaxSpeeds": [],
            "Accelerations": [],
            "Decelerations": [],

            "ExtraDashTime": entry["_extraDashTime"],

            "DashStartCount": entry["_dashStart"]["Count"],
            "IncDashStartCount": entry["_dashStart"]["IncCount"],
            "DecDashStartCount": entry["_dashStart"]["DecCount"],

            "DashStopCount": entry["_dashStop"]["Count"],
            "IncDashStopCount": entry["_dashStop"]["IncCount"],
            "DecDashStopCount": entry["_dashStop"]["DecCount"],

            "RotationalSpeed": entry["_moveSetting"]["RotationalSpeed"],
            "SpeedDownRange": entry["_moveSetting"]["SpeedDownRange"],

            # Aren't specified in debug data
            # "InitialSpeed": entry["Value"],
            # "Acceleration": entry["Value"],
            # "NormalSpeedMax": entry["Value"],
            # "DashSpeedRate": entry["Value"],
            # "DashTime": entry["Value"]
        }

        for speed_entry in entry["_speed"]:
            adapted_entry["InitialSpeeds"].append(speed_entry["Init"])
            adapted_entry["MaxSpeeds"].append(speed_entry["Max"])
            adapted_entry["Accelerations"].append(speed_entry["Acceleration"])
            adapted_entry["Decelerations"].append(speed_entry["Deceleration"])

        adapted_entries.append(adapted_entry)

    return adapted_entries


if __name__ == "__main__":
    debugPartsStatusInfo_path = "../masterdatadebug/VehicleMasterDataObject.json"
    output_path = "./Adapted MasterData/VehicleMasterData.json"

    adapted_data = adapt_debug_vehicle_master_data(debugPartsStatusInfo_path)

    # CommonJSONFunctions.save_json(output_path, adapted_data)

