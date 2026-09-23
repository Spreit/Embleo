import os
import json

from .scenario.checkpoint import adapt_debug_scenario_checkpoint
from .scenario.arrival import adapt_debug_scenario_arrival
from .scenario.kill import adapt_debug_scenario_kill
from .scenario.talk import adapt_debug_scenario_talk
from .scenario.gimmick import adapt_debug_scenario_gimmick
from .scenario.demo import adapt_debug_scenario_demo
from .scenario.edit_party import adapt_debug_scenario_party
from .scenario.script import adapt_debug_scenario_script
from .scenario.party_flag import adapt_debug_scenario_party_flag
from .scenario.party_param import adapt_debug_scenario_party_param
from .scenario.route_fork import adapt_debug_scenario_route_fork
from .scenario.route_merge import adapt_debug_scenario_route_merge
from .scenario.timer import adapt_debug_scenario_timer
from .scenario.enemy_param import adapt_debug_scenario_enemy_param
from .scenario.route_check import adapt_debug_scenario_route_check
from .scenario.player_actions import adapt_debug_scenario_player_actions
from .scenario.breakable_action import adapt_debug_scenario_breakable_action
from .scenario.mini_game import adapt_debug_scenario_minigame
'''
Adapts debug scenario file by splitting it into separate files and reassigning variables.
'''

"""
TODO

Figure out Route Merge/Fork/Check system 
"""


