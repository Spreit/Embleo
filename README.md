**Embleo** is a WIP server emulator for a vertical mobile anime game.

# How to play
Download this server (`Code > Download ZIP`) and extract the archive.
## Running the Game Server
1. Install [Python](https://www.python.org/downloads/release/python-3147/)
2. Double-click `install_python_dependencies.py`
3. Open `src` folder
4. Double-click `setup_server.py`
5. Type in (copy-paste) **Asset Server URL** into the newly open window and press Enter.

The script will then download necessary files from the specified **Asset Server**. Wait for it to finish.

(TODO: write a guide for self-hosting assets)

6. Double-click `server.py` to start the **Game Server**.

## Patching APK
A phone or emulator with Android **11**-13 is required to install the game.

Currently, only japanese APK (not XAPK) v.1.6.0  is supported (it has english language option). 

1. Install [Java](https://www.java.com/en/download/manual.jsp)
2. Download [uber-apk-signer-1.3.0.jar](https://github.com/patrickfav/uber-apk-signer/releases)
3. Put `uber-apk-signer-1.3.0.jar` in `/src/scripts/` folder (this folder will also have "apk_patcher.py")
4. Drag-and-drop the APK onto the `apk_patcher.py` file.
5. Type in **Game Server URL** and press Enter 
  -  You can find the URL in the **" \* Running on http://192..."** line after double-clicking the `server.py`. (Example URL: http://192.168.0.50:5001) 
6. 2 patched APKs will appear in the same folder as your original APK.
7. Install the APK with **edited-aligned-debugSigned.apk** at the end

Since the **Game Server** is hosted locally, your phone needs to be in the same network as your computer.

##	Success
Finally, if:
1. **Game Server** is running `/src/server.py`
2. Your smartphone/emulator is in the same network as your computer that runs the **Game Server**
3. **Asset Server** is running and reachable
4. Patched APK was installed without errors
5. The entered **Game Server URL** is correct

You will see a disclaimer and the title screen after opening the game.

Congradulations!
