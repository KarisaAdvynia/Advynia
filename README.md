# Advynia
An editor for Yoshi's Island: Super Mario Advance 3.

Aiming to be a streamlined editor experience, providing what's needed for creating custom Yoshi's Island levels, with no in-depth ROM hacking knowledge required. Work in progress.

## Features, as of 0.2
- Sublevel editing, with visuals for about 80% of objects, most sprites, background gradient, layer 2/3
- Level main/midway entrance editing
- Viewers for palettes, 8x8 tiles, and layer 1 16x16 tiles
- Customizing sprite tileset and music in each sublevel
- Inserting 16x16 tiles as objects
- Exporting/importing sublevels to Advynia-format .a3l files, including one-way SNES-GBA importing (using .a3l or .ylt files)
- Exporting graphics and compressed data (note: only exporting is currently supported, not importing)
- Internal name editing
- Various conveniences:
    - detailed tooltip descriptions for many object/sprites
    - shading to show which screens can be accessed in-game
    - button to count the current sublevel's red coins/flowers
    - warning if items may vanish due to an item memory glitch, manually and when saving

## How to run
If running a prebuilt release (<https://github.com/KarisaAdvynia/Advynia/releases>):
- Download and run Advynia.exe (Windows) or Advynia.app (Mac), no installation needed.

If running from source:
- Install Python from <https://www.python.org/> (requires Python 3.10 or later)
- Install PyQt6 from the command line with pip. This varies by operating system, but should be a variation of `pip install pyqt6`.
    - On Windows 10: `py -m pip install pyqt6`
- Run Advynia.py
    - Your computer may have multiple versions of Python installed; make sure it opens in Python 3.10+ by default

Advynia should run natively on any platform that supports Python/PyQt, but only the Windows layout is currently supported. It's functional on Mac, but looks awkward in the default Qt Mac theme; this is planned to be improved later.
