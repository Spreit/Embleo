import os
import pathlib
import requests
import UnityPy
import json
from pathlib import Path

from scripts.adapt.adapt_debug_master_data import adapt_debug_master_data
from scripts.adapt.adapt_debug_scenario import adapt_debug_scenario_file, batch_adapt_scenario_folder
from scripts.adapt.adapt_chronology_for_server import generate_character_chronology_json

from scripts.adapt.extract_sequence_data import extract_all_SequenceSetting_files
from scripts.adapt.adapt_sequence_data import adapt_all_sequence_data

from scripts.generate.generate_episode_master_data import generate_episode_master_data
from scripts.generate.generate_temp_level_curve import generate_character_curve_list, generate_equipment_curve_list
from scripts.generate.generate_save_file import generateSaveFile

'''
TODO

Move to proper Path system
- asset_server_link can be moved after server restructuring

Add URL checks or something

Make a selector for which part to setup, to not go through the entire process.
For example:
    Check if "download" folder exist
'''

manifest = True
download = True
extract = True
adapt_master_data = True
extract_sequences = True
adapt_sequences = True
adapt_scenario = True
generate = True
save_data = True

DEBUG_CONFIG = False

if DEBUG_CONFIG:
    manifest = False
    download = False
    extract = False
    adapt_master_data = True
    extract_sequences = False
    adapt_sequences = False
    adapt_scenario = False
    generate = True
    save_data = False

# Download and extract manifest from the asset server
path_cwd = Path.cwd()

asset_server_link_file = path_cwd / "src" / "asset_server_link.txt"
asset_server_link = ""

DATA_FOLDER = path_cwd / "src" / "data"
DOWNLOAD_FOLDER = DATA_FOLDER / "download"
EXTRACT_FOLDER = DATA_FOLDER / "extract"

CHRONOLOGY_FOLDER = DATA_FOLDER / "chronology"
MASTER_DATA_FOLDER = DATA_FOLDER / "masterdata"
SAVE_DATA_FOLDER = DATA_FOLDER / "user"

SEQUENCE_SETTING_EXTRACT_FOLDER = EXTRACT_FOLDER / "SequenceSetting"

manifest_version = "fd2ab21941c4f074bb19997e67f62eb1"
manifest_file_name = "manifest_{0}.ab".format(manifest_version)


# Functions

def load_asset_server_url():
    if os.exist(asset_server_link_file):
        print("Found file")


def make_placeholder_link_file():
    pass


def does_file_exist(path):
    if os.path.isfile(path):
        return True

    return False


def download_file(url, output_folder=DOWNLOAD_FOLDER, force_redownload=False):
    file_name_without_server_url = url[len(asset_server_link):]

    # Save file at path
    # print(file_name_without_server_url)

    output_file_path = output_folder / file_name_without_server_url

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    if does_file_exist(output_file_path):
        print("File", output_file_path, "is already downloaded")

        if not force_redownload:
            return
    
    response = requests.get(url)

    if response.status_code == 200:
        # Save file
        pass

    if response.status_code == 404:
        print("File not found:", url)

    file_data = response.content

    with open(output_file_path, "wb") as of:
        of.write(file_data)
        print("Downloaded", output_file_path)


