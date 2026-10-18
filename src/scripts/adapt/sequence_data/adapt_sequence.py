import copy
import UnityPy
import json
from pathlib import Path

from .tracks.Animator import adapt_animator_track
from .tracks.Attack import adapt_attack_track
from .tracks.Move import adapt_move_track
from .tracks.UpdateParameter import adapt_update_parameter_track


sequence_timeline_script_PathID = 5650615754327761616


def group_files_by_PathID(asset_env):
    grouped_objects = {}

    for obj in asset_env.objects:
        grouped_objects[str(obj.path_id)] = obj

    return grouped_objects


def deref_tracks(tracks, PathID_files):
    parsed_tracks = []

    for track in tracks:
        track_MonoBehaviour_PathID = str(track["behaviourPrefab"]["m_PathID"])

        if track_MonoBehaviour_PathID not in PathID_files:
            print("Couldn't find track PathID", track_MonoBehaviour_PathID)
            continue

        parsed_track = {
            "behaviour": PathID_files[str(track_MonoBehaviour_PathID)].parse_as_dict(),
            "clips": [],
            "keys": track["keys"]
        }

        for clip in track["clips"]:
            clip_MonoBehaviour_PathID = str(clip["behaviourPrefab"]["m_PathID"])

            if clip_MonoBehaviour_PathID not in PathID_files:
                print("Couldn't find clip PathID", clip_MonoBehaviour_PathID)
                continue

            parsed_clip = {
                "behaviour": PathID_files[str(clip_MonoBehaviour_PathID)].parse_as_dict()
            }

            parsed_track["clips"].append(parsed_clip)

        parsed_tracks.append(parsed_track)

    return parsed_tracks


def get_sequence_timeline_data(bundle_env, sequence_timeline_PathID, sequence_name, owner_id):
    # Group AssetBundle files by m_PathID
    PathID_files = group_files_by_PathID(bundle_env)

    sequence_timeline_PathID = str(sequence_timeline_PathID)

    # print(owner_id, sequence_name)

    sequence_timeline = {}

    if sequence_timeline_PathID == "":
        # Find by sequence_name
        for obj in bundle_env.objects:
            if obj.peek_name() == sequence_name:
                sequence_timeline = obj.parse_as_dict()

    elif sequence_timeline_PathID in PathID_files:
        sequence_timeline = PathID_files[sequence_timeline_PathID].parse_as_dict()

    else:
        print("Couldn't find timeline", sequence_timeline_PathID, "in", owner_id, " - ", sequence_name)
        return {}

    try:
        sequence_timeline["tracks"]
    except KeyError:
        print("Timeline has no tracks", owner_id, sequence_name, "-", sequence_timeline_PathID)

    # Get all objects, referenced by action_objects
    deref_sequence_timeline = {
        "owner_id": owner_id,
        "action_name": sequence_name,
        "tracks": deref_tracks(sequence_timeline["tracks"], PathID_files)
    }

    # print(deref_sequence_track_data)

    return deref_sequence_timeline


RESOURCE_KEYS = {
    'HitEffect': 21, 'OWWallHitEffect': 21, 'OWTerminateEffect': 21,
    'HitSE': 20, 'WallHitSE': 20,
    'SeId': 10, 'SeIdAddBulletShot': 10, 'SeIdFinish': 10,
    'ShotSE': 10, 'TerminateSE': 10, 'BulletSE': 10,
    'soundKey': 10, 'soundKeyList': 10, 'SoundKey': 10, 'SoundKeyList': 10,
    'BulletCreateSeName': 10, 'BulletCreateSeNames': 10,
    'BulletCreatedLoopSeName': 10, 'BulletShotSeName': 10,
    'FinishEffectSE': 10, 'StaySeName': 10, 'AreaEffect': 21,
    'PrefabPath': 1, 'DisappearSE': 20, 'DisappearEffect': 21,
    'EventAttackBreakSE': 20, 'EventAttackBreakEffect': 21,
}

RESOURCE_CLIPS = [
    "EffectCall Clip"
]


