import os
import json
from pathlib import Path

from .master_data.buff import adapt_debug_buff_master_data
from .master_data.character import adapt_debug_character_master_data
from .master_data.enemy import adapt_debug_enemy_master_data
from .master_data.enemy_individual import adapt_debug_enemy_individual_master_data
from .master_data.episode_character_visual_data import adapt_debug_episode_character_visual_master_data
from .master_data.equipment import adapt_equipment_master_data
from .master_data.sequence import adapt_debug_sequences_master_data
from .master_data.item import adapt_debug_item_master_data
from .master_data.partsstatusinfo import adapt_debug_parts_status_info_master_data
from .master_data.platoon import adapt_debug_platoon_info
from .master_data.secret_mission import adapt_debug_secret_missions
from .master_data.stage_option_gimmick import adapt_debug_stage_option_gimmick_master_data
from .master_data.vehicle import adapt_debug_vehicle_master_data


adapt_debug_functions = [
    {
        "DisplayName": "Buffs",
        "DebugName": "BuffMasterDataObject",
        "AdaptName": "BuffMasterData",
        "Function": adapt_debug_buff_master_data
    },
    {
        "DisplayName": "Character Master Data",
        "DebugName": "Character",
        "AdaptName": "CharacterMasterData",
        "Function": adapt_debug_character_master_data
    },
    {
        "DisplayName": "Enemy Master Data",
        "DebugName": "Enemy",
        "AdaptName": "EnemyMasterData",
        "Function": adapt_debug_enemy_master_data
    },
    {
        "DisplayName": "Enemy Individual",
        "DebugName": "EnemyIndividualMasterDataObject",
        "AdaptName": "EnemyIndividualMasterData",
        "Function": adapt_debug_enemy_individual_master_data
    },
    {
        "DisplayName": "Episode Character Visuals",
        "DebugName": "EpisodeCharacterVisual",
        "AdaptName": "EpisodeCharacterVisualMasterData",
        "Function": adapt_debug_episode_character_visual_master_data
    },
    {
        "DisplayName": "Episode Master Data",
        "DebugName": "Equipment",
        "AdaptName": "EquipmentMasterData",
        "Function": adapt_equipment_master_data
    },
    {
        "DisplayName": "Item Master Data",
        "DebugName": "ItemMasterDataObject",
        "AdaptName": "ItemMasterData",
        "Function": adapt_debug_item_master_data
    },
    {
        "DisplayName": "PartsStatusInfo",
        "DebugName": "PartsStatusInfo",
        "AdaptName": "PartsStatusInfo",
        "Function": adapt_debug_parts_status_info_master_data
    },
    {
        "DisplayName": "PlatoonMasterData",
        "DebugName": "PlatoonMasterDataObject",
        "AdaptName": "PlatoonMasterData",
        "Function": adapt_debug_platoon_info
    },
    {
        "DisplayName": "Secret Missions",
        "DebugName": "SecretMission",
        "AdaptName": "SecretMissions",
        "Function": adapt_debug_secret_missions
    },
    {
        "DisplayName": "Stage Option Gimmick",
        "DebugName": "StageOptionGimmickMasterDataObject",
        "AdaptName": "StageOptionGimmickMasterData",
        "Function": adapt_debug_stage_option_gimmick_master_data
    },
    {
        "DisplayName": "Vehicle (Patara)",
        "DebugName": "VehicleMasterDataObject",
        "AdaptName": "VehicleMasterData",
        "Function": adapt_debug_vehicle_master_data
    }
]


def adapt_debug_master_data(extract_folder, output_folder):
    # Adapt all extracted data
    print("= = = Adapting extracted data (may take some time) = = =")

    extract_debug_master_data_folder_path = extract_folder / "masterdatadebug"

    # Go through the list of functions and what files they need to adapt
    for entry in adapt_debug_functions:
        display_name = entry["DisplayName"]
        debug_name = entry["DebugName"]
        adapt_name = entry["AdaptName"]
        adapt_function = entry["Function"]

        print("Adapting", display_name)

        debug_file_path = extract_debug_master_data_folder_path / (debug_name + ".json")
        adapted_file_path = output_folder / (adapt_name + ".json")
        
        debug_data: dict
        with open(debug_file_path, "r", encoding="UTF-8") as f:
            debug_data = json.load(f)

        adapted_data = adapt_function(debug_data)
        
        os.makedirs(os.path.dirname(adapted_file_path), exist_ok=True)
        with open(adapted_file_path, "w") as of:
            json.dump(adapted_data, of, ensure_ascii=False, indent=4)

    # Sequence Data is handles separately, because it produces two files
    print("Adapting Sequence Master Data")
    adapt_debug_sequences_master_data(extract_debug_master_data_folder_path / "SequenceMasterDataObject.json",
                                      output_folder)
