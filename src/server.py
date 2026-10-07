# server.py
#
# Generic Flask server that:
#	- Maps any request path under / to offline_responses/<path>.json or <path>.msgpack
#	- If .json exists: loads JSON and encodes it as MessagePack
#	- If .msgpack exists: returns the raw MessagePack bytes
#	- Content-Type is set to a MessagePack MIME type
#
# Example mappings:
#	/api/game/provision	 -> offline_responses/api/game/provision.json (or .msgpack)
#	/api/user/register	 -> offline_responses/api/user/register.json (or .msgpack)
#	/api/user/login	  -> offline_responses/api/user/login.json (or .msgpack)
#
# Runs on port 5001.

import datetime
import json
import os
import secrets
# import sqlite3
import time
import urllib
# import logging
from pathlib import Path

import msgpack
from flask import Flask, Response, g, has_request_context, request, url_for

from accounts import AccountError, AccountStore, decode_icon, default_saves, save_key
from profiles import add_all_emblems, noble_dates, utc_date

from scripts.adapt.adapt_debug_episode_data import fill_episode_layout_group_by_episode_id

# from server_scripts.challenge_mission.challenge_mission import challenge_mission

DISABLE_LEVELUPCAMP = True
DISABLE_EVENTS = True
DISABLE_GACHA = True
DISABLE_SHOP = True
DISABLE_CHALLENGE_MISSIONS = True

DISABLE_SCENARIOS = False

SKIP_BATTLES = True
SKIP_VIDEOS = False
SKIP_ROUTE_FORK_MERGE = False

FAKE_CHECKPOINT_PATH = "./checkpoint.txt"


'''
logging.basicConfig(
	filename='app.log',		 # The name of the log file
	level=logging.INFO,		 # Minimum logging level to record
	format='%(asctime)s - %(levelname)s - %(message)s', # Format of log entries
	filemode='a'			 # 'a' (append) to add new logs (default), 'w' (write) to overwrite each run
)
'''

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
RESP_DIR = BASE_DIR / "offline_responses"

app.config["ACCOUNT_DB"] = os.environ.get(
	"EMBLEO_ACCOUNT_DB", str(BASE_DIR / "data/user/top/accounts.sqlite3"))
app.config["ACCOUNT_DEFAULTS"] = default_saves
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024
app.config["ONLINE_TIMEOUT_SECONDS"] = 300

# These constructors explicitly disable authentication in the original client.
PUBLIC_API_PATHS = frozenset({
	"/api/game/heartbeat", "/api/game/provision", "/api/log/anonymous-action",
	"/api/privacy-policy/get-terms-url", "/api/server-message/anonymous-list",
	"/api/user/get-bnid-migration-info", "/api/user/bnid-migration",
	"/api/user/get-migration-info", "/api/user/login-migration",
})


@app.before_request
def resolve_account():
	if not request.path.startswith("/api/"):
		return
	if request.path in PUBLIC_API_PATHS:
		return
	header = request.headers.get("Authorization", "")
	token = header[7:] if header.startswith("Bearer ") else ""
	if not token and request.path != "/api/user/register":
		return account_error_response("Account login required.", 401)
	g.account_store = AccountStore(app.config["ACCOUNT_DB"])
	g.account_id = g.account_store.authenticate(token) if token else None
	if token and not g.account_id:
		return account_error_response("Invalid account token.", 401)


@app.after_request
def finish_account_request(response):
	store = getattr(g, "account_store", None)
	if store:
		if response.status_code < 400:
			if getattr(g, "account_id", None):
				now = int(time.time())
				if request.path in ("/api/user/login", "/api/user/register"):
					# An authenticated register retry does not create a new login.
					if request.path.endswith("/login") or getattr(g, "issued_token", None):
						store.record_login(g.account_id, now, request.path.rsplit("/", 1)[-1])
				store.record_activity(g.account_id, now)
			store.connection.commit()
		else:
			store.connection.rollback()
		if getattr(g, "issued_token", None) and response.status_code < 400:
			response.headers["Authorization"] = "Bearer " + g.issued_token
	if request.path.startswith("/api/") and response.status_code < 400:
		response.content_type = "application/x-msgpack"
	if getattr(g, "account_id", None):
		response.headers["Cache-Control"] = "no-store"
	return response


@app.teardown_request
def close_account_request(error):
	store = getattr(g, "account_store", None)
	if store:
		store.close()


def account_error_response(message, status=400):
	return Response(msgpack.packb({"error": message}, use_bin_type=True),
		status=status, content_type="application/x-msgpack")


@app.errorhandler(AccountError)
def handle_account_error(error):
	return account_error_response(str(error))


def request_object():
	try:
		value = msgpack.unpackb(request.data, raw=False)
	except (ValueError, TypeError, msgpack.UnpackException) as error:
		raise AccountError("Invalid MessagePack request.") from error
	if not isinstance(value, dict):
		raise AccountError("Request must be an object.")
	return value


def current_account_save(path):
	key = save_key(path)
	if key is not None:
		if not has_request_context() or not getattr(g, "account_id", None):
			raise AccountError("Account login required.")
		return g.account_store, g.account_id, key
	return None

MSGPACK_CONTENT_TYPE = "application/x-msgpack"

# app.register_blueprint(challenge_mission, url_prefix="/api/challenge-mission/")

time_variable = time.time()


def resolve_response_path(req_path: str):
	"""
	Given a request path like '/api/user/login', return:
	  - JSON path:	 offline_responses/api/user/login.json
	  - MsgPack path:offline_responses/api/user/login.msgpack
	in that order of preference.
	"""

	# Strip leading slash
	rel = req_path.lstrip("/")
	if not rel:
		return None, None

	json_path = (RESP_DIR / f"{rel}.json").resolve()
	msgpack_path = (RESP_DIR / f"{rel}.msgpack").resolve()
	if not json_path.is_relative_to(RESP_DIR) or not msgpack_path.is_relative_to(RESP_DIR):
		raise AccountError("Invalid response path.")
	return json_path, msgpack_path


def load_for_request(req_path: str) -> bytes:
	"""
	Load the appropriate response for req_path:
	  - If <path>.json exists: load JSON and convert to MessagePack
	  - Else if <path>.msgpack exists: return raw bytes
	  - Else: 404
	"""
	json_path, msgpack_path = resolve_response_path(req_path)
	if json_path and json_path.is_file():
		with json_path.open("r", encoding="utf-8") as f:
			data = json.load(f)
		return msgpack.packb(data, use_bin_type=True)

	if msgpack_path and msgpack_path.is_file():
		return msgpack_path.read_bytes()

	else:
		return msgpack.packb("{}", use_bin_type=True)


def does_file_exist(path):
	account = current_account_save(path)
	if account:
		store, account_id, key = account
		return store.exists(account_id, key)
	if os.path.isfile(path):
		return True

	return False


def load_json(path):
	account = current_account_save(path)
	if account:
		store, account_id, key = account
		value = store.read(account_id, key)
		if key == "UserParameter.json":
			value["NobleStartAtUnix"], value["NobleEndAtUnix"] = noble_dates()
			value.update(store.relationship_counts(account_id))
		return value
	path = Path(path)
	if not path.is_absolute():
		path = BASE_DIR / path
	with open(path, "r", encoding='utf-8') as f:
		return json.load(f)


def save_json(path, data):
	account = current_account_save(path)
	if account:
		store, account_id, key = account
		store.write(account_id, key, data)
		return
	with open(path, "w", encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=4)


def pack_json_response(json_data):
	return msgpack.packb(json_data, use_bin_type=True)


def parse_query_params(request_url):
	# 1. Parse the URL to get the query component
	parsed_url = urllib.parse.urlparse(request_url)
	# 2. Parse the query string component
	query_params = urllib.parse.parse_qs(parsed_url.query)

	return query_params


def SerVec2toVec2(SerializableVector2):
	vector_2 = [
		SerializableVector2["x"],
		SerializableVector2["y"]
	]

	return vector_2


def SerVec3toVec3(SerializableVector3):
	vector_3 = [
		SerializableVector3["x"],
		SerializableVector3["y"],
		SerializableVector3["z"]
	]

	return vector_3


