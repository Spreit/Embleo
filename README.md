**Embleo** is a WIP server emulator for a vertical mobile anime game.

# How to play
Download this server (`Code > Download ZIP`) and extract the archive.
## Running the Game Server
1. Install [Python](https://www.python.org/downloads/release/python-3147/)
2. Download [UV package manager](https://github.com/astral-sh/uv/releases/tag/0.12.15) for you platform
2. Extract the archive and copy `uv` into the `Embleo` folder (where README.md file is)
3. Open `src` folder
4. Double-click `run_setup.py` (`uv` will download necessary Python dependencies)
5. Type in (copy-paste) **Asset Server URL** into the newly open window and press Enter.

The script will then download necessary files from the specified **Asset Server**. Wait for it to finish.

(TODO: write a guide for self-hosting assets)

6. Double-click `run_server.py` to start the **Game Server**.

## Patching APK
A phone or emulator with Android 9-12 is required to install the game. Android 11 is recommended as it is confirmed working.

Currently, only japanese APK (not XAPK) v.1.6.0  is supported (it has english language option). 

1. Install [Java](https://www.java.com/en/download/manual.jsp)
2. Download [uber-apk-signer-1.3.0.jar](https://github.com/patrickfav/uber-apk-signer/releases)
3. Put `uber-apk-signer-1.3.0.jar` in `/src/scripts/` folder (this folder will also have "apk_patcher.py")
4. Drag-and-drop the game **APK** onto the `apk_patcher.py` file.
5. Type in **Game Server URL** and press Enter 
  -  You can find the URL in the **" \* Running on http://192..."** line after double-clicking the `server.py`. (Example URL: http://192.168.0.50:5001) 
6. 2 patched APKs will appear in the same folder as your original APK.
7. Install the APK with **edited-aligned-debugSigned.apk** at the end

Since the **Game Server** is hosted locally, your phone needs to be in the same network as your computer.

##	Success
Finally, if:
1. **Game Server** is running (`/src/run_server.py`)
2. Your smartphone/emulator is in the same network as your computer that runs the **Game Server**
3. **Asset Server** is running and reachable
4. Patched APK was installed without errors
5. The entered **Game Server URL** is correct

You will see a disclaimer and the title screen after opening the game.

Congradulations!

# During play
Account system doesn't work yet, you have to entering a nickname each time you start the game. Shortest nickname is any 2 letters and it is not saved by the game.

The in-game saving system is also not functional. Instead, `/src/checkpoint.txt` is created and updated each time you reach a checkpoint during an episode. Starting an episode will put you at the last in-game checkpoint, most of the time the UI will be hidden, besides the control pad. You can delete the `/src/checkpoint.txt` file to start the episode from the beggining.
