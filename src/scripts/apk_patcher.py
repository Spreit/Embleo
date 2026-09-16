import subprocess
import sys
import zipfile

'''
TODO
Add checks
'''

# Alternative method to patch an APK
path_to_apk = "./lumi_apk.apk"
new_server_url = "replace_this_with_server_address"

# Variables
max_length = 35
url_offset = 0x00011364
colopl_mention_offset = 0x00011390

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

    # Clear current link
    for i in range(max_length + 1):
        patched_level0[url_offset + i] = 0

    # Paste new link
    for i in range(len(new_url)):
        patched_level0[url_offset + i] = ord(new_url[i])

    print(get_current_url(patched_level0))

    return bytes(patched_level0)


if __name__ == "__main__":

    # Check dragged and dropped APK
    try:
        path_to_apk = sys.argv[1]
        print(path_to_apk)
    except IndexError:
        print("No file dropped, using script values")

    # Check extension
    if path_to_apk[-4:] == "xapk":
        print("XAPK is not supported.")
        input()
        exit()

    current_url: str
    current_level0_bytes: bytes

    with zipfile.ZipFile(path_to_apk, "r", compression=zipfile.ZIP_DEFLATED) as apk:
        with apk.open(level0_path, mode="r") as level0:
            current_level0_bytes = level0.read()
            current_url = get_current_url(current_level0_bytes)

    print("Current game server URL:", current_url)

    print("Enter new game server URL:")
    new_server_url = input()

    if len(new_server_url) > max_length:
        print("This game server URL is too long! Are you confusing it with asset server URL?")
        input()
        exit()

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

    # Sign apk
    uber_sign_command = ["java", "-jar", "uber-apk-signer-1.3.0.jar", "-apk", edited_apk_path]
    subprocess.run(uber_sign_command)

    print("Patched the APK with URL:", new_server_url)
    print("Press any button to exit")
    input()
    exit()