@app.route("/api/game/provision", methods=["GET", "POST"])
def provision():
	provision_data = load_json("./offline_responses/api/game/provision.json")

	with open("./asset_server_link.txt", "r") as f:
		asset_server_url = f.readline()

		provision_data["assetUrl"] = asset_server_url

	# current_time = time.time()
	# current_datetime = datetime.datetime.fromtimestamp(current_time, datetime.UTC)

	# provision_data["serverTime"] = str(datetime)

	return pack_json_response(provision_data)


########################
#			GACHA
########################
"""
For each pulled item

Roll for rarity
5☆ -  5%
4☆ - 30%
3☆ - 65%

Roll for random item in that rarity
	TODO Rate Up have higher chance
	- Sort out prize pool by rarity
	- secret.choice() a random item
	
	Handle a case where a rarity is not present

"""


def roll_rarity():
	five_star_chance = 5
	four_star_chance = 30

	chance_number = secrets.randbelow(100) + 1	# Add 1 to put it into 1-100 range, instead of 0-99

	if chance_number <= five_star_chance:
		return 5
	elif five_star_chance < chance_number <= four_star_chance:
		return 4
	elif chance_number > four_star_chance:
		return 3


def roll_equipment_item(single_rarity_equipment_list):
	return secrets.choice(single_rarity_equipment_list)


def sort_gacha_prize_list_by_rarity(prize_list):
	sorted_prize_list = {
		"5": [],
		"4": [],
		"3": []
	}

	for entry in prize_list:
		rarity = entry["Rarity"]
		sorted_prize_list[str(rarity)].append(entry)

	return sorted_prize_list


def gacha_get_draw_result(pull_amount, sorted_rarity_prize_list):
	gacha_result = []

	for i in range(pull_amount):
		rarity_roll = roll_rarity()
		equipment_item = roll_equipment_item(sorted_rarity_prize_list[str(rarity_roll)])
		equipment_id = equipment_item["ItemId"]

		gacha_result.append({"ItemId": equipment_id})

	return gacha_result


def gacha_find_banner(gacha_master, gacha_base_id):
	for gacha in gacha_master:
		if gacha["GachaBaseId"] == gacha_base_id:
			return gacha


user_equipment_example = {
	"EquipmentId": "pl001_04_001",
	"Category": 1,
	"Level": 1,
	"Exp": 1,
	"UpdatedAt": 0,
	"SpLevel": 1,
	"SpNext": 5,
	"CreatedAt": 0
}


def is_equipment_id_in_user_equipment(equipment_id, user_equipment):
	return any(equipment_id in i for i in user_equipment)


@app.route("/api/gacha/draw", methods=["GET", "POST"])
def gacha_draw():
	draw_request_data = msgpack.unpackb(request.data)

	request_gacha_id = draw_request_data["gachaId"]

	gacha_draw_result = {
		"GachaId": request_gacha_id,
		"Gacha": [],
		# "GachaTicket": [],
		"HcBalance": {},
		"OrderdIds": [],
		"Equipment": [],
		"Character": [],
		"Result": []
		# "Mission": [],
		# "MissionMaster": []
	}

	# gacha_master = load_json("./data/masterdata/GachaMasterData generated.json")

	# Update banner retrieval time in gacha master
	for entry in gacha_master:
		current_time = time.time()
		entry["ContentsOrderDate"] = int(current_time)

	# Send current banners
	# Implement removing Daily banner
	gacha_draw_result["Gacha"] = gacha_master

	# _single or _ten
	gacha_base_id = request_gacha_id[:request_gacha_id.rfind("_")]
	pull_count: int

	current_banner = gacha_find_banner(gacha_master, gacha_base_id)

	for body in current_banner["Bodies"]:
		if body["GachaId"] == request_gacha_id:
			pull_count = body["EjectionCount"]
			break

	# Implement currency subtraction
	gacha_draw_result["HcBalance"] = load_json("./data/user/HcBalance.json")

	# Pulling gacha items
	sorted_rarity_prize_list = sort_gacha_prize_list_by_rarity(current_banner["Prizes"])
	gacha_draw_result["Result"] = gacha_get_draw_result(pull_count, sorted_rarity_prize_list)

	# Implement upgrades
	# Check if item_id is in the user_equipment
	# If it's present, increment the level by 1
	# If it's not - add the item

	equipment_master = load_json("./data/masterdata/EquipmentMasterData.json")
	user_equipment = load_json("./data/user/UserEquipment.json")

	for entry in gacha_draw_result["Result"]:
		item_id = entry["ItemId"]

		# Add equipment piece if it's not in response
		new_equipment = dict.copy(user_equipment_example)

		new_equipment["EquipmentId"] = item_id

		if "wp" in item_id:
			new_equipment["Category"] = 2

		if "acc" in item_id:
			new_equipment["Category"] = 3

		if new_equipment not in gacha_draw_result["Equipment"]:
			gacha_draw_result["Equipment"].append(new_equipment)

	# gacha_draw_result["Equipment"] = user_equipment
	# gacha_draw_result["Character"] = load_json("./data/user/UserCharacter.json")

	return pack_json_response(gacha_draw_result)


########################
#			MARKET
########################

@app.route("/api/cooking/market-buy", methods=["GET", "POST"])
def market_buy():
	# {"carts": [{"id": "ing040", "amount": 5, "itemId": "ing040", "price": 199}], "gold": 10000, "total": 995}

	cart_json = msgpack.unpackb(request.data)

	bought = {}

	for item in cart_json["carts"]:
		bought[item["itemId"]] = item["amount"]

	for item in user_items_json_data:
		if item["ItemId"] in bought:
			item["Count"] += bought[item["itemId"]]

	return pack_json_response({})


@app.route("/api/cooking/market-goods", methods=["GET", "POST"])
def market_list():
	market_goods = {
		"Goods": load_json("./data/food/market_goods.json")
	}

	return pack_json_response(market_goods)


########################
#			EPISODE
########################


@app.route("/api/episode/list", methods=["GET", "POST"])
def episode_list():
	episode_data = {
		"episodes": load_json("./data/masterdata/EpisodeMasterData.json"),
		"episodeUsers": load_json("./data/user/UserEpisode.json")
	}

	return pack_json_response(episode_data)


episode_master_data_path_format = "./data/masterdata/episode/{0}/"

# Use unadapted debug data for now
episode_master_data_path_format = "./data/extract/masterdatadebug/episode/{0}/"

def get_episode_gimmick_id_list(episode_id):
	episode_gimmick_id_list = []

	gimmick_file_path = episode_master_data_path_format.format(episode_id) + "EpisodeGimmickMasterDataObject.json"
	if os.path.isfile(gimmick_file_path):
		gimmick_data = load_json(gimmick_file_path)

		for entry in gimmick_data["Datas"]:
			gimmick_id = entry["_id"]
			episode_gimmick_id_list.append(gimmick_id)

	return episode_gimmick_id_list


def get_all_episode_scenario_gimmicks(episode_id):
	episode_scenario_gimmicks = []

	scenario_file_path = "./data/masterdata/scenario/{0}.json".format(episode_id)
	if os.path.isfile(scenario_file_path):
		scenario_data = load_json(scenario_file_path)

		for entry in scenario_data:
			if entry["ProgressType"] == 5:
				episode_scenario_gimmicks.extend(entry["Progress"]["Gimmicks"])

	return episode_scenario_gimmicks


# Don't turn into a list yet, because there might be progress types past that
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


def fill_scenario_group_from_adapted_scenario(episode_id):
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

	adapted_episode_scenario = load_json("./data/masterdata/scenario/{0}.json".format(episode_id))

	for entry in adapted_episode_scenario:
		ProgressType = entry["ProgressType"]

		if ProgressType > 100:
			continue

		scenario_group_name = progress_type_dict[str(ProgressType)]

		if scenario_group_name == "CheckPoints":
			entry["Progress"][
				"RequestSave"] = True  # MUST be true. Checkpoints that don't request save will softlock the game.

		# Disable story fights
		if SKIP_BATTLES:
			if scenario_group_name == "Kills":
				continue

			if scenario_group_name == "EnemyParams":
				continue

		if SKIP_VIDEOS:
			if scenario_group_name == "Demos":
				continue

		if SKIP_ROUTE_FORK_MERGE:
			if scenario_group_name == "RouteMerges":
				continue
			if scenario_group_name == "RouteForks":
				continue

		ScenarioGroup[scenario_group_name].append(entry["Progress"])

	return ScenarioGroup


