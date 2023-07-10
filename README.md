# Advynia
An editor for Yoshi's Island: Super Mario Advance 3.

Aiming to be a streamlined editor experience, providing what's needed for creating custom Yoshi's Island levels, with no in-depth ROM hacking knowledge required. Work in progress.

## Features, as of 0.5
- Sublevel editing, with in-game graphics for objects, sprites, the background gradient, and all 4 GBA layers
- Level main/midway entrance editing
- Message editing (including standard messages, level names, file select, story intro, ending, credits)
- Viewers for palettes, 8x8 tiles, and layer 1 16x16 tiles
- Customizing sprite tileset and music in each sublevel
- Inserting 16x16 tiles as objects
- Exporting/importing sublevels, entrances, and messages (using Advynia-format .a3l files), including SNES-GBA porting
- Exporting/importing graphics and tilemaps to .bin files
- Internal name editing
- Various conveniences:
    - detailed tooltip descriptions for many objects/sprites
    - shading to show which screens can be accessed in-game
    - button to count the current sublevel's red coins/flowers
    - warning if items may vanish due to an item memory glitch, manually and when saving

## How to run
If running a prebuilt release (<https://github.com/KarisaAdvynia/Advynia/releases>):
- Download and run Advynia.exe (Windows)<!-- or Advynia.app (Mac)-->, no installation needed.

If running from source:
- Install Python from <https://www.python.org/> (requires Python 3.10 or later)
- Install PyQt6 from the command line with pip. This varies by operating system, but should be a variation of `pip install pyqt6`.
    - On Windows 10: `py -m pip install pyqt6`
    - On Mac: `pip3 install pyqt6`
- Run Advynia.py
    - Your computer may have multiple versions of Python installed; make sure it opens in Python 3.10+ by default

Advynia should run natively on any platform that supports Python 3.10+ and PyQt6, including Windows, Mac, and Linux.

## Settings
Settings are stored in Advynia.cfg in the app folder, and can be modified manually while Advynia is closed.
<!-- - Note: In the Mac build, Advynia.app/Contents/MacOS/ is treated as the app folder, as opposed to the folder containing Advynia.app. This is unintentional.-->

To reset a setting to default, delete the line corresponding to that setting; it will be restored the next time Advynia is opened. To reset all settings, delete the entire file.

If upgrading from 0.3+, or using Advynia on a different platform, copy Advynia.cfg to the new app folder to keep your settings.

## Recovery
Advynia automatically exports each sublevel to /recovery/\<ROMfilename\> when saving, along with the previous version of the ROM (before the most recent save). This may be useful in case of data corruption.
