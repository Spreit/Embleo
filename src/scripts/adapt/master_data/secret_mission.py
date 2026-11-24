
def adapt_debug_secret_missions(debug_secret_missions):
    secret_missions = []

    # Just take Base from each entry
    for entry in debug_secret_missions["Datas"]:
        mission_info = entry["Base"]
        secret_missions.append(mission_info)

    # Sort by secret mission ID
    secret_missions.sort(key=lambda mission: mission["Id"])

    # Group by episode id
    secret_missions_by_episode_id = {}

    for mission_info in secret_missions:
        # pl001_ep001_sc01
        secret_mission_id = mission_info["Id"]
        episode_id = secret_mission_id[:secret_mission_id.rfind("_")]

        secret_missions_by_episode_id.setdefault(episode_id, [])

        secret_missions_by_episode_id[episode_id].append(mission_info)

    return secret_missions_by_episode_id