def fill_episode_scenario_group_by_episode_id(episode_id):
	episode_scenario_group_master_data = load_json(
		"./data/masterdata/adapted scenario/{0} scenario group.json".format(episode_id))

	gimmick_id_list = get_episode_gimmick_id_list(episode_id)

	# Disabling specific parts for testing
	# episode_scenario_group_master_data["CheckPoints"] = []
	# episode_scenario_group_master_data["Kills"] = []

	# Remove debug gimmicks, since they softlock the game
	cleared_gimmick_list = []

	gimmicks = episode_scenario_group_master_data["Gimmicks"]

	for gimmick_entry_list in gimmicks:
		cleared_list_entry = {
			"ProgressGimmickId": gimmick_entry_list["ProgressGimmickId"],
			"Gimmicks": []
		}

		for gimmick in gimmick_entry_list["Gimmicks"]:
			gimmick_id = gimmick["GimmickId"]

			if gimmick_id in gimmick_id_list:
				cleared_list_entry["Gimmicks"].append(gimmick)

		if cleared_list_entry["Gimmicks"] != []:
			cleared_gimmick_list.append(cleared_list_entry)

		episode_scenario_group_master_data["Gimmicks"] = cleared_gimmick_list

	return episode_scenario_group_master_data


def fill_scenario_list_from_scenario_file(episode_id):
	scenarios = []

	# Skip gimmick with IDs that don't appear in EpisodeGimmickMasterDataObject

	gimmick_id_list = get_episode_gimmick_id_list(episode_id)

	episode_scenario_master_data = load_json("./data/masterdata/scenario/{0}.json".format(episode_id))

	for entry in episode_scenario_master_data["Datas"]:
		preload_entry = {
			"EpisodeScenarioId": entry["Id"],
			"ScenarioNo": entry["ScenarioNo"],

			"ProgressType": entry["Condition"]["ProgressType"],
			"ProgressId": entry["Id"]
		}

		if entry["Condition"]["ProgressType"] == 1:
			pass

		if entry["Condition"]["ProgressType"] == 3:
			pass

		# Skip gimmicks without AP_
		if entry["Condition"]["ProgressType"] == 5 and False:
			ap_in_entry = False
			for gimmick in entry["Condition"]["ProgressGimmick"]["GimmickOperations"]:
				# if "AP_" in gimmick["GimmickId"]:
				if gimmick["GimmickId"] in gimmick_id_list:
					ap_in_entry = True
					break

			if not ap_in_entry:
				pass
				continue

		# continue

		# Arrival
		if entry["Condition"]["ProgressType"] >= 1000:
			# continue
			pass

		scenarios.append(dict.copy(preload_entry))

	return scenarios


skip_scenario = []


def fill_scenario_list_from_adapted_scenario(episode_id):
	scenarios = []

	adapted_episode_scenario = load_json("./data/masterdata/scenario/{0}.json".format(episode_id))

	for entry in adapted_episode_scenario:
		new_scenario_entry = {
			"EpisodeScenarioId": entry["Id"],
			"ScenarioNo": entry["ScenarioNo"],

			"ProgressType": entry["ProgressType"],
			"ProgressId": entry["Id"]
		}

		if entry["ProgressType"] in skip_scenario:
			continue

		if SKIP_BATTLES:
			# Kills
			if entry["ProgressType"] == 3:
				continue
			# EnemyParams
			if entry["ProgressType"] == 14:
				continue

		if SKIP_VIDEOS:
			if entry["ProgressType"] == 6:
				continue

		if SKIP_ROUTE_FORK_MERGE:
			if entry["ProgressType"] == 11:
				continue
			if entry["ProgressType"] == 12:
				continue

		if entry["ProgressType"] > 100:
			continue

		scenarios.append(new_scenario_entry)

	return scenarios


def fill_event_drops_by_episode_id(episode_id):
	event_drops = []

	event_drops_path = episode_master_data_path_format.format(episode_id) + "EpisodeEventDropMasterDataObject.json"

	if does_file_exist(event_drops_path):
		debug_drops = load_json(event_drops_path)

		for entry in debug_drops["Datas"]:
			event_drop = {
				"Id": entry["ID"],
				"ScriptPath": entry["_targetRequirements"]
			}

			print(event_drop)

			event_drops.append(event_drop)

	return event_drops


def fill_episode_detail_by_episode_id(episode_id):
	EpisodeDetail = {
		"Scenarios": [],
		"LayoutGroup": {},
		"ScenarioGroup": {},
		"EventDrops": []
	}

	# Fill "Scenarios" list
	# EpisodeDetail["Scenarios"] = fill_scenario_list_from_scenario_file(episode_id)

	# EpisodeDetail["ScenarioGroup"] = fill_episode_scenario_group_by_episode_id(episode_id)

	if not DISABLE_SCENARIOS:
		EpisodeDetail["Scenarios"] = fill_scenario_list_from_adapted_scenario(episode_id)

	EpisodeDetail["LayoutGroup"] = fill_episode_layout_group_by_episode_id(episode_id)
	EpisodeDetail["ScenarioGroup"] = fill_scenario_group_from_adapted_scenario(episode_id)

	# EventDrops can be found in scenario ProgressScript, that give out dishes
	EpisodeDetail["EventDrops"] = fill_event_drops_by_episode_id(episode_id)

	return EpisodeDetail


def fill_enemy_detail_by_episode_id(episode_id):
	enemy_detail = {
		"Enemies": []
	}

	episode_enemy_data = load_json(episode_master_data_path_format.format(episode_id) + "EpisodeEnemyMasterDataObject.json")

	for enemy in episode_enemy_data["Datas"]:
		master_enemy_id = enemy["_individualID"]
		new_entry = {
			"EnemyId": master_enemy_id
		}

		if new_entry not in enemy_detail["Enemies"]:

			if master_enemy_id != "":
				enemy_detail["Enemies"].append(new_entry)

		if len(enemy["_childEnemyData"]["EnemyIds"]) > 0:
			for child_enemy_id in enemy["_childEnemyData"]["EnemyIds"]:
				new_entry = {
					"EnemyId": child_enemy_id
				}

				if new_entry not in enemy_detail["Enemies"]:
					if child_enemy_id != "":
						enemy_detail["Enemies"].append(new_entry)

	# print("Enemy count", len(start_data["EnemyDetail"]["Enemies"]))

	return enemy_detail


def fill_episode_master_group():
	MasterGroup = {
		"characters": [],
		"enemies": [],
		"enemyIndividuals": [],
		"partsStatusInfos": [],
		"items": [],
		"equipments": [],
		"searchMoveArounds": [],

		"characterSequences": [],
		"enemySequences": [],

		"characterLevelStatus": [],
		"characterLevelExp": [],
		"equipmentLevelStatus": [],

		"characterBehaviourTrees": [],
		"enemyBehabiourTrees": [],

		"secretMissions": [],
		"vehicles": [],
		"tutorialGuides": [],

		"equipmentSpLevelExp": [],
		"buff": []
	}

	MasterGroup["characters"] = load_json("./data/masterdata/CharacterMasterData.json")
	MasterGroup["enemies"] = load_json("./data/masterdata/EnemyMasterData.json")

	MasterGroup["enemyIndividuals"] = load_json("./data/masterdata/EnemyIndividualMasterData.json")
	MasterGroup["partsStatusInfos"] = load_json("./data/masterdata/PartsStatusInfo.json")

	MasterGroup["items"] = load_json("./data/masterdata/ItemMasterData.json")
	MasterGroup["equipments"] = load_json("./data/masterdata/EquipmentMasterData.json")

	MasterGroup["characterSequences"] = load_json("./data/masterdata/CharacterSequenceMasterData.json")
	MasterGroup["enemySequences"] = load_json("./data/masterdata/EnemySequenceMasterData.json")

	MasterGroup["characterLevelStatus"] = load_json(
		"./data/masterdata/TemporaryLevelStatusCurveCharacterMasterData.json")
	MasterGroup["equipmentLevelStatus"] = load_json(
		"./data/masterdata/TemporaryLevelStatusCurveEquipmentMasterData.json")

	MasterGroup["vehicles"] = load_json("./data/masterdata/VehicleMasterData.json")

	MasterGroup["buff"] = load_json("./data/masterdata/BuffMasterData.json")

	return MasterGroup


