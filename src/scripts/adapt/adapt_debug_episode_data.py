import os
import json

from .episode_data.breakables import adapt_breakables_for_episode_layout
from .episode_data.checkpoints import adapt_checkpoints_for_episode_layout
from .episode_data.enemies import adapt_episode_enemies_for_episode_layout
from .episode_data.gimmicks import adapt_gimmicks_for_episode_layout
from .episode_data.npcs import adapt_npcs_for_episode_layout
from .episode_data.static_items import adapt_static_items_for_episode_layout
from .episode_data.secret_missions import adapt_secret_missions_for_episode_layout
from .episode_data.defense_targets import adapt_defense_targets_for_episode_layout


def load_json(path):
    with open(path, "r", encoding='utf-8') as f:
        return json.load(f)

'''
Add:
EventDrop ?
SecretMissions
Items
EventObjects
'''


layout_parts = [
    {
        "GroupName": "Breakables",
        "FileName": "EpisodeBreakableMasterDataObject",
        "Function": adapt_breakables_for_episode_layout
    },
    {
        "GroupName": "CheckPoints",
        "FileName": "EpisodeCheckPointMasterDataObject",
        "Function": adapt_checkpoints_for_episode_layout
    },
    {
        "GroupName": "Enemies",
        "FileName": "EpisodeEnemyMasterDataObject",
        "Function": adapt_episode_enemies_for_episode_layout
    },
    {
        "GroupName": "Gimmicks",
        "FileName": "EpisodeGimmickMasterDataObject",
        "Function": adapt_gimmicks_for_episode_layout
    },
    {
        "GroupName": "Npcs",
        "FileName": "EpisodeNPCMasterDataObject",
        "Function": adapt_npcs_for_episode_layout
    },
    {
        "GroupName": "StaticItems",
        "FileName": "EpisodeStageItemMasterDataObject",
        "Function": adapt_static_items_for_episode_layout
    },
    {
        "GroupName": "SecretMissions",
        "FileName": "EpisodeSecretMissionMasterDataObject",
        "Function": adapt_secret_missions_for_episode_layout
    },
    {
        "GroupName": "DefenseTargets",
        "FileName": "EpisodeDefenseTargetMasterDataObject",
        "Function": adapt_defense_targets_for_episode_layout
    }
]


def fill_episode_layout_group_by_episode_id(episode_id):
    LayoutGroup = {
        "Breakables": [],
        "CheckPoints": [],
        "Enemies": [],
        # Event drop? Where does it go?
        "EventObjects": [],
        "Gimmicks": [],
        "Npcs": [],
        "SecretMissions": [],
        "Items": [],
        "StaticItems": [],
        "EventItems": [],
        "DefenseTargets": []
    }

    episode_master_data_path = "./data/masterdata/episode/{0}/".format(episode_id)

    # Get a list of files in the relevant episode data folder
    episode_master_data_path_files = os.listdir(episode_master_data_path)

    # Load each episode data file
    for layout_group in layout_parts:
        group_name = layout_group["GroupName"]
        file_name = layout_group["FileName"] + ".json"
        adapt_function = layout_group["Function"]

        if file_name in episode_master_data_path_files:
            master_data = load_json(episode_master_data_path + file_name)

            if group_name == "Gimmicks":
                LayoutGroup[group_name] = adapt_function(master_data, episode_id)
            else:
                LayoutGroup[group_name] = adapt_function(master_data)

    return LayoutGroup