def adapt_debug_scenario_wtalk(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressArrival"]

    adapted_entry = {
        "ProgressArrivalId": scenario_id,
        "LayoutPointId": condition_entry["PointId"],
        "Event": {}
    }

    adapted_entry["Event"] = {
        "Flag": condition_entry["Flag"],
        "TriggerType": 1,  # Where do I get this?
        # "ActionType": condition_progress["ActionType"],
        "ScriptPath": condition_entry["ScriptPath"],
        "Param": "",
        "Drop": {
            "Id": condition_entry["EventDropInfo"]["ID"]
        }
    }

    return adapted_entry


progress_type_function_dict = {
    "0": "Unknown",
    "1": adapt_debug_scenario_checkpoint,
    "2": adapt_debug_scenario_arrival,
    "3": adapt_debug_scenario_kill,
    "4": adapt_debug_scenario_talk,
    "5": adapt_debug_scenario_gimmick,
    "6": adapt_debug_scenario_demo,
    "7": adapt_debug_scenario_party,
    "8": adapt_debug_scenario_script,
    "9": adapt_debug_scenario_party_flag,
    "10": adapt_debug_scenario_party_param,
    "11": adapt_debug_scenario_route_fork,
    "12": adapt_debug_scenario_route_merge,
    "13": "Timers",
    "14": adapt_debug_scenario_enemy_param,
    "15": "RouteChecks",
    "16": "PlayerActions",
    "17": adapt_debug_scenario_breakable_action,
    "18": adapt_debug_scenario_minigame,

    "1000": adapt_debug_scenario_arrival,  # WTalk (ArrivalPoint)
    "1001": adapt_debug_scenario_checkpoint,  # RouteStart (checkpoint)
    "1002": adapt_debug_scenario_checkpoint,  # RouteEnd (checkpoint)
    "1003": "",
    "1004": "",

    "99998": "",
    "99999": ""
}


def adapt_debug_scenario_entries(debug_scenario_data):
    adapted_scenario_data = []

    # Iterate through all entries
    for debug_entry in debug_scenario_data["Datas"]:
        scenario_id = debug_entry["Id"]  # String, not number
        scenario_no = debug_entry["ScenarioNo"]
        debug_condition = debug_entry["Condition"]
        ProgressType = debug_condition["ProgressType"]

        adapted_scenario_entry = {
            "Id": scenario_id,
            "ScenarioNo": scenario_no,  # Leo's Ep.2 uses an id with "(c)", so this is needed
            "ProgressType": ProgressType,
            "Progress": {}
        }
        # Are ProgressType past that need to be adapted?


        # WTalk
        if ProgressType == 1000:
            ProgressType = 2
            adapted_scenario_entry["ProgressType"] = 2

        # RouteStart
        if ProgressType == 1001:
            ProgressType = 1
            adapted_scenario_entry["ProgressType"] = 1

        # RouteEnd
        if ProgressType == 1002:
            ProgressType = 1
            adapted_scenario_entry["ProgressType"] = 1

        if ProgressType > 18:
            continue
            pass

        # TimerStart
        if ProgressType == 1003:
            continue

        # TimerEnd
        if ProgressType == 1004:
            continue

        # EventSkitEnd
        if ProgressType == 99998:
            pass

        # EpisodeEnd
        if ProgressType == 99999:
            pass

        adapt_function = progress_type_function_dict[str(ProgressType)]

        try:
            adapted_scenario_entry["Progress"] = adapt_function(debug_condition, scenario_id)
        except:
            raise ValueError("Adapt function {} not implemented".format(adapt_function))

        adapted_scenario_data.append(adapted_scenario_entry)

        '''
        # Checkpoint also sets PartyParam
        if ProgressType == 1:
            adapted_scenario_entry = {
                "Id": scenario_id,
                "ProgressType": 10,
                "Progress": {}
            }
            adapted_scenario_entry["Progress"] = adapt_debug_scenario_party_param(debug_condition, scenario_id)
            adapted_scenario_data.append(adapted_scenario_entry)
        '''

    return adapted_scenario_data


def adapt_debug_scenario_file(scenario_file_path) -> json:
    # Load scenario file
    debug_scenario_data: json
    with open(scenario_file_path, "r", encoding="utf-8") as file:
        debug_scenario_data = json.load(file)

    adapted_scenario_file = adapt_debug_scenario_entries(debug_scenario_data)

    # Save the result
    # print(adapted_scenario_file)

    return adapted_scenario_file


progress_type_dict = {
    "0": "Unknown",
    "1": "CheckPoints",
    "2": "ArrivalPoints",
    "3": "Kills",
    "4": "Talks",
    "5": "Gimmicks",
    "6": "Demos",
    "7": "EditParties",
    "8": "Scripts",
    "9": "PartyFlags",
    "10": "PartyParams",
    "11": "RouteForks",
    "12": "RouteMerges",
    "13": "Timers",
    "14": "EnemyParams",
    "15": "RouteChecks",
    "16": "PlayerActions",
    "17": "BreakableActions",
    "18": "MiniGames",
}


def split_scenario_into_scenario_group(adapted_scenario_data):
    ScenarioGroup = {
        "CheckPoints": [],
        "Kills": [],
        "ArrivalPoints": [],
        "Talks": [],
        "Gimmicks": [],
        "Demos": [],
        "EditParties": [],
        "Scripts": [],
        "PartyParams": [],
        "PartyFlags": [],
        "RouteMerges": [],
        "RouteForks": [],
        "RouteChecks": [],
        "Timers": [],
        "EnemyParams": [],
        "PlayerActions": [],
        "BreakableActions": [],
        "MiniGames": []
    }

    for entry in adapted_scenario_data:
        ProgressType = entry["ProgressType"]

        scenario_group_name = progress_type_dict[str(ProgressType)]

        ScenarioGroup[scenario_group_name].append(entry["Progress"])

    return ScenarioGroup


def batch_adapt_scenario_folder(debug_scenario_folder, output_path):
    debug_scenario_list = os.listdir(debug_scenario_folder)

    print("Converting Scenario files")

    for debug_scenario_file_name in debug_scenario_list:

        # Skip .cvs files
        if ".json" not in debug_scenario_file_name:
            continue

        debug_scenario_file_path = os.path.join(debug_scenario_folder, debug_scenario_file_name)

        file_name_without_extension = debug_scenario_file_name[:- len(".json")]
        # print("Converting", file_name_without_extension)

        adapted_scenario = adapt_debug_scenario_file(debug_scenario_file_path)

        # Scenario
        adapted_scenario_output_path = os.path.join(output_path, file_name_without_extension + ".json")

        # make sure that the dir of that path exists
        os.makedirs(os.path.dirname(adapted_scenario_output_path), exist_ok=True)

        with open(adapted_scenario_output_path, "w", encoding="utf-8") as of:
            json.dump(adapted_scenario, of, ensure_ascii=False, indent=4)

        # print("Saved ", adapted_scenario_output_path)

        # Scenario Group (grouped scenario, it is how the scenario is sent to the server)
        '''
        
        adapted_scenario_group = split_scenario_into_scenario_group(adapted_scenario)
        adapted_scenario_group_output_path = os.path.join(output_path, file_name_without_extension + " scenario group.json")
        with open(adapted_scenario_group_output_path, "w", encoding="utf-8") as of:
            json.dump(adapted_scenario_group, of, ensure_ascii=False, indent=4)
        print("Saved ", adapted_scenario_group_output_path)
        
        
        '''