@app.route("/api/episode/preload", methods=["GET", "POST"])
def episode_preload():
	preload_data = load_json("./offline_responses/api/episode/preload.json")

	episode_preload_list = msgpack.unpackb(request.data)

	print(request.data)

	# Fill "details" list
	for episode_id in episode_preload_list["episodeIds"]:
		detail = {
			"episodeId": episode_id,
			"EpisodeDetail": fill_episode_detail_by_episode_id(episode_id)
		}

		preload_data["details"].append(detail)

	'''
	# Fill "characterDetail"
	preload_data["characterDetail"] = fill_episode_character_detail()

	# Fill baseVisual Settings
	for episode_id in episode_preload_list["episodeIds"]:

		episode_scenario_master_data = load_json("./data/masterdata/scenario/{0}.json".format(episode_id))

		for entry in episode_scenario_master_data["Datas"]:

			preload_settings = {
				"ScenarioNo": 0,
				"Ids": []
			}

			party_visual_id_list = entry["Condition"]["ProgressEditParty"]["partyVisualIds"]

			if party_visual_id_list != [] and party_visual_id_list[0] != "":
				preload_settings["ScenarioNo"] = entry["ScenarioNo"]
				preload_settings["Ids"] = party_visual_id_list

				# print(preload_settings)
				preload_data["characterDetail"]["baseVisual"]["settings"].append(preload_settings)
	'''

	preload_data["masterGroup"] = fill_episode_master_group()

	return pack_json_response(preload_data)


def get_episode_character_visual_settings(episode_id):
	visual_settings = []

	# From debug checkpoint
	episode_checkpoint_data = load_json("./data/extract/masterdatadebug/episode/{0}/EpisodeCheckPointMasterDataObject.json".format(episode_id))

	for entry in episode_checkpoint_data["Datas"]:
		visual_setting = {
			"ScenarioNo": entry["_startScenarioNo"],
			"Ids": entry["PartyVisualIds"]
		}

		# print(visual_setting)
		visual_settings.append(visual_setting)

	# Add "fixes" from scenario files?

	return visual_settings


@app.route("/api/episode/start", methods=["GET", "POST"])
def episode_start():
	print("Episode start endpoint")

	# If EpisodeChapterStatus (or simply Status in UserChapter) is set to 1/2/3/4
	# Pressing chapter button will also send chapter ID
	request_data = msgpack.unpackb(request.data)
	print(request_data)

	episode_id = request_data["episodeId"]

	if "chapterId" in request_data:
		chapter_id = request_data["chapterId"]
		print("Chapter ID", chapter_id)

	episode_character_id, _ = episode_id.split("_")

	# Fill episode start data
	start_data = load_json("./offline_responses/api/episode/start.json")

	# Probably can be anything
	start_data["EpisodeToken"] = episode_id

	start_data["CharacterDetail"] = fill_episode_character_detail()
	
	start_data["CharacterDetail"]["baseVisual"]["settings"] = get_episode_character_visual_settings(episode_id)
	
	# Just a list of masterdata ids?
	start_data["EnemyDetail"] = fill_enemy_detail_by_episode_id(episode_id)

	# Fills Scenarios, LayoutGroup, scenarioGroup, eventDrops
	start_data["EpisodeDetail"] = fill_episode_detail_by_episode_id(episode_id)

	# Fake? saving system
	fake_checkpoint_data = {}

	if does_file_exist(FAKE_CHECKPOINT_PATH):
		fake_checkpoint_data = load_json(FAKE_CHECKPOINT_PATH)

	if episode_id in fake_checkpoint_data:
		start_data["EpisodeDetailUser"]["startScenarioNo"] = fake_checkpoint_data[episode_id]

	# EpisodeDetailUser

	start_data["EpisodeDetailUser"]["playCharacters"][0]["characterId"] = episode_character_id
	start_data["EpisodeDetailUser"]["playCharacters"][0]["hp"] = 1000000
	start_data["EpisodeDetailUser"]["playCharacters"][0]["sp"] = 100000

	# MissionDetail
	# Secret Mission Detail from episode master data

	# MasterGroup
	start_data["MasterGroup"] = fill_episode_master_group()

	return pack_json_response(start_data)

@app.route("/api/episode/continue", methods=["GET", "POST"])
def episode_continue():
	print("Episode continue endpoint")

	# Would be very useful if the game sent something other than episode id
	request_data = msgpack.unpackb(request.data)
	print(request_data)

	episode_id = request_data["episodeId"]
	episode_character_id, _ = episode_id.split("_")

	# Fill episode start data
	start_data = load_json("./offline_responses/api/episode/continue.json")

	# Probably can be anything
	start_data["EpisodeToken"] = episode_id

	start_data["CharacterDetail"] = fill_episode_character_detail()

	start_data["CharacterDetail"]["baseVisual"]["settings"] = get_episode_character_visual_settings(episode_id)

	# Just a list of masterdata ids?
	start_data["EnemyDetail"] = fill_enemy_detail_by_episode_id(episode_id)

	# Fills Scenarios, LayoutGroup, scenarioGroup, eventDrops
	start_data["EpisodeDetail"] = fill_episode_detail_by_episode_id(episode_id)

	# EpisodeDetailUser
	start_data["EpisodeDetailUser"]["playCharacters"][0]["characterId"] = episode_character_id
	start_data["EpisodeDetailUser"]["playCharacters"][0]["hp"] = 1000000
	start_data["EpisodeDetailUser"]["playCharacters"][0]["sp"] = 100000

	# Fake? saving system
	fake_checkpoint_data = {}

	if does_file_exist(FAKE_CHECKPOINT_PATH):
		fake_checkpoint_data = load_json(FAKE_CHECKPOINT_PATH)

	if episode_id in fake_checkpoint_data:
		start_data["EpisodeDetailUser"]["startScenarioNo"] = fake_checkpoint_data[episode_id]

	# MasterGroup
	start_data["MasterGroup"] = fill_episode_master_group()

	return pack_json_response(start_data)

@app.route("/api/episode/retire", methods=["GET", "POST"])
def episode_retire():
	request_data = msgpack.unpackb(request.data)

	print(request_data)

	response = {
		"Result": {
			"Parameter": load_json("./data/user/UserParameter.json"),
			"Characters": load_json("./data/user/UserCharacter.json"),
			"Reward": reward_result()
		}
	}

	return pack_json_response(response)


