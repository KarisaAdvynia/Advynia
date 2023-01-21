"Functions for loading and evaluating the current sublevel."

# standard library imports
import copy, traceback
from collections import defaultdict

# import from other files
import AdvMetadata, AdvEditor.ROM
from AdvEditor import (AdvSettings, AdvWindow,
                       Adv3Attr, Adv3Save, Adv3Patch, Adv3Visual)
from AdvGame import GBA, SMA3
from AdvGUI.Dialogs import (QSimpleDialog, QDialogLoadValidation,
                            QDialogSaveWarning)
from AdvGUI import QtAdvFunc

def loadsublevel(sublevel):
    "Load a sublevel from an SMA3.Sublevel object."

    if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

    # if SublevelFromSNES, copy to base class to ensure correct methods
    if isinstance(sublevel, SMA3.SublevelFromSNES):
        sublevel = copy.deepcopy(sublevel)
        sublevel.__class__ = SMA3.Sublevel

    try:
        Adv3Attr.sublevel = sublevel
        if not sublevel.fromfile:
            Adv3Patch.loadsublevelpatchattr(sublevel)
        if not sublevel.stripeIDs:
            Adv3Visual.updatestripesfromsublevel()
        Adv3Visual.loadpalette(sublevel)
        Adv3Visual.loadgraphics(sublevel)

        AdvWindow.editor.reload("All")

    except Exception as err:
        text = ("Error loading sublevel.\n"
            "This sublevel appears to be corrupt. If you're getting this "
            "error from normal Advynia usage, please report this as a bug. "
            "Uploading your hack as a patch is recommended to help debug "
            "the error."
            "\n\n" + traceback.format_exc())
        traceback.print_exc()
        QSimpleDialog(AdvWindow.editor, text=text).exec()
        return

    # reset undo history, reinit with new sublevel as first state
    AdvWindow.undohistory.reset(sublevel)
    if not sublevel.fromfile:
        AdvWindow.undohistory.updatelastsave()

    # window title and status bar
    if sublevel.ID is not None:
        if sublevel.datablocks:
            actiontext = ("Loaded sublevel {sublevelID}: main data from "
            "{mainptr}, sprite data from {spriteptr}.")
            AdvWindow.statusbar.setActionText(actiontext.format(
                sublevelID=format(sublevel.ID, "02X"),
                mainptr=format(sublevel.datablocks["main"][0], "08X"),
                spriteptr=format(sublevel.datablocks["sprite"][0], "08X")))
    AdvWindow.editor.updatewindowtitle()
    AdvWindow.statusbar.updateByteText()

    if AdvMetadata.printtime: print("Total sublevel load:",
        QtAdvFunc.timerend(timer), "ms")  # debug

    if sublevel.ID == 0x38:
        QSimpleDialog(AdvWindow.editor, text="Sublevel 38 is used by the intro "
            "cutscene. The header is unused, and "
            "editing this may result in unexpected in-game behavior.",
            title="Warning").exec()
    if sublevel.header[9] == 9:
        QSimpleDialog(AdvWindow.editor, text="This is the Raphael arena. "
            "Editing this may result in unexpected in-game behavior.",
            title="Warning").exec()
    elif sublevel.header[9] == 0xD:
        QSimpleDialog(AdvWindow.editor, text="This is the Froggy arena. "
            "Editing this may result in unexpected in-game behavior.",
            title="Warning").exec()
    return True

def loadsublevelID(sublevelID):
    "Load a sublevel from the ROM."
    if not AdvEditor.ROM.exists(): return
    return loadsublevel(SMA3.Sublevel.importbyID(Adv3Attr.filepath, sublevelID))

def savesublevel_action():
    """Called from the main window's save sublevel action, and when confirming
    Save As. Handles other checks before saving."""

    # check for screen count
    if AdvSettings.warn_save_screencount:
        screencount = AdvWindow.sublevelscene.layer1.tilemap.screencount()
        if screencount >= 0x40:
            QSimpleDialog(AdvWindow.editor, title="Warning",
                          dontshow="warn_save_screencount",
                          text="".join(
                ("The current sublevel uses ", format(screencount, "02X"),
                 " screens. If a sublevel uses more than 3F screens, it "
                 "will freeze the game on the loading screen!\n"
                 "If this sublevel loads in-game, please report this-- "
                 "there may be an error with how Advynia simulates object "
                 "screen memory allocation."
                          ))).exec()

    # check for item memory errors
    if AdvSettings.warn_save_itemmemory:
        itemmemorycheck(dialog_on_pass=False)

    # save
    success = Adv3Save.savesubleveltoROM(Adv3Attr.sublevel, Adv3Attr.sublevel.ID)
    if success:
        AdvWindow.undohistory.updatelastsave()
    return success

