import copy
import json
from enum import Enum

from .user.UserEpisode_generator import generateUserEpisode

# I need some more info for characters

ALL_EPISODES = True
ALL_EQUIPMENT = False
ALL_DISHES = True

"""
Files that needs to be generated

+ UserCharacter
+ UserEpisode
+ UserEquipment
UserItem

"""

base_character_id_format = "pl{:03d}"
base_costume_format = "{char_id}_04_001"
base_weapon_format = "{weap_id}_04_{weap_index}"

# To not add them manually all the time
additional_equipment_id_list = [
    "pl001_05_001",
    "wp001_05_001"
]

character_base_weapons = {
    "pl001": "wp001_04_001",
    "pl002": "wp006_04_001",
    "pl003": "wp002_04_001",
    "pl004": "wp005_04_001",
    "pl005": "wp002_04_002",
    "pl006": "wp004_04_001",
    "pl007": "wp006_04_002",
    "pl008": "wp003_04_001",
    "pl009": "wp007_04_001",
    "pl010": "wp007_04_002",
    "pl011": "wp001_04_002",
    "pl012": "wp006_04_003",
    "pl013": "wp002_04_003",
    "pl014": "wp005_04_002",
    "pl015": "wp003_04_002",
    "pl016": "wp004_04_002",
    "pl017": "wp004_04_003",
    "pl018": "wp001_04_003",
    "pl019": "wp003_04_003",
    "pl020": "wp005_04_003",
    "pl021": "wp007_04_003"
}


def load_json(path):
    data = {}

    with open(path, "r", encoding='utf-8') as f:
        data = json.load(f)

    return data


def save_json(path, data):
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


base_character = {
    "CharacterId": "",
    "Level": 1,
    "Exp": 0,
    "LevelCap": 10,
    "CapExp": 0,
    "VisualEquipment": [
        "",
        "",
        "",
        "",
        "",
        ""
    ],
    "Costume": [],
    "WeaponMain": [],
    "WeaponSub": [],
    "AccessoryMain": [],
    "AccessorySub": [],
    "CostumeSpell": [],
    "WeaponSpell": [],
    "Food": ["dish_3_01"],
    "Flags": 0,
    "LastPower": 0,
    "CapExpPrev": 0,
    "CapExpNext": 0
}


def generateUserCharacter():
    UserCharacterData = []
    BaseCharacterWeaponDict = character_base_weapons

    for char_index in range(1, 22):
        BaseUserCharacter = copy.deepcopy(base_character)

        character_id = base_character_id_format.format(char_index)

        BaseUserCharacter["CharacterId"] = character_id

        base_costume = base_costume_format.format(char_id=character_id)
        base_weapon = BaseCharacterWeaponDict[character_id]

        BaseUserCharacter["VisualEquipment"][0] = base_costume
        BaseUserCharacter["VisualEquipment"][1] = base_weapon

        BaseUserCharacter["Costume"].append(base_costume)
        BaseUserCharacter["CostumeSpell"].append(base_costume)

        BaseUserCharacter["WeaponMain"].append(base_weapon)
        BaseUserCharacter["WeaponSpell"].append(base_weapon)

        UserCharacterData.append(BaseUserCharacter)

    return UserCharacterData


class EquipmentCategory(Enum):
    Unknown = 0
    Costume = 1
    Weapon = 2
    Accessory = 3
    Attachment = 4


def convertEquipmentIDtoDataEntry(equipment_id):
    pass


# For testing purposes
def addAdditionalUserEquipment(equipment_id_list):
    additional_equipment = []

    for equipment_id in equipment_id_list:
        pass

    return additional_equipment


base_equipment = {
    "EquipmentId": "",
    "Category": 0,
    "Level": 1,
    "Exp": 0,
    "UpdatedAt": 0,
    "SpLevel": 1,
    "SpNext": 0,
    "CreatedAt": 0
}


def generateUserEquipment(unlock_all=False):
    UserEquipmentData = []
    BaseCharacterWeaponDict = character_base_weapons

    # Costume + Weapon per character
    for char_index in range(1, 22):
        character_id = base_character_id_format.format(char_index)

        BaseUserCostume = copy.deepcopy(base_equipment)
        BaseUserCostume["EquipmentId"] = base_costume_format.format(char_id=character_id)
        BaseUserCostume["Category"] = EquipmentCategory.Costume.value

        BaseUserWeapon = dict.copy(base_equipment)
        BaseUserWeapon["EquipmentId"] = BaseCharacterWeaponDict[character_id]
        BaseUserWeapon["Category"] = EquipmentCategory.Weapon.value

        UserEquipmentData.append(BaseUserCostume)
        UserEquipmentData.append(BaseUserWeapon)

    if unlock_all:
        EquipmentMasterData = load_json("./data/masterdata/EquipmentMasterData.json")
        base_entry = copy.deepcopy(base_equipment)

        for master_entry in EquipmentMasterData:
            user_entry = base_entry

            user_entry["EquipmentId"] = master_entry["EquipmentId"]
            user_entry["Category"] = master_entry["Category"]

            if user_entry not in UserEquipmentData:
                UserEquipmentData.append(dict.copy(user_entry))

    UserEquipmentData.extend(addAdditionalUserEquipment(additional_equipment_id_list))

    print("Generated UserEquipment")

    return UserEquipmentData


def generateUserItem(unlock_all=False):
    # Dishes
    # Ingredient
    # Other?
    userItems = []

    curry = {
        "ItemId": "dish_3_01",
        "Category": 2,
        "Count": 10
    }

    userItems.append(curry)

    return userItems


def generateSaveFile(output_folder):
    save_json(output_folder + "UserCharacter.json", generateUserCharacter())
    save_json(output_folder + "UserEpisode.json", generateUserEpisode())
    save_json(output_folder + "UserEquipment.json", generateUserEquipment(ALL_EQUIPMENT))
    save_json(output_folder + "UserItems.json", generateUserItem())