@app.route("/api/training-mission/start", methods=["GET", "POST"])
def level_up_camp_start():
	print("Level Up Camp start endpoint")

	# level up camp id and character id
	request_data = msgpack.unpackb(request.data)
	print(request_data)

	training_mission_id = request_data["trainingMissionId"]
	character_id = request_data["characterId"]

	# Fill episode start data
	start_data = load_json("./offline_responses/api/training-mission/start.json")

	# Probably can be anything
	start_data["MissionToken"] = training_mission_id

	start_data["CharacterDetail"] = fill_episode_character_detail()

	start_data["CharacterDetail"]["baseVisual"] = {
		"settings": [{
			"ScenarioNo": 1,
			"Ids": [
				"pl003_05_001"
			]
		}
		],
		"characters": [{
			"VisualId": "pl003_05_001",
			"CharacterId": "pl003",
			"VisualEquipment": [
				"pl003_05_001",
				"wp001_04_001",
				"",
				"",
				"",
				""
			]
		}
		]
	}

	# Add character setting
	# start_data["CharacterDetail"]["baseVisual"]["setting"] = {
	# "ScenarioNo": 1,
	# "Ids": [character_id + "_04_001"]
	# }

	# EpisodeDetail
	start_data["EpisodeDetail"] = fill_episode_detail_by_episode_id(training_mission_id)

	# EpisodeDetailUser

	start_data["EpisodeDetailUser"] = {
		"status": 0,

		"startScenarioNo": 0,
		"revivalPointId": "",
		"revivalScenarioNo": 0,

		"playUser": {
			"money": 0,
			"fieldCoin": 0,
			"skill": 0,
			"magic": 0,
			"food": 0
		},
		"playCharacters": [{
			"characterId": character_id,
			"hp": 240,
			"sp": 45,
			"level": 1,
			"exp": 0
		}
		],
		"drops": [],
		"secretMission": {
			"Statuses": []
		},
		"acquireStaticItemIds": [],
		"tutorialGuideIds": [],
		"conqueredPoint": 0
	}

	# MissionDetail
	start_data["MissionDetail"] = {
		"TrainingMissionId": "exp_mission_001",
		"Category": 1,
		"LocationId": "IC_VI01",
		"Detail": {
			"TimeLimit": 300,
			"TimerCountType": 1,
			"Finishes": [
				{
					"Type": 0,
					"Flag": 1,
					"Option": ""
				}],
			"Rules": []
		}
	}

	# MasterGroup
	start_data["MasterGroup"] = fill_episode_master_group()

	return pack_json_response(start_data)


def reward_result(episode_id="", scenario_no=""):
	result = {
		"User": load_json("./data/user/User.json"),
		"UserPresents": [],
		"UserParameter": load_json("./data/user/UserParameter.json"),
		"UserItems": load_json("./data/user/UserItems.json"),
		"UserEquipments": load_json("./data/user/UserEquipment.json"),
		"HcBalance": load_json("./data/user/HcBalance.json"),
		"UserTickets": [],
		"UserStampBadge": [],
		"UserCharacters": load_json("./data/user/UserCharacter.json"),
		"UserEventSkits": [],
		"UserPanelMissions": []
	}

	return result


def fake_checkpoint(episode_id, scenarioNo):
	# Temporary measure for saving during episodes

	checkpoint_path = "./checkpoint.txt"

	checkpoint = {}

	if does_file_exist(checkpoint_path):
		checkpoint = load_json(checkpoint_path)

	checkpoint[episode_id] = scenarioNo

	if scenarioNo == 0:
		del checkpoint[episode_id]

	save_json(checkpoint_path, checkpoint)


@app.route("/api/episode/check-point", methods=["GET", "POST"])
def episode_checkpoint():
	request_info = msgpack.unpackb(request.data)
	print(request_info)
	print("Checkpoint")
	print("Episode", request_info["episodeId"])
	print("ScenarioNo", request_info["scenarioNo"])

	fake_checkpoint(request_info["episodeId"], request_info["scenarioNo"])

	# bruh why do you need all of that for a checkpoint???
	checkpoint_response = {
		"Result": {
			"Parameter": {},
			"Characters": [],
			"Reward": {}
		},
		"MasterGroup": {},
		# "IntroductionResult": {}
	}

	# Result
	checkpoint_response["Result"]["Parameter"] = load_json("./data/user/UserParameter.json")
	checkpoint_response["Result"]["Characters"] = load_json("./data/user/UserCharacter.json")

	checkpoint_response["Result"]["Reward"] = reward_result()

	checkpoint_response["MasterGroup"] = fill_episode_master_group()

	'''
	checkpoint_response["IntroductionResult"] = {
		"Finished": True,
		"OpenedEpisodes":[]
	}
	'''

	# Put UserEpisode at continue mode
	user_episode = load_json("./data/user/UserEpisode.json")

	for episode_entry in user_episode:
		if episode_entry["EpisodeId"] == request_info["episodeId"]:
			# Set Continue status
			if episode_entry["Status"] < 32768:
				episode_entry["Status"] += 32768

			break

	save_json("./data/user/UserEpisode.json", user_episode)

	# checkpoint_response = {}

	return pack_json_response(checkpoint_response)


@app.route("/api/episode/reset", methods=["GET", "POST"])
def episode_reset():
	request_info = msgpack.unpackb(request.data)
	print("Deleting save data for", request_info["episodeId"])
	episode_id = request_info["episodeId"]

	reset_response = {
		"EpisodeId": episode_id
	}

	fake_checkpoint(episode_id, 0)

	# Put UserEpisode at continue mode
	user_episode = load_json("./data/user/UserEpisode.json")

	for episode_entry in user_episode:
		if episode_entry["EpisodeId"] == episode_id:
			# Set Continue status
			if episode_entry["Status"] >= 32768:
				episode_entry["Status"] -= 32768

			break

	save_json("./data/user/UserEpisode.json", user_episode)

	return pack_json_response(reset_response)


@app.route("/api/episode/chronology-list", methods=["GET", "POST"])
def chronology_list():
	adventurers_id_list = [
		"pl017",  # "Edouard",
		"pl018",  # "Ana-Maria",
		"pl019",  # "Raoul",
		"pl020",  # "Lydie",
		"pl021"	 # "Charles"
	]

	url = request.url
	# 1. Parse the URL to get the query component
	parsed_url = urllib.parse.urlparse(url)
	# 2. Parse the query string component
	query_params = urllib.parse.parse_qs(parsed_url.query)

	# print(query_params)

	character_id = query_params["characterIds[0]"][0]

	if character_id in adventurers_id_list:
		character_id = "adv"

	chronology_path = "./data/chronology/{0}.json"

	chronology_data = load_json(chronology_path.format(character_id))

	'''
	chronology_data = {
		"Chronologies": [
			{
				"Events": []
			}
		],
		"episodes": [],
		"episodeUsers": []
	}

	# Load chronology table based on character id
	db = sqlite3.connect("./data/chronology.db")
	c = db.cursor()
	c.execute("SELECT * FROM {0}".format(character_id))
	rows = c.fetchall()

	for row in rows:
		base_event = {
			"ChronologyId": row[0],
			"Year": row[1],
			"Order": row[2],
			"EpisodeId": row[3],
			"AdventureNo": row[4]
		}

		chronology_data["Chronologies"][0]["Events"].append(base_event)
	'''

	chronology_data["episodes"] = load_json("./data/masterdata/EpisodeMasterData.json")
	chronology_data["episodeUsers"] = load_json("./data/user/UserEpisode.json")

	return pack_json_response(chronology_data)


def fill_episode_character_detail():
	character_detail = {
		"characters": load_json("./data/masterdata/CharacterMasterData.json"),
		"userCharacters": load_json("./data/user/UserCharacter.json"),
		"userEquipments": load_json("./data/user/UserEquipment.json"),
		"userItems": load_json("./data/user/UserItems.json"),
		"baseVisual": {
			"settings": [],
			"characters": []
		}
	}

	# Better way would be only loading options used by an episode
	character_detail["baseVisual"]["characters"] = load_json(
		"./data/masterdata/EpisodeCharacterVisualMasterData.json")
	
	
	return character_detail