def extract_file(file_path, output_folder=EXTRACT_FOLDER):
    # Shorten extracted file path
    masterdatadebug_shorten = "assets/variableresources/develop/assetbundles/"
    masterdata_shorten = "assets/variableresources/core/assetbundles/"

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    # load that file via UnityPy.load
    env = UnityPy.load(file_path)

    # alternative way which keeps the original path
    for asset_path, obj in env.container.items():
        # All scripts in the AssetBundle
        if obj.type.name in ["MonoBehaviour"]:

            # Shorten container path
            short_path: str

            if masterdatadebug_shorten in asset_path:
                short_path = asset_path[len(masterdatadebug_shorten):]
            elif masterdata_shorten in asset_path:
                short_path = asset_path[len(masterdata_shorten):]
            else:
                short_path = asset_path

            # Remove .asset extension
            if short_path != "manifest":
                short_path = short_path[:-len(".asset")]

            data = obj.deref_parse_as_dict()

            # Make file names LookLikeThis and not looklikethis
            cased_file_name = data["m_Name"]

            short_path = short_path[:-len(cased_file_name)] + cased_file_name

            # print(short_path)

            output_file_path = output_folder / (short_path + ".json")

            # make sure that the dir of that path exists
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            with open(output_file_path, "wt", encoding="utf8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)


def adapt_manifest_entry_for_server(entry):
    asset_name = entry["Name"]
    version = entry["Version"]

    return asset_name + "_" + version + ".ab"


def get_all_files_in_folder_manifest(folder, exclude="", path_to_manifest_json=(EXTRACT_FOLDER / "manifest.json")):
    manifest_data: dict

    with open(path_to_manifest_json, "r") as f:
        manifest_data = json.load(f)

    server_file_list = []

    for entry in manifest_data["m_Entries"]:

        if folder in entry["Name"]:
            if exclude != "":
                if exclude in entry["Name"]:
                    continue

            server_file_path = adapt_manifest_entry_for_server(entry)
            server_file_list.append(server_file_path)
        # print(server_file_path)

    return server_file_list


def download_manifest_files_from_asset_server(file_list):
    for file_path in file_list:
        file_server_path = asset_server_link + file_path
        # print(file_server_path)
        download_file(file_server_path)


def generate_master_data():
    print("= = = Generating other master data = = =")

    master_data_path = DATA_FOLDER / "masterdata"

    print("Generating Episode Master Data")
    generate_episode_master_data(master_data_path, CHRONOLOGY_FOLDER, master_data_path / "SecretMissions.json")

    # LevelCurves
    print("Generating Character Level Curves")
    char_status_file_name = "TemporaryLevelStatusCurveCharacterMasterData.json"
    with open(master_data_path / char_status_file_name, "w") as f:
        curve_data = generate_character_curve_list()
        json.dump(curve_data, f, indent=4)

    print("Generating Equipment Level Curves")
    equip_stats_file_name = "TemporaryLevelStatusCurveEquipmentMasterData.json"
    with open(master_data_path / equip_stats_file_name, "w") as f:
        curve_data = generate_equipment_curve_list()
        json.dump(curve_data, f, indent=4)

    # Gacha


def get_asset_server_link():
    is_saved_url_found = False
    is_url_valid = False

    # Check if there is Asset Server URL file
    # print("Does asset_server_link.txt exist?", os.path.exists(asset_server_link_file))
    if os.path.exists(asset_server_link_file):

        with open(asset_server_link_file, "r") as f:
            asset_server_link = f.readline()

            if asset_server_link == "":
                print("Saved Asset Server URL is empty")
            else:
                print("Found Asset Server URL in", asset_server_link_file)
                is_saved_url_found = True
                is_url_valid = True

    while not is_url_valid:
        # Ask for Asset Server URL and write it to file
        if not is_saved_url_found:
            print("Please input Asset Server URL and then press Enter:")
            asset_server_link = input()

            # Simple validity check
            if ("http://" in asset_server_link) or ("https://" in asset_server_link):
                with open(asset_server_link_file, "w") as f:
                    f.write(asset_server_link)
                is_url_valid = True
                print("Saved Asset Server URL at", asset_server_link_file)
            else:
                print("Entered Asset Server URL seems to be invalid. Check if you entered \"http://\" or \"https://\" correctly.")

    return asset_server_link

download_list = [
    {
        "print_name": "masterdatadebug",
        "manifest_folder": "masterdatadebug/",
        "exclude": ""
    },
    {
        "print_name": "masterdata",
        "manifest_folder": "masterdata/",
        "exclude": "masterdata/episode/"
    },
    {
        "print_name": "chronology",
        "manifest_folder": "lang_ja/texts/commonterm/chronology",
        "exclude": ""
    },
    {
        "print_name": "enemy data",
        "manifest_folder": "characters/enemy/",
        "exclude": ""
    },
    {
        "print_name": "character data",
        "manifest_folder": "characters/player/",
        "exclude": ""
    }
]


def setup(asset_server_link):

    if manifest:
        print("Downloading and extracting manifest file")
        # Download manifest
        download_file(asset_server_link + manifest_file_name)
        # Extract manifest
        extract_file((DOWNLOAD_FOLDER / manifest_file_name).as_posix())

    # Downloading and extracting files
    if download:
        print("Downloading necessary files...")

        for download_group in download_list:
            print("Downloading", download_group["print_name"])
            files_to_download = get_all_files_in_folder_manifest(download_group["manifest_folder"],
                                                                 exclude=download_group["exclude"])
            download_manifest_files_from_asset_server(files_to_download)


    # Extract downloaded AssetBundles
    if extract:
        print("= = = Extracting downloaded files (may take some time) = = =")

        downloaded_files = set(pathlib.Path(DOWNLOAD_FOLDER).rglob("*.*"))

        # EXCLUDE character/enemy data, since it is extracted separately
        enemy_files = set(pathlib.Path(DOWNLOAD_FOLDER).rglob("characters/**"))
        downloaded_files = downloaded_files - enemy_files

        for path in downloaded_files:
            extract_file(str(path))

    if adapt_master_data:
        adapt_debug_master_data(EXTRACT_FOLDER, MASTER_DATA_FOLDER)

        generate_character_chronology_json(EXTRACT_FOLDER / "lang_ja/texts/commonterm/Chronology.json",
                                           CHRONOLOGY_FOLDER)

    # Sequences are handled separately from other master data
    if extract_sequences:
        extract_all_SequenceSetting_files(DOWNLOAD_FOLDER / "characters", SEQUENCE_SETTING_EXTRACT_FOLDER)

    if adapt_sequences:
        character_sequence, enemy_sequence = adapt_all_sequence_data(SEQUENCE_SETTING_EXTRACT_FOLDER, DOWNLOAD_FOLDER / "characters")

        if character_sequence != []:
            with open(MASTER_DATA_FOLDER / "CharacterSequenceMasterData.json", "w", encoding="UTF-8") as f:
                json.dump(character_sequence, f, indent=4)

        if enemy_sequence != []:
            with open(MASTER_DATA_FOLDER / "EnemySequenceMasterData.json", "w", encoding="UTF-8") as f:
                json.dump(enemy_sequence, f, indent=4)

    if adapt_scenario:
        scenario_output_folder = DATA_FOLDER / "masterdata" / "scenario"
        batch_adapt_scenario_folder(EXTRACT_FOLDER / "masterdatadebug/scenario", scenario_output_folder)

    if generate:
        generate_master_data()

    if save_data:
        generateSaveFile(SAVE_DATA_FOLDER)


if __name__ == "__main__":
    print("Current working directory", os.getcwd())

    asset_server_link = get_asset_server_link()

    print("Asset Server URL:", asset_server_link)

    setup(asset_server_link)

    print("")
    print("Finished setting up the server")
    input("Press Enter to exit")


