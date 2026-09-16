import json

user_episode_base = {
    "EpisodeId": "pl001_ep001",
    "Status": 0,
    "ChapterUser": {
        "Status": 0,
        "FieldCoinCounts": [0, 0, 0, 0]
    },
    "SecretMissionUser": {
        "Statuses": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    },
    "TreasureCount": 0,
    "Progress": [0, 0, 0, 0],
    "IsLike": False,
    "FirstClearDate": "2021-01-01T00:00:00Z",
    "UnacquiredItems": []
}


def generate_episode_id_list():
    episode_id_list = []

    # All episodes, up to ep.Final
    # not all are playable though
    episode_id_template = "{0}_{1}"
    char_id_template = "pl{:03d}"
    ep_num_template = "ep{:03d}"

    for episode_number in range(1, 4):
        # Character episodes
        for char_number in range(1, 22):
            char_id = char_id_template.format(char_number)
            ep_num = ep_num_template.format(episode_number)

            episode_id = episode_id_template.format(char_id, ep_num)
            episode_id_list.append(episode_id)

        # Crossroads episodes
        char_id = "mstone"
        ep_num = ep_num_template.format(episode_number)

        episode_id = episode_id_template.format(char_id, ep_num)
        episode_id_list.append(episode_id)

    return episode_id_list


def generateUserEpisode(unlock_chapters=False, unlock_secret_missions=True):
    user_episode_data = []

    episode_id_list = generate_episode_id_list()

    for episode_id in episode_id_list:
        user_episode = dict.copy(user_episode_base)

        user_episode["EpisodeId"] = episode_id

        if unlock_chapters:
            user_episode["Status"] = 1

        if unlock_secret_missions:
            for i in range(0, 10):
                user_episode["SecretMissionUser"]["Statuses"][i] = 1

        user_episode_data.append(user_episode)

    print("Generated UserEpisode data")

    return user_episode_data


if __name__ == "__main__":
    UserEpisode_data = generateUserEpisode()

    output_file_path = "./UserEpisode.json"

    with open(output_file_path, "w") as f:
        json.dump(UserEpisode_data, f, indent=4)
        print("Saved UserEpisode at", output_file_path)