@app.route("/api/secret-mission/start", methods=["GET", "POST"])
def secret_mission_start():
	print("Secret mission start endpoint")
	start_data = load_json("./offline_responses/api/secret-mission/start.json")

	request_data = msgpack.unpackb(request.data)
	print(request_data)

	secret_mission_id = request_data["secretMissionId"]

	# MissionToken
	start_data["MissionToken"] = secret_mission_id

	# CharacterDetail
	character_detail = fill_episode_character_detail()

	character_detail["baseVisual"] = {
		"settings": [{
			"ScenarioNo": 1,
			"Ids": [
				"pl003_05_001"
			]
		}
		],
		"characters": [{
			"VisualId": "pl003_05_001",
			"CharacterId": "pl003",
			"VisualEquipment": [
				"pl003_05_001",
				"wp001_04_001",
				"",
				"",
				"",
				""
			]
		}
		]
	}

	start_data["CharacterDetail"] = character_detail

	episode_scenario_master_data = load_json("./data/masterdata/scenario/{0}.json".format(secret_mission_id))
	for entry in episode_scenario_master_data:

		preload_settings = {
			"ScenarioNo": 0,
			"Ids": []
		}

		party_visual_id_list = entry["Condition"]["ProgressEditParty"]["partyVisualIds"]

		if party_visual_id_list != [] and party_visual_id_list[0] != "":
			preload_settings["ScenarioNo"] = entry["ScenarioNo"]
			preload_settings["Ids"] = party_visual_id_list

			# print(preload_settings)
			# start_data["CharacterDetail"]["baseVisual"]["settings"][0] = preload_settings

			break

	start_data["CharacterDetail"]["baseVisual"]["characters"] = load_json(
		"./data/masterdata/EpisodeCharacterVisualMasterData.json")

	# EpisodeDetail
	start_data["EpisodeDetail"] = fill_episode_detail_by_episode_id(secret_mission_id)

	# EpisodeDetailUser

	# MissionDetail
	# Secret Mission Detail from episode master data
	episode_master_data = load_json("./data/masterdata/EpisodeMasterData.json")
	episode_id = secret_mission_id[:secret_mission_id.rfind("_")]

	for episode in episode_master_data:
		if episode_id == episode["EpisodeId"]:
			for secret_mission in episode["SecretMissions"]:
				if secret_mission["Id"] == secret_mission_id:
					start_data["MissionDetail"] = secret_mission["Detail"]

					print(start_data["MissionDetail"])

	# MasterGroup
	start_data["MasterGroup"] = fill_episode_master_group()

	return pack_json_response(start_data)


@app.route("/api/challenge-mission/start", methods=["GET", "POST"])
def challenge_mission_start():
	print("Challenge mission start endpoint")

	start_data = load_json("./offline_responses/api/challenge-mission/start.json")

	# Character Detail
	start_data["characterDetail"] = fill_episode_character_detail()

	# base visual goes here, but it's preset in the start file

	# EpisodeDetail
	#	Scenarios
	episode_id = "wp001_05_001_cl01"
	episode_scenario_master_data = load_json("./data/masterdata/scenario/{0}.json".format(episode_id))

	start_data["EpisodeDetail"] = fill_episode_detail_by_episode_id(episode_id)

	# episodeDetailUser

	# missionDetail

	# masterGroup
	start_data["MasterGroup"] = fill_episode_master_group(episode_id)

	return pack_json_response(start_data)


@app.route("/api/challenge-mission/list", methods=["GET", "POST"])
def challenge_mission_list():
	if DISABLE_CHALLENGE_MISSIONS:
		return pack_json_response({})

	list_data = load_json("./offline_responses/api/challenge-mission/list.json")

	list_data["MstEquipments"] = load_json("./data/masterdata/EquipmentMasterData.json")

	return pack_json_response(list_data)


@app.route("/", methods=["GET", "POST"])
def root():
	# Optional: simple message or 404
	return "Offline server root. Put files under offline_responses/ matching request paths.\n"


# user_items_json_data = json.load(open("./data/user/UserItems.json", "r"))

unreleased_episodes = [
	"pl005_ep002",
	"pl006_ep002",
	"pl011_ep002",
	"pl012_ep002",
	"pl014_ep002",
	"pl015_ep002",
	"pl020_ep002",
	"pl021_ep002"
]


def top_add_episodes():
	episode_ordered_ids = []

	# All episodes, up to ep.Final
	# not all are playable though
	episode_id_template = "{0}_{1}"
	char_id_template = "pl{:03d}"
	ep_num_template = "ep{:03d}"

	# Add Episodes
	for episode_number in range(1, 3):
		for char_number in range(1, 22):
			char_id = char_id_template.format(char_number)
			ep_num = ep_num_template.format(episode_number)
			episode_id = episode_id_template.format(char_id, ep_num)

			# print(episode_id)

			if episode_id in unreleased_episodes:
				continue

			episode_order = {
				"MasterDataId": episode_id,
				"Type": 0
			}

			episode_ordered_ids.append(dict.copy(episode_order))

		'''
		# Crossroads
		episode_order = {
			"MasterDataId": "mstone_ep00" + str(episode_number),
			"Type": 0
		}
		
		if episode_order not in ordered_ids:
			episode_ordered_ids.append(dict.copy(episode_order))
		'''

	# print(episode_ordered_ids)
	return episode_ordered_ids


def top_add_equipment(ordered_ids):
	equipment_tiles = []

	base_tile = {
		"MasterDataId": "",
		"Type": 0
	}

	user_equipment = load_json("./data/user/UserEquipment.json")

	for entry in user_equipment:

		new_tile = base_tile

		new_tile["MasterDataId"] = entry["EquipmentId"]

		gear_category = entry["Category"]

		tile_type: int

		if gear_category == 1:	# Costume
			tile_type = 7
		elif gear_category == 2:  # Weapon
			tile_type = 6
		elif gear_category == 3:  # Accessory
			tile_type = 8
		elif gear_category == 4:  # Attachment
			tile_type = 9

		new_tile["Type"] = tile_type

		if new_tile not in ordered_ids:
			equipment_tiles.append(dict.copy(new_tile))

	return equipment_tiles


def top_add_characters():
	tiles = []

	char_tile_template = {
		"MasterDataId": "pl001",
		"Type": 1
	}

	for i in range(1, 22):
		char_id = "pl{:03d}".format(i)
		# print(char_id)

		char_tile = char_tile_template
		char_tile["MasterDataId"] = char_id

		tiles.append(dict.copy(char_tile))

	return tiles


@app.route("/api/user/top", methods=["GET", "POST"])
def top():
	top_data = load_json("./offline_responses/api/user/top.json")
	top_data["user"] = load_json("./data/user/User.json")

	# Auto-fill orderdIds

	top_data["orderdIds"].extend(top_add_episodes())
	top_data["orderdIds"].extend(top_add_equipment(top_data["orderdIds"]))
	top_data["orderdIds"].extend(top_add_characters())

	if not DISABLE_LEVELUPCAMP:
		top_data["orderdIds"].append(
			{
				"MasterDataId": "LvUpCamp",
				"Type": 99
			}
		)

	# Curry
	top_data["orderdIds"].append(
		{
			"MasterDataId": "dish_3_01",
			"Type": 5
		}
	)

	# Master episodes and episodeUser are sent to the game independently

	top_data["character"] = load_json("./data/user/UserCharacter.json")
	top_data["equipment"] = load_json("./data/user/UserEquipment.json")
	top_data["item"] = load_json("./data/user/UserItems.json")
	top_data["episodeUsers"] = load_json("./data/user/UserEpisode.json")

	top_data["parameter"] = load_json("./data/user/UserParameter.json")
	top_data["hcBalance"] = load_json("./data/user/HcBalance.json")
	top_data["pieUserSetting"] = load_json("./data/user/PieUserSetting.json")

	top_data["characterMaster"] = load_json("./data/masterdata/CharacterMasterData.json")
	add_all_emblems(top_data, BASE_DIR / "data/extract/manifest.json")
	top_data["equipmentMaster"] = load_json("./data/masterdata/EquipmentMasterData.json")
	top_data["itemMaster"] = load_json("./data/masterdata/ItemMasterData.json")

	top_data["buff"] = load_json("./data/masterdata/BuffMasterData.json")

	top_data["levelStatusCurveChrMaster"] = load_json(
		"./data/masterdata/TemporaryLevelStatusCurveCharacterMasterData.json")
	top_data["levelStatusCurveEquMaster"] = load_json(
		"./data/masterdata/TemporaryLevelStatusCurveEquipmentMasterData.json")

	if DISABLE_SHOP:
		top_data["nobleShop"] = []
	else:
		top_data["nobleShop"] = load_json("./data/shop/NobleShop.json")

	# Gacha
	if not DISABLE_GACHA:
		t = time.time()
		gacha_data = load_json("./data/masterdata/GachaMasterData generated.json")

		for entry in gacha_data:
			entry["ContentsOrderDate"] = int(t)

		top_data["gacha"] = gacha_data

	body = pack_json_response(top_data)
	return Response(body, content_type=MSGPACK_CONTENT_TYPE)