def savecheck():
    if AdvSettings.warn_unsaved and not AdvWindow.undohistory.issaved():
        result = QDialogSaveWarning(AdvWindow.editor).exec()
        # 1=Save, 2=Don't Save, 0=Cancel
        if result == 0:
            return False
        if result == 1:
            if not savesublevel_action():
                return False
    return True

def cmpheader(newheader):
    """Given a header that may differ from the current sublevel's header,
    return a mapping containing the header values to update."""
    toupdate = {}
    for i, (new, old) in enumerate(zip(
            newheader, Adv3Attr.sublevel.header, strict=True)):
        if new != old:
            toupdate[i] = new
    return toupdate

def countitems():
    redcoins = 0
    flowers = 0
    for row in AdvWindow.sublevelscene.layer1.tilemap:
        for tileID in row:
            if tileID in (0x6001, 0xA400, 0x10E16) or tileID>>8 == 0xA3:
                # red coin tile or in poundable post
                redcoins += 1
    for spr in Adv3Attr.sublevel.sprites:
        match spr.ID:
            case 0x065 | 0x022 | 0x068 | 0x05B:
                # stationary sprite, flashing egg, flashing egg block,
                #  Bandit with red coin
                redcoins += 1
            case 0x0FA | 0x110 | 0x0B8:
                # flower, tileset-specific flower, ? cloud with flower
                flowers += 1
            case 0x12C:
                if not spr.x&1:
                    # Fly Guy with red coin, back and forth
                    redcoins += 1
            case 0x08D:
                if spr.parity() == 1:
                    # Fly Guy with red coin, timed
                    redcoins += 1
            case 0x067:
                if spr.parity() == 2:
                    # Chomp Rock ? cloud with flower
                    flowers += 1
            case 0x161:
                # reward for killing all enemies
                if spr.parity() == 0:
                    redcoins += 1
                elif spr.parity() == 2:
                    flowers += 1

    text = "Red coins: {redcoins}<br>Flowers: {flowers}"
    QSimpleDialog(AdvWindow.editor, title="Count Items", wordwrap=False,
        text=text.format(redcoins=redcoins, flowers=flowers)).exec()

def itemmemorycheck(*, dialog_on_pass=True):
    # check for sprite conflicts, and track any item memory sprites
    sprcolstatus = defaultdict(int)
    for spr in Adv3Attr.sublevel.sprites:
        itemattr = SMA3.SpriteMetadata[(spr.ID, spr.parity())].itemmemory
        if spr.ID == 0x0B6:
            # if ring of 8 coins: activate 5 nearby columns, low priority
            for x in (spr.x-2, spr.x-1, spr.x+1, spr.x+2, spr.x+3):
                if not 0 <= x < SMA3.Constants.maxtileX:
                    continue
                screen = SMA3.coordstoscreen(x, spr.y)
                if sprcolstatus[(screen, x)] >= 2:
                    _itemmemoryerror(screen, x)
                    return
                sprcolstatus[(screen, x)] = 1
            itemattr = 2
        if itemattr:
            # sprite uses item memory
            screen = SMA3.coordstoscreen(spr.x, spr.y)
            if itemattr + sprcolstatus[(screen, spr.x)] >= 3:
                _itemmemoryerror(screen, spr.x)
                return
            sprcolstatus[(screen, spr.x)] = itemattr

    # check for tile conflicts
    tilemap = AdvWindow.sublevelscene.layer1.tilemap
    for screen in range(SMA3.Constants.maxscreen + 1):
        startX, startY = SMA3.screentocoords(screen)
        for x in range(startX, startX+0x10):
            if not _itemmemorycolcheck(
                    tilemap, x, startY, sprcolstatus[(screen, x)]):
                _itemmemoryerror(screen, x)
                return

    if dialog_on_pass:
        QSimpleDialog(AdvWindow.editor, title="Item Memory Check", wordwrap=False,
            text="No item memory errors detected.").exec()

def _itemmemorycolcheck(tilemap, x, startY, colstatus=0):
    for y in range(startY, startY+0x10):
        tileID = tilemap[y][x]
        if tileID in (0x6001, 0x10E16) or tileID>>8 == 0xA3:
            # red coin tile or in poundable post: high priority
            if colstatus:
                return False
            colstatus = 2
        elif tileID in (0x6000, 0x7400, 0xA400):
            # normal coins only conflict with high-priority items
            # green red coins aren't objects, so they're also low priority
            if colstatus >= 2:
                return False
            colstatus = 1
    return True

def _itemmemoryerror(screen, x):
    text = """Items in the same column detected on screen {screen} at x={x}.
If one item is collected, any others may vanish!"""
    QSimpleDialog(AdvWindow.editor, title="Item Memory Check", wordwrap=False,
                  text=text.format(
        screen=format(screen, "02X"), x=format(x, "02X"))).exec()
