import os
import pathlib
import requests
import UnityPy
import json

from scripts.adapt.adapt_debug_master_data import adapt_debug_master_data
from scripts.adapt.adapt_debug_scenario import adapt_debug_scenario_file, batch_adapt_scenario_folder
from scripts.adapt.adapt_chronology_for_server import generate_character_chronology_json

from scripts.generate.generate_episode_master_data import generate_episode_master_data
from scripts.generate.generate_temp_level_curve import generate_character_curve_list, generate_equipment_curve_list
from scripts.generate.generate_save_file import generateSaveFile

'''
TODO

Add URL checks or something

Make a selector for which part to setup, to not go through the entire process.
For example:
	Check if "download" folder exist
'''

# Download and extract manifest from the asset server
asset_server_link_file = "./asset_server_link.txt"
asset_server_link = ""

DOWNLOAD_FOLDER = "./data/download/"
EXTRACT_FOLDER = "./data/extract/"

manifest_version = "fd2ab21941c4f074bb19997e67f62eb1"
manifest_file_name = "manifest_{0}.ab".format(manifest_version)

# Functions

def load_asset_server_url():
    if os.exist(asset_server_file):
        print("Found file")


def make_placeholder_link_file():
    pass


def does_file_exist(path):
	if os.path.isfile(path):
		return True

	return False


def download_file(url, output_folder=DOWNLOAD_FOLDER, force_redownload=False):
    response = requests.get(url)

    if response.status_code == 200:
        # Save file
        pass

    if response.status_code == 404:
        print("File not found:", url)

    file_data = response.content

    file_name_without_server_url = url[len(asset_server_link):]

    # Save file at path
    # print(file_name_without_server_url)

    output_file_path = output_folder + file_name_without_server_url

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    if does_file_exist(output_file_path):
        print("File", output_file_path, "is already downloaded")

        if not force_redownload:
            return

    with open(output_file_path, "wb") as of:
        of.write(file_data)


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

            output_file_path = output_folder + short_path + ".json"

            # make sure that the dir of that path exists
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            with open(output_file_path, "wt", encoding="utf8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)


def adapt_manifest_entry_for_server(entry):
    asset_name = entry["Name"]
    version = entry["Version"]

    return asset_name + "_" + version + ".ab"


def get_all_files_in_folder_manifest(path_to_manifest_json, folder, exclude=""):
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

    master_data_path = "./data/masterdata/"

    print("Generating Episode Master Data")
    generate_episode_master_data(master_data_path)

    # LevelCurves
    print("Generating Level Curves")
    char_status_file_name = "TemporaryLevelStatusCurveCharacterMasterData.json"

    with open(master_data_path + char_status_file_name, "w") as f:
        curve_data = generate_character_curve_list()
        json.dump(curve_data, f, indent=4)

    equip_stats_file_name = "TemporaryLevelStatusCurveEquipmentMasterData.json"
    with open(master_data_path + equip_stats_file_name, "w") as f:
        curve_data = generate_equipment_curve_list()
        json.dump(curve_data, f, indent=4)

    # Gacha


def get_asset_server_link():
    is_saved_url_found = False
    is_url_valid = False

    # Check if there is Asset Server URL file
    if os.path.exists(asset_server_link_file):

        with open(asset_server_link_file, "r") as f:
            asset_server_link = f.readline()

            if asset_server_link == "":
                print("Saved Asset Server URL is empty")
            else:
                print("Found Asset Server URL in", asset_server_link_file, ":", asset_server_link)
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


manifest = False
download = False
extract = False
adapt_master_data = True
adapt_scenario = True
generate = True
save_data = True


def setup(asset_server_link):

    if manifest:
        print("Downloading and extracting manifest file")
        # Download manifest
        download_file(asset_server_link + manifest_file_name)
        # Extract manifest
        extract_file(DOWNLOAD_FOLDER + manifest_file_name)

    # Downloading and extracting files

    if download:
        print("Downloading necessary files...")
        # Download masterdatadebug files
        print("Downloading masterdatadebug")
        MasterDataDebug_files = get_all_files_in_folder_manifest(EXTRACT_FOLDER + "manifest.json", "masterdatadebug/")
        download_manifest_files_from_asset_server(MasterDataDebug_files)

        # Download masterdata files
        print("Downloading masterdata")
        MasterData_files = get_all_files_in_folder_manifest(EXTRACT_FOLDER + "manifest.json", "masterdata/",
                                                            exclude="masterdata/episode/")
        download_manifest_files_from_asset_server(MasterData_files)

        # japanese chronology, single file
        print("Downloading chronology")
        Chronology = get_all_files_in_folder_manifest(EXTRACT_FOLDER + "manifest.json",
                                                      "lang_ja/texts/commonterm/chronology")
        download_manifest_files_from_asset_server(Chronology)

    # Extract downloaded AssetBundles
    if extract:
        print("= = = Extracting downloaded files (may take some time) = = =")

        downloaded_files = list(pathlib.Path(DOWNLOAD_FOLDER).rglob("*.*"))

        for path in downloaded_files:
            extract_file(str(path))

    if adapt_master_data:
        adapt_debug_master_data(EXTRACT_FOLDER)

        chronology_output_folder = "./data/chronology/"
        generate_character_chronology_json(EXTRACT_FOLDER + "lang_ja/texts/commonterm/Chronology.json", chronology_output_folder)

    if adapt_scenario:
        scenario_output_folder = "./data/masterdata/scenario/"
        batch_adapt_scenario_folder(EXTRACT_FOLDER + "/masterdatadebug/scenario/", scenario_output_folder)

    if generate:
        generate_master_data()

    if save_data:
        save_data_path = "./data/user/"
        generateSaveFile(save_data_path)


if __name__ == "__main__":
    asset_server_link = get_asset_server_link()

    print("Asset Server URL:", asset_server_link)

    setup(asset_server_link)

    print("")
    print("Finished setting up the server")
    input("Press Enter to exit")