@app.route("/api/user/info", methods=["GET", "POST"])
def api_user_info():
	if request.method == 'GET':
		# print("Headers:", request.headers)
		# print("Data", request.data)
		pass

	json_data = load_json("./offline_responses/api/user/info.json")

	json_data["user"] = load_json("./data/user/User.json")
	json_data["supportUrl"] = f"{public_scheme()}://{request.host}"

	current_time = time.time()
	json_data["serverTime"] = str(datetime.datetime.fromtimestamp(current_time, datetime.UTC))
	json_data["serverTimeRaw"] = int(current_time)
	json_data["serverTimeTSRaw"] = int(current_time)

	# print(json_data)

	body = pack_json_response(json_data)
	return Response(body, content_type=MSGPACK_CONTENT_TYPE)


@app.route("/api/user/character-update", methods=["GET", "POST"])
def api_user_character_update():
	request_decrypted_data = request_object()

	character_update_response_json = load_json("./offline_responses/api/user/character-update.json")

	updates = request_decrypted_data.get("userCharacter")
	characters = load_json("./data/user/UserCharacter.json")
	if not isinstance(updates, list):
		raise AccountError("Invalid character update.")
	by_id = {entry["CharacterId"]: entry for entry in characters}
	updated_ids = []
	for update in updates:
		if not isinstance(update, dict):
			raise AccountError("Invalid character update.")
		character_id = update.get("CharacterId", update.get("characterId"))
		if not isinstance(character_id, str) or character_id not in by_id:
			raise AccountError("Unknown character.")
		# Character-update edits loadouts, not server-owned level/experience.
		entry = by_id[character_id]
		updated_ids.append(character_id)
		for key in ("VisualEquipment", "Costume", "WeaponMain", "WeaponSub",
				"AccessoryMain", "AccessorySub", "CostumeSpell", "WeaponSpell", "Food"):
			request_key = key if key in update else key[0].lower() + key[1:]
			if request_key in update:
				if not isinstance(update[request_key], list) or not all(isinstance(v, str) for v in update[request_key]):
					raise AccountError("Invalid character loadout.")
				entry[key] = update[request_key]
	save_json("./data/user/UserCharacter.json", characters)
	character_update_response_json["UserCharacter"] = [by_id[character_id] for character_id in updated_ids]

	body = pack_json_response(character_update_response_json)  # keep leading slash semantics consistent
	return Response(body, content_type=MSGPACK_CONTENT_TYPE)


@app.route("/api/user/login", methods=["GET", "POST"])
def api_user_login():
	login_data = load_json("./offline_responses/api/user/login.json")
	login_data["user"] = load_json("./data/user/User.json")

	login_data["loginInfo"]["name"] = login_data["user"]["name"]

	body = pack_json_response(login_data)  # keep leading slash semantics consistent
	return Response(body, content_type=MSGPACK_CONTENT_TYPE)


@app.route("/api/user/register", methods=["GET", "POST"])
def api_user_register():
	request_data = request_object()

	response_json = {}

	if not g.account_id:
		g.account_id, g.issued_token = g.account_store.create(
			request_data.get("name"), app.config["ACCOUNT_DEFAULTS"]())
	user_data = load_json("./data/user/User.json")

	response_json["User"] = user_data
	response_json["UserItems"] = load_json("./data/user/UserItems.json")

	body = pack_json_response(response_json)
	return Response(body, content_type=MSGPACK_CONTENT_TYPE)


@app.route("/api/user/change-name", methods=["POST"])
def change_name():
	name = request_object().get("name")
	if not isinstance(name, str) or not 2 <= len(name.strip()) <= 64:
		raise AccountError("Invalid nickname.")
	user = load_json("./data/user/User.json")
	user["name"] = name
	save_json("./data/user/User.json", user)
	return pack_json_response({"User": user})


@app.route("/api/user/change-view-param", methods=["POST"])
def change_view_param():
	data = request_object()
	parameter = load_json("./data/user/UserParameter.json")
	for request_key, save_field in (("word", "Word"),
			("favoriteChrId", "FavoriteChrId"), ("emblemId", "EmblemId")):
		if request_key in data:
			if not isinstance(data[request_key], str) or len(data[request_key]) > 2048:
				raise AccountError("Invalid profile value.")
			parameter[save_field] = data[request_key]
	save_json("./data/user/UserParameter.json", parameter)
	return pack_json_response({"UserParameter": parameter, "OrderdIds": [],
		"Mission": [], "MissionMaster": []})


@app.route("/api/billing/get-product-ids", methods=["GET", "POST"])
def api_billing_get_product_ids():
	response_json = {
		"productIds": []
	}

	if DISABLE_SHOP:
		return pack_json_response(response_json)

	ProductList = load_json("./data/shop/ProductList.json")

	for entry in ProductList:
		response_json.append(entry["ProductId"])

	NobleShop = load_json("./data/shop/NobleShop.json")

	for entry in NobleShop:
		response_json.append(entry["Id"])

	return pack_json_response(response_json)


@app.route("/api/billing/list", methods=["GET", "POST"])
def api_billing_list():
	response_json = {
		"productList": [],
		"pieUserSetting": load_json("./data/user/PieUserSetting.json"),
		"hcBalance": load_json("./data/user/HcBalance.json")
	}

	if DISABLE_SHOP:
		return pack_json_response(response_json)

	response_json["productList"] = load_json("./data/shop/ProductList.json")

	return pack_json_response(response_json)


@app.route("/api/billing/is-buyable", methods=["GET", "POST"])
def api_billing_is_buyable():
	# No paid item is really buyable, since it softlocks the game.
	return pack_json_response({"IsStopped": True, "IsReachedLimitByAge": False,
		"IsTooYoungToPurchase": False, "IsLimited": True})

@app.route("/api/present/list", methods=["GET", "POST"])
def api_present_list():
	user_present_box_path = "./data/user/Presents.json"

	present_list = load_json(user_present_box_path)

	return pack_json_response(present_list)


@app.route("/api/present/history", methods=["GET", "POST"])
def api_present_history():
	present_history = {
		"UserPresents": []
	}

	present_history = load_json("./data/user/Presents.json")

	return pack_json_response(present_history)


@app.route("/api/present/receive", methods=["GET", "POST"])
def api_present_receive():
	print("receive present")
	response = {
		"RewardResult": reward_result(),
		"Mission": [],
		"MissionMaster": [],
		"OrderdIds": [],
		"UserCharacter": load_json("./data/user/UserCharacter.json"),
	}

	presents = load_json("./data/user/Presents.json")

	presents["UserPresents"] = []

	save_json("./data/user/Presents.json", presents)

	# Impelement recieving items

	return pack_json_response(response)


# Calendar
@app.route("/api/login-calendar/calendar", methods=["GET", "POST"])
def login_calendar():
	calendar = {
		"LoginCalendar":
			{
				"LoginBonusPanels": [
					{
						"Date": 0,
						"OpenStatus": 0,
						"Rewards": [
							{
								"Type": 1,
								"Amount": 10,
								"Complements": ""
							}
						],
						"IsToday": 0,
						"TimeZone": 0
					}
				],
				"Events": [],
				"RequiredGold": 100,
				"OffsetSecond": 0,
				"Timezone": 0
			}
	}

	# Where to get event Id from?

	calendar = load_json("./offline_responses/api/login-calendar/calendar.json")

	# calendar["LoginCalendar"]["Events"].append(test_event)
	# calendar["LoginCalendar"]["Events"] = []

	return pack_json_response(calendar)


# Calendar
@app.route("/api/login-calendar/open", methods=["GET", "POST"])
def login_calendar_open_tile():
	open_tile_result = {
		"RewardResult": reward_result(),
		"LoginBonusPanel": {}
	}

	open_tile_result["LoginBonusPanel"] = {
		"Date": 0,
		"OpenStatus": 2,
		"Rewards": [
			{
				"Type": 1,
				"Amount": 10,
				"Complements": "",
			}
		],
		"IsToday": 0,
		"TimeZone": 0
	}

	return pack_json_response(open_tile_result)


