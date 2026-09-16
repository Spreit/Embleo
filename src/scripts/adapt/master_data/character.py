import json

countries = {
    "pl001": 1,
    "pl002": 1,
    "pl003": 1,
    "pl004": 8,
    "pl005": 2,
    "pl006": 3,
    "pl007": 4,
    "pl008": 5,
    "pl009": 5,

    "pl010": 2,
    "pl011": 7,
    "pl012": 2,
    "pl013": 2,
    "pl014": 8,
    "pl015": 2,
    "pl016": 3,

    "pl017": 8,
    "pl018": 2,
    "pl019": 1,
    "pl020": 6,
    "pl021": 2
}
factions = {
	"pl001": 1,
	"pl002": 1,
	"pl003": 2,
	"pl004": 1,
	"pl005": 1,
	"pl006": 1,
	"pl007": 1,
	"pl008": 1,
	"pl009": 1,

	"pl010": 2,
	"pl011": 2,
	"pl012": 2,
	"pl013": 2,
	"pl014": 2,
	"pl015": 2,
	"pl016": 2,

	"pl017": 3,
	"pl018": 3,
	"pl019": 3,
	"pl020": 3,
	"pl021": 3
}
sort_order = {
    "pl001": 0,
    "pl002": 1,
    "pl009": 2,
    "pl004": 3,
    "pl005": 4,
    "pl007": 5,
    "pl006": 6,
    "pl008": 7,

    "pl010": 8,
    "pl013": 9,
    "pl011": 10,
    "pl012": 11,
    "pl014": 12,
    "pl003": 13,
    "pl015": 14,
    "pl016": 15,

    "pl017": 16,
    "pl020": 17,
    "pl018": 18,
    "pl021": 19,
    "pl019": 20
}

character_base = {
    "CharacterId": "",
    "Country": 0,
    "Faction": 0,
    "DominantHand": 0,
    "BothHands": True,
    "ChargeTime": 1.0,
    "DamageRate": [],
    "InitialSpeed": [],
    "Acceleration": [],
    "MaxSpeed": [],
    "Friction": [],
    "WeaponScale": 1.0,
    "EffectPath": "",
    "SoundPath": "",
    "CounterGaugeDispDistance": 1.0,

    "LevelupCurve": "",
    "LevelupScale": 1.0,

    "Hp": 0,
    "HpCurve": "",
    "HpScale": 1.0,

    "Attack": 0,
    "AttackCurve": "",
    "AttackScale": 1.0,

    "Defense": 0,
    "DefenseCurve": "",
    "DefenseScale": 1.0,

    "UniqueParamData": "",
    "SortOrder": 0
}


def fill_base_dict_with_debug_data_if_same_keys(basedata, debugdata):
    result = dict.copy(basedata)

    for key in basedata.keys():
        if key in debugdata:
            result[key] = debugdata[key]

    return result


def adapt_debug_character_master_data(debug_data):
    AdaptedMasterData = []

    # Doesn't work when embedded
    base_data_path = "./base_data/character/"

    CharacterBase = dict.copy(character_base)

    CharacterCountries = countries
    CharacterFactions = factions
    # Used by the game when you select a faction on character tab and in help section
    CharacterSortOrder = sort_order

    for debug_entry in debug_data["CharacterDatas"]:
        AdaptedEntry = fill_base_dict_with_debug_data_if_same_keys(CharacterBase, debug_entry)

        character_id = debug_entry["ID"]
        AdaptedEntry["CharacterId"] = character_id

        # The check if needed for characters that are not from the main 21
        AdaptedEntry["Country"] = CharacterCountries[character_id] if character_id in CharacterCountries else 1
        AdaptedEntry["Faction"] = CharacterFactions[character_id] if character_id in CharacterFactions else 1

        AdaptedEntry["BothHands"] = bool(debug_entry["BothHands"])

        AdaptedEntry["Hp"] = debug_entry["HpBase"]
        AdaptedEntry["Attack"] = debug_entry["AttackBase"]
        AdaptedEntry["Defense"] = debug_entry["DefenseBase"]

        AdaptedEntry["UniqueParamData"] = json.dumps(debug_entry["UniqueParam"])
        AdaptedEntry["SortOrder"] = CharacterSortOrder[character_id] if character_id in CharacterSortOrder else 0

        AdaptedMasterData.append(AdaptedEntry)

    return AdaptedMasterData
