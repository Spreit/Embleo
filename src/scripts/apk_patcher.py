import subprocess
import sys
import zipfile
import os

"""
    How to use
- Drag-and-drop APK onto the script 
- Enter new Game Server URL
- Wait for it to finish
- Install the APK with "edited-aligned-debugSigned.apk" at the end

If the patcher window auto-closes, put the APK in the same folder as the patcher and double-click it.
"""

"""
    How it works
The Game Server URL is stored in /assets/bin/Data/level0 file at 0x00011364.
All this script does is:
- Change current Game Server URL to provided URL and its hardcoded length
- Remove *.colopl.jp template and its hardcoded length (otherwise Global APK crashes)

Since changing anything within the APK breaks its integrity, uber-apk-signer is used to fix this.
"""

'''
TODO
Add more URL checks
Make messaging more clear
Add ability to patch using hardcoded values below
Make uber-apk-signer finder
'''

# Alternative method to patch an APK
# To make the patcher use the following parameters
# Set manual_patching to True

manual_patching = False

manual_apk_path = "./lumi.apk"
manual_server_url = "replace_this_with_server_address"


# Variables
max_length = 35
url_offset = 0x00011364

second_link_length = 16
second_url_offset = 0x00011388

level0_path = "assets/bin/Data/level0"


def get_current_url(level0_bytes):
    url_bytes = level0_bytes[url_offset:]

    # Go through the bytes until 0x00
    url_length = 0
    for i in range(max_length + 1):
        if url_bytes[i] == 0:
            url_length = i
            break

    return url_bytes[:url_length]


def patch_game_server_url_in_level0(new_url, level0_bytes):
    patched_level0 = bytearray(level0_bytes)

    new_url_length = len(new_url)

    # Clear current URL
    for i in range(max_length + 1):
        patched_level0[url_offset + i] = 0

    # Paste new URL
    for i in range(new_url_length):
        patched_level0[url_offset + i] = ord(new_url[i])

    # Patch URL size
    patched_level0[url_offset - 4] = new_url_length

    print(new_url_length, get_current_url(patched_level0))

    # Zero out second link
    for i in range(second_link_length):
        patched_level0[second_url_offset + i] = 0

    return bytes(patched_level0)


def get_path_to_apk(current_working_directory):
    # Check dragged and dropped APK
    path_to_apk = ""

    if manual_patching:
        return manual_apk_path

    try:
        path_to_apk = sys.argv[1]
        print("Path to the dropped apk:", path_to_apk)
        return path_to_apk

    # If not dropped, check the script folder for APKs
    except IndexError:
        print("No file dropped, using script values")
        print("Looking for APK at ", current_working_directory)

        file_list = os.listdir("./")

        for file in file_list:

            if ".apk" in file:
                path_to_apk = current_working_directory + "/" + file
                print(path_to_apk)

    return path_to_apk


def extract_level0_from_apk(path_to_apk):
    level0_bytes: bytes

    with zipfile.ZipFile(path_to_apk, "r", compression=zipfile.ZIP_DEFLATED) as apk:
        with apk.open(level0_path, mode="r") as level0:
            level0_bytes = level0.read()

    return level0_bytes


def make_apk_with_patched_level0(apk_path, patched_apk_path):
    pass


if __name__ == "__main__":
    print("= = = Embleo APK patcher = = =")

    working_directory = os.getcwd()

    argument_amount = len(sys.argv)

    if argument_amount > 2:
        print("Too many arguments. If path to APK contains spaces, put it inbetween double quotes.")
        input("Press Enter to exit")
        exit()

    # print(os.listdir())
    print("Amount of sys.argv", argument_amount)

    # Find original APK, or any at this point
    path_to_apk = get_path_to_apk(working_directory)

    if path_to_apk == "":
        print("No APK was found. Either: \n- Drag-and-drop the APK onto the apk_patcher file \nor \n- Put the APK next to the apk_patcher and run the script again.")

    # Check extension
    if path_to_apk[-4:] == "xapk":
        print("XAPK is not supported.")
        input("Press Enter to exit")
        exit()

    if not os.path.isfile(path_to_apk):
        print("Couldn't find game APK at", working_directory)
        input()
    else:
        print("Found APK at", path_to_apk)

    # Patching Game Server URL
    current_level0_bytes = extract_level0_from_apk(path_to_apk)
    current_url = get_current_url(current_level0_bytes)

    print("Current Game Server URL:", current_url)

    is_url_valid = False

    while not is_url_valid:
        print("Enter new Game Server URL:")
        new_server_url = input()

        # Check URL validity
        if len(new_server_url) > max_length:
            print("This Game Server URL is too long! Are you confusing it with asset server URL?")
        elif ("http://" != new_server_url[:7]) and ("https://" != new_server_url[:8]):
            print("Game Server URL has to start with either \"http://\" or \"https://\".")
        else:
            is_url_valid = True


    patched_level0 = patch_game_server_url_in_level0(new_server_url, current_level0_bytes)

    edited_apk_path = path_to_apk[:-4] + " edited.apk"
    # Make a new APK and copy all files, but level0
    with zipfile.ZipFile(path_to_apk, "r") as og_apk:
        with zipfile.ZipFile(edited_apk_path, "w", compression=zipfile.ZIP_STORED) as apk:
            apk.comment = og_apk.comment # preserve the comment
            for item in og_apk.infolist():

                if item.filename != level0_path:
                    apk.writestr(item, og_apk.read(item.filename))
                else:
                    apk.writestr(item, patched_level0)

    # Align and sign apk
    uber_sign_command = ["java", "-jar", "uber-apk-signer-1.3.0.jar", "-apk", edited_apk_path]
    subprocess.run(uber_sign_command)

    print("Patched the APK with URL:", new_server_url)
    input("Press Enter to exit")
    exit()