@app.route("/api/guild/top", methods=["GET", "POST"])
def guild_top():
	guild_top_response = {
		"UserGuild": {},
		"Guild": {},
		"Members": [],
		"Applications": []
	}

	guild_top_response["UserGuild"] = {
		"Status": 1,  # Member
		"JoinedAt": 0,
		"Exstatus": 0
	}

	guild_top_response["Guild"] = {
		"GuildId": "asdf",
		"ShortGuildId": "asdf",
		"Status": 0,
		"Name": "Lumi",
		"LastAccessAt": 0,
		"Members": [],
		"Officers": [],
		"Level": 0,
		"Exp": 0,
		"Coin": 0,
		"Recruitment": -1,
		"Mood": 1,
		"Cadence": -1,
		"MinimumPower": 0,
		"Description": "Description",
		"Icon": "emblem_em001_001",
		"Title": "Lumi",
		"NotificationBody": "",
		"CommentCount": 0,
		"BlockCount": 0,
		"MemberCount": 0,
		"LeaderName": "Cheese",
		"EventScore": 0
	}

	return pack_json_response(guild_top_response)


@app.route("/api/user/other-user-info", methods=["GET", "POST"])
def other_user_info():
	identifiers = request_object().get("userIdInfo", [])
	if not isinstance(identifiers, list) or len(identifiers) > 32:
		raise AccountError("Invalid player list.")
	views = []
	for identifier in identifiers:
		if not isinstance(identifier, str):
			raise AccountError("Invalid player identifier.")
		# RequestOtherPlayer(userId, characterId) formats "{0},{1}".
		parts = identifier.split(",")
		if len(parts) > 2 or not parts[0] or (len(parts) == 2 and not parts[1]):
			raise AccountError("Invalid player identifier.")
		account_id = g.account_store.find_account(parts[0])
		if account_id is None:
			continue
		views.append(user_view(account_id, parts[1] if len(parts) == 2 else None))
	return pack_json_response({"UserViews": views})


def user_view(account_id, character_id=None):
	user = g.account_store.read(account_id, "User.json")
	parameter = g.account_store.read(account_id, "UserParameter.json")
	character_id = character_id if character_id is not None else parameter.get("FavoriteChrId", "pl001")
	characters = g.account_store.read(account_id, "UserCharacter.json")
	character = next((c for c in characters if c["CharacterId"] == character_id), None)
	if character is None:
		raise AccountError("Unknown profile character.")
	revision = g.account_store.icon_revision(account_id)
	is_online, last_login = g.account_store.presence(
		account_id, int(time.time()), app.config["ONLINE_TIMEOUT_SECONDS"])
	noble_start, noble_end = noble_dates()
	return {"UserId": user["id"], "Name": user["name"],
		"CharacterId": character_id,
		"UserCharacter": character,
		"UserEquipment": [], "UserItem": [], "EmblemId": parameter.get("EmblemId", ""),
		"GuildName": "", "Comment": parameter.get("Word", ""),
		"IsLogin": account_id == g.account_id or is_online, "LastLoginAt": utc_date(last_login),
		"TotalPower": 0, "MissionRank": parameter.get("MissionRank", 1), "EventScore": 0,
		**g.account_store.relationship_flags(g.account_id, account_id),
		"LastMessage": "", "IsNewMessage": False,
		"NobleStartAt": utc_date(noble_start), "NobleEndAt": utc_date(noble_end),
		"RankingCharacterId": "", "CharacterRankingRank": 0,
		"IconUrl": url_for("account_icon", account_id=account_id,
			revision=revision, _external=True, _scheme=public_scheme()) if revision else None}


@app.route("/api/friend/follow", methods=["POST"])
@app.route("/api/friend/follow-release", methods=["POST"])
@app.route("/api/friend/follower-release", methods=["POST"])
@app.route("/api/friend/block", methods=["POST"])
@app.route("/api/friend/block-release", methods=["POST"])
def change_friend_relationship():
	identifiers = request_object().get("targetUserIds")
	if not isinstance(identifiers, list) or len(identifiers) > 32:
		raise AccountError("Invalid player list.")
	targets = []
	for identifier in identifiers:
		if not isinstance(identifier, str) or not identifier or len(identifier) > 64:
			raise AccountError("Invalid player identifier.")
		account_id = g.account_store.find_account(identifier)
		if account_id is None:
			raise AccountError("Unknown player.")
		if account_id not in targets:
			targets.append(account_id)
	action = request.path.rsplit("/", 1)[-1]
	for account_id in targets:
		g.account_store.change_relationship(g.account_id, account_id, action)
	response = {"UserParameter": load_json("./data/user/UserParameter.json"),
		"Results": [user_view(account_id) for account_id in targets]}
	if action == "follow":
		response.update(Mission=[], MissionMaster=[], OrderdIds=[])
	return pack_json_response(response)


@app.route("/api/friend/list", methods=["GET", "POST"])
def friend_list():
	return pack_json_response({key: [user_view(account_id) for account_id in accounts]
		for key, accounts in g.account_store.relationship_lists(g.account_id).items()})


@app.route("/api/friend/search", methods=["POST"])
def friend_search():
	identifier = request_object().get("searchId")
	if not isinstance(identifier, str) or not identifier.strip() or len(identifier) > 64:
		raise AccountError("Invalid player identifier.")
	views = [user_view(account_id) for account_id in
		g.account_store.search_accounts(identifier.strip())]
	return pack_json_response({"User": views[0] if views else None, "Users": views})


@app.route("/api/character-icon/upload-icon", methods=["POST"])
def upload_icon():
	png = decode_icon(request_object().get("icon"))
	revision = g.account_store.put_icon(g.account_id, png)
	response_json = {"IconUrl": url_for("account_icon", account_id=g.account_id,
		revision=revision, _external=True, _scheme=public_scheme())}

	return Response(pack_json_response(response_json), content_type=MSGPACK_CONTENT_TYPE)


@app.route("/account-icons/<account_id>/<revision>.png", methods=["GET"])
def account_icon(account_id, revision):
	if len(account_id) != 32 or len(revision) != 64:
		return Response(status=404)
	g.account_store = AccountStore(app.config["ACCOUNT_DB"])
	png = g.account_store.get_icon(account_id, revision)
	if png is None:
		return Response(status=404)
	response = Response(png, content_type="image/png")
	response.headers["Cache-Control"] = "public, max-age=86400"
	response.set_etag(revision)
	return response.make_conditional(request)


def public_scheme():
	# TLS can terminate at the reverse proxy. Do not trust forwarded host/prefix.
	return "https" if request.headers.get("X-Forwarded-Proto") == "https" else request.scheme


# Catch-all for any path
@app.route("/<path:req_path>", methods=["GET", "POST"])
def any_path(req_path):
	# Account secrets and uploaded images must never be captured by this fallback.
	app.logger.info("Unhandled game route: %s", request.path)
	if req_path in ("api/friend/follow", "api/friend/follow-release",
			"api/friend/follower-release", "api/friend/block",
			"api/friend/block-release", "api/friend/search"):
		return account_error_response("This friend endpoint requires POST.", 405)
	if req_path in ("api/user/login-migration", "api/user/register-migration",
			"api/user/get-migration-info", "api/user/bnid-migration",
			"api/user/get-bnid-migration-info", "api/user/bnid-release"):
		return account_error_response("Account transfer is not implemented.", 501)
	json_path, msgpack_path = resolve_response_path("/" + req_path)
	if not (json_path.is_file() or msgpack_path.is_file()):
		return account_error_response("Unknown game route.", 404)
	return Response(load_for_request("/" + req_path), content_type=MSGPACK_CONTENT_TYPE)


if __name__ == "__main__":
	# os.makedirs(RESP_DIR, exist_ok=True)

	if not os.path.exists("./post/"):
		os.makedirs("./post/", exist_ok=True)
	
	# print("Current Working Directory:", os.getcwd())
	
	app.run(host="0.0.0.0", port=5001, debug=True)