def collect_resources(container):
    resources = {}

    def add_resource(resource_type, value):
        if isinstance(value, list):
            for item in value:
                add_resource(resource_type, item)
        elif isinstance(value, str) and value:
            resources.setdefault((resource_type, value), {'type': resource_type, 'value': value})

    def scan_for_resources(value):
        if isinstance(value, list):
            for item in value:
                scan_for_resources(item)
        elif isinstance(value, dict):
            for key, item in value.items():
                if key in RESOURCE_KEYS:
                    resource_type = RESOURCE_KEYS[key]

                    if key in ("soundKey", "soundKeyList") and value.get('m_Name', '').startswith('VoiceCall'):
                        resource_type = 30

                    add_resource(resource_type, item)
                elif isinstance(item, str) and item.startswith("External/"):
                    add_resource(1, item)
                else:
                    scan_for_resources(item)

    scan_for_resources(container)

    if resources:
        # print(resources)
        pass

    return resources


def adapt_sequence_timeline(sequence_timeline, owner_id):
    adapted_sequence = {
        "AttackSetting": {},
        "MoveSetting": {},
        "UpdateParameterSetting": {},
        "ResourceList": {}
    }

    action_name = sequence_timeline["action_name"]
    # print("Action Name", action_name)

    base_attack_info = {}

    attack_clips = [clip for track in sequence_timeline['tracks']
                    if track['behaviour']['m_Name'] == 'Attack Track' for clip in track['clips']]
    adapted_attack = False

    for track in sequence_timeline["tracks"]:

        track_behaviour_name = track["behaviour"]["m_Name"]

        if track_behaviour_name == "Animator Track":
            base_attack_info = adapt_animator_track(track)

        elif track_behaviour_name == "Attack Track":
            if not adapted_attack:
                attack_data = adapt_attack_track({'clips': attack_clips}, action_name, owner_id)
                if attack_data['totalClipCount'] > 0:
                    adapted_sequence["AttackSetting"] = attack_data
                adapted_attack = True

        elif track_behaviour_name == "Move Track":
            adapted_sequence["MoveSetting"] = adapt_move_track(track, action_name, owner_id)

        elif track_behaviour_name == "UpdateParameter Track":
            adapted_sequence["UpdateParameterSetting"] = adapt_update_parameter_track(track, action_name, owner_id)

    ResourceSet = collect_resources(sequence_timeline)

    if ResourceSet:
        resources = {
            "id": owner_id,
            "values": list(ResourceSet.values())
        }

        adapted_sequence["ResourceList"] = resources

    if base_attack_info != {} and adapted_sequence["AttackSetting"] != {}:
        adapted_sequence["AttackSetting"]["baseInfo"] = base_attack_info

    return adapted_sequence


def group_character_sequence_files_by_sequence_name(character_sequence_folder):
    sequence_file_by_sequence_name = {}

    sequence_file_path_list = Path(character_sequence_folder).rglob("*.ab")
    for asset_bundle_path in sequence_file_path_list:
        file_name = asset_bundle_path.name
        file_action_name = file_name[:file_name.rfind("_")]

        sequence_file_by_sequence_name[file_action_name] = asset_bundle_path

    return sequence_file_by_sequence_name


