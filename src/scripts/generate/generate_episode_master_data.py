import json
import os
from enum import Enum, auto
from pathlib import Path

'''
All episode 1 and ep 2
'''

episode_master_base = {
        "EpisodeId": "pl001_ep001",
        "Category": 0,
        "CharacterId": "pl001",
        "EpisodeNo": 1,
        "Year": 0,
        "MinVerIOS": "1",
        "MinVerAndroid": "1",
        "Chapters": [],
        "SecretMissions": [],
        "MaxTreasureCount": 0,
        # "AdventureNo": 0,  # Not present on non-Adventurer's episode
        "LikeCount": 0,
        "CommentCount": 0,
        "StartAt": "2026-01-01T00:00:00Z"
}

chapter_master_base = {
                "Id": "pl001_ep002_cp01",
                "MaxFieldCoin": 100
            }

crossroads_characters = {
    "mstone_ep001": ["pl001", "pl002", "pl003"],
    "mstone_ep002": ["pl004", "pl006", "pl016"],  # Speculations
    "mstone_ep003": ["pl002", "pl004", "pl001", "pl003"]
}


class EpisodeCategory(Enum):
    character = 0
    crossroads = 1


def get_episode_years_from_adapted_chronology(adapted_chronology_path):
    chronology_files = os.listdir(adapted_chronology_path)

    episode_years = {
        "mstone_ep001": 998,
        "mstone_ep002": 0,
        "mstone_ep003": 999,
        "mstone_ep004": 999
    }

    for chronology_file_name in chronology_files:

        with open(adapted_chronology_path / chronology_file_name, 'r') as chronology_file:
            chronology = json.load(chronology_file)

            for entry in chronology["Chronologies"][0]["Events"]:
                if "EpisodeId" in entry:
                    episode_years[entry["EpisodeId"]] = entry["Year"]
                    # print(entry["EpisodeId"], entry["Year"])

    episode_years = {k: v for k, v in sorted(episode_years.items(), key=lambda item: item[0])}

    return episode_years


def get_adventurer_episode_order_from_adapted_chronology(adapted_chronology_path):
    adventurer_chronology_path = adapted_chronology_path / "adv.json"

    adv_episode_order = {}

    with open(adventurer_chronology_path, "r", encoding="UTF-8") as f:
        chronology = json.load(f)

        for entry in chronology["Chronologies"][0]["Events"]:
            if "EpisodeId" in entry:
                adv_episode_order[entry["EpisodeId"]] = entry["AdventureNo"]

    return adv_episode_order


def generate_episode_id_list():
    episode_id_list = []

    # Generate for all episodes up to Crossroads 3, even though not all are present.
    episode_id_template = "{0}_{1}"
    char_id_template = "pl{:03d}"
    ep_num_template = "ep{:03d}"
    mstone_template = "mstone_ep{:03d}"

    for episode_number in range(1,4):
        # Character Episodes
        for char_number in range(1, 22):
            char_id = char_id_template.format(char_number)
            ep_num = ep_num_template.format(episode_number)

            episode_id = episode_id_template.format(char_id, ep_num)
            episode_id_list.append(episode_id)

        # Crossroads
        episode_id_list.append(mstone_template.format(episode_number))

    return episode_id_list


def generate_episode_chapters(episode_id):
    chapters = []

    for i in range(1,5):
        chapter = dict.copy(chapter_master_base)
        chapter_id_format = "{episode_id}_cp0{chapter_digit}"

        chapter["Id"] = chapter_id_format.format(episode_id=episode_id,
                                                 chapter_digit=i)

        # MaxFieldCoin needs to be calculated based on level data
        chapters.append(chapter)

    return chapters


def generate_episode_master_entry(episode_id, episode_year, adventurer_episode_number=0):
    episode = dict.copy(episode_master_base)

    episode["EpisodeId"] = episode_id

    char_id, ep_num = episode_id.split("_")

    episode["CharacterId"] = char_id

    if "mstone" in episode_id:
        episode["Category"] = EpisodeCategory.crossroads.value
        episode["CharacterId"] = ""
        episode["MilestoneCharacterIds"] = crossroads_characters[episode_id]

    episode["EpisodeNo"] = int(ep_num[-1])

    episode["Year"] = episode_year

    episode["Chapters"] = generate_episode_chapters(episode_id)

    if adventurer_episode_number > 0:
        episode["AdventureNo"] = adventurer_episode_number

    return episode


def generate_episode_master_data(output_folder, adapted_chronology_folder, secret_missions_file_path):
    episode_master_data = []

    episode_id_list = generate_episode_id_list()
    episode_years = get_episode_years_from_adapted_chronology(adapted_chronology_folder)
    adv_episode_order = get_adventurer_episode_order_from_adapted_chronology(adapted_chronology_folder)

    secret_missions = {}
    with open(secret_missions_file_path, "r") as f:
        secret_missions = json.load(f)

    for episode_id in episode_id_list:
        episode_year = episode_years.get(episode_id, 0)
        adventurer_episode_number = adv_episode_order.get(episode_id, 0)

        episode_master_entry = generate_episode_master_entry(episode_id, episode_year, adventurer_episode_number)
        episode_master_entry["SecretMissions"] = secret_missions.get(episode_id, [])

        episode_master_data.append(episode_master_entry)

    with open(output_folder / "EpisodeMasterData.json", "w") as f:
        json.dump(episode_master_data, f, indent=4)


if __name__ == "__main__":
    generate_episode_master_data()