def adapt_character_sequences(extracted_setting_folder, character_player_folder):
    sequence_master_data = []

    sequence_setting_files = Path(extracted_setting_folder).rglob("*.json")

    for sequence_setting_path in sequence_setting_files:
        sequence_setting: json

        with open(sequence_setting_path, "r", encoding="UTF-8") as f:
            sequence_setting = json.load(f)

        character_id = sequence_setting["owner_id"]
        # print("Character ID", character_id)

        character_sequences = {
            "AttackSetting": [],
            "MoveSetting": [],
            "UpdateParameterSetting": [],
            "ResourceList": []   # What does he even do?
        }

        # Regular moves (attacks, dodging)
        character_sequence_folder = character_player_folder / character_id / "sequences"
        asset_bundle_by_sequence_name_dict = group_character_sequence_files_by_sequence_name(character_sequence_folder)

        for sequence_reference in sequence_setting["keyAndSequences"]:
            sequence_name = sequence_reference["path"]
            sequence_timeline_PathID = sequence_reference["sequence"]["m_PathID"]

            # Load sequence AssetBundle by sequenceName
            asset_bundle_path = asset_bundle_by_sequence_name_dict[sequence_name.lower()]
            sequence_bundle_env = UnityPy.load(str(asset_bundle_path))
            # print(sequence_name, asset_bundle_path)

            # print(character_id)
            sequence_timeline = get_sequence_timeline_data(sequence_bundle_env, sequence_timeline_PathID,
                                                           sequence_name, character_id)

            adapted_sequence = adapt_sequence_timeline(sequence_timeline, character_id)

            for key, value in adapted_sequence.items():
                if value:
                    character_sequences[key].append(value)

        # Mystic Artes
        # "characters/player/{char_id}/specialskill/{skill_folder_name}/"
        character_special_skill_folder = character_player_folder / character_id / "specialskill"
        special_skill_bundle_path_list = Path(character_special_skill_folder).rglob("*/specialskill@*.ab")

        for special_skill_bundle_path in special_skill_bundle_path_list:
            special_skill_bundle_data = UnityPy.load(str(special_skill_bundle_path))

            skill_folder_name = special_skill_bundle_path.parent.name
            skill_name = "SpecialSkill@" + str(skill_folder_name)
            # print(skill_folder_name)

            # print("SpecialSkill@" + str(skill_folder_name))
            sequence_timeline = get_sequence_timeline_data(special_skill_bundle_data, "",
                                                           skill_name, character_id)

            adapted_sequence = adapt_sequence_timeline(sequence_timeline, character_id)

            for key, value in adapted_sequence.items():
                if value:
                    character_sequences[key].append(value)

        # Regular spells

        for setting_key, value_list in character_sequences.items():
            if value_list:
                setting = {
                    "CharacterId": character_id,
                    "Category": setting_key,
                    "Data": serialize_setting(setting_key, character_id, value_list)
                }

                sequence_master_data.append(setting)

    return sequence_master_data


def adapt_enemy_sequence(extracted_setting_folder, animation_folder):
    sequence_master_data = []

    enemy_animation_files = sorted(Path(animation_folder).rglob("*.ab"))

    # Enemy animation files have all sequences for an enemy group
    for animation_asset_bundle_path in enemy_animation_files:
        animation_asset_bundle_path = str(animation_asset_bundle_path)

        animation_data = UnityPy.load(animation_asset_bundle_path)

        # Load correct SequenceSetting file
        # ../em0001_slgdjg.ab -> em0001
        enemy_group_name = animation_asset_bundle_path[len(str(animation_folder)) + 1:
                                                       animation_asset_bundle_path.rfind("_")]
        sequence_file_path = extracted_setting_folder / (enemy_group_name + ".json")

        enemy_group_sequence_data: json

        with open(sequence_file_path, "r", encoding="UTF-8") as f:
            enemy_group_sequence_data = json.load(f)

        # Extract and adapt action data
        for enemy_id, sequence_setting in enemy_group_sequence_data.items():

            enemy_sequences = {
                "AttackSetting": [],
                "MoveSetting": [],
                "UpdateParameterSetting": [],
                "ResourceList": []  # What does he even do?
            }

            for sequence_reference in sequence_setting["keyAndSequences"]:
                sequence_name = sequence_reference["path"]
                sequence_timeline_PathID = sequence_reference["sequence"]["m_PathID"]

                sequence_timeline = get_sequence_timeline_data(animation_data, sequence_timeline_PathID,
                                                               sequence_name, enemy_id)

                if sequence_timeline:
                    adapted_sequence = adapt_sequence_timeline(sequence_timeline, enemy_id)

                    for key, value in adapted_sequence.items():
                        if value:
                            enemy_sequences[key].append(value)

            for setting_key, value_list in enemy_sequences.items():
                if value_list:
                    setting = {
                        "EnemyId": enemy_id,
                        "Category": setting_key,
                        "Data": serialize_setting(setting_key, enemy_id, value_list)
                    }

                    sequence_master_data.append(setting)

    return sequence_master_data


def serialize_setting(category, owner, values):
    if category == 'ResourceList':
        resources = {(r['type'], r['value']): r for value in values for r in value['values']}
        values = {'id': owner, 'values': list(resources.values())}
    return json.dumps({category: values})
