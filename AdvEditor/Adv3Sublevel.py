"Functions for loading and evaluating the current sublevel."

# standard library imports
import os, traceback
from collections import defaultdict

# import from other files
import AdvMetadata, AdvEditor.ROM
from AdvEditor import (AdvFile, AdvSettings, AdvWindow,
                       Adv3Attr, Adv3Save, Adv3Patch, Adv3Visual)
from AdvGame import SMA3
from AdvGUI.PyQtImport import QFileDialog
from AdvGUI.Dialogs import QSimpleDialog, QDialogImportPatch, QDialogSaveWarning
from AdvGUI import QtAdvFunc

oldglobals = frozenset(globals())

def loadsublevel(sublevel):
    "Load a sublevel from an SMA3.Sublevel object."

    if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

    try:
        Adv3Attr.sublevel = sublevel
        if not sublevel.fromfile:
            Adv3Patch.loadsublevelpatchattr(sublevel)
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
            QSimpleDialog(AdvWindow.editor, title="Warning", text="".join(
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
    success = Adv3Save.saveSublevelToROM(Adv3Attr.sublevel, Adv3Attr.sublevel.ID)
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

def importsublevel():
    "Load a sublevel from a separate file."

    filepath, _ = QFileDialog.getOpenFileName(
        AdvWindow.editor, caption="Import Sublevel",
        directory=os.path.dirname(Adv3Attr.filepath),
        filter=";;".join((
            "All supported files (*.a3l *.ylt)",
            AdvMetadata.export3ext,
            "SNES YI Level Tool file (*.ylt)")))
    if filepath:
        _, ext = os.path.splitext(filepath)

        warnSNES = False

        if ext.lower() == ".a3l":
            data = AdvFile.A3LFileData.importfromfile(filepath)
            if data.version > AdvMetadata.version:
                QSimpleDialog(AdvWindow.editor, title="Warning", text="".join((
                    "This sublevel was created in Advynia ", str(version),
                    ". You are using version ", str(AdvMetadata.version),
                    "."
                    ))).exec()

            sublevel = data.tosublevel()
            if 0x95 in data:
                warnSNES = True

            # check for patches that aren't applied to current ROM
            newpatches = []
            if not Adv3Attr.world6flag and 0x06 in data:
                newpatches.append("world6flag")
            if not Adv3Attr.musicoverride and sublevel.music:
                newpatches.append("musicoverride")
            if not Adv3Attr.sublevelstripes and sublevel.stripeIDs:
                if sublevel.stripeIDs != SMA3.loadstripeIDs(
                        Adv3Attr.filepath, sublevel.header[7]):
                    newpatches.append("sublevelstripes")
            if not Adv3Attr.object65 and 0x65 in data:
                newpatches.append("object65")
            if newpatches:
                if AdvSettings.warn_patch_all:
                    # load warning dialog
                    if not QDialogImportPatch(newpatches, sublevel).exec():
                        return
                else:
                    Adv3Patch.applymultiplepatches(newpatches)

            loadsublevel(sublevel)

            AdvWindow.statusbar.setActionText("".join((
                "Imported sublevel ", format(Adv3Attr.sublevel.ID, "02X"),
                " from ", filepath)))

        elif ext.lower() == ".ylt":
            warnSNES = True
            sublevel = SMA3.SublevelFromSNES()
            sublevel.fromfile = True
            with open(filepath, "rb") as f:
                sublevel.ID = f.read(1)[0]
                sublevel.importmaindata(f)
                sublevel.importspritedata(f)
            loadsublevel(sublevel)

            AdvWindow.statusbar.setActionText("".join((
                "Imported sublevel ", format(Adv3Attr.sublevel.ID, "02X"),
                " from ", filepath)))

        if warnSNES and AdvSettings.warn_import_SNES:
            QSimpleDialog(AdvWindow.editor, title="Warning", text="".join((
                "This sublevel was created on the SNES version. The "
                "entrance camera bytes will need to be set manually, and "
                "level design may need to be tweaked for the GBA screen "
                "size."
                ))).exec()

def exportsublevel_action():
    """Called from the main window's export sublevel action. Prompts the user
    for an export filepath, then exports the current sublevel if valid."""

    # generate default filepath
    defaultpath = os.path.join(
        os.path.dirname(Adv3Attr.filepath),
        AdvFile.sublevelfilename(Adv3Attr.filename, Adv3Attr.sublevel.ID))

    # get filepath from user
    filepath, _ = QFileDialog.getSaveFileName(
        AdvWindow.editor, caption="Export Sublevel",
        filter=AdvMetadata.export3ext, directory=defaultpath)

    # export to filepath
    if filepath:
        exportsublevel(filepath)

def exportsublevel(filepath):
    "Export the current sublevel to the given filepath."
    data = AdvFile.A3LFileData.fromsublevel(Adv3Attr.sublevel)
    if not Adv3Attr.sublevelstripes:
        # include stripe data even if the patch isn't applied
        data[5] = Adv3Visual.spritegraphics.stripeIDs
    data.exporttofile(filepath)
    AdvWindow.statusbar.setActionText("Exported sublevel to " + filepath)

def exportallsublevels():
    outputdir = QFileDialog.getExistingDirectory(
        AdvWindow.editor, caption="Export All Sublevels",
        directory=os.path.dirname(Adv3Attr.filepath))

    if outputdir:
        AdvFile.exportallYIsublevels(Adv3Attr.filepath, outputdir)
        AdvWindow.statusbar.setActionText(
            "Exported all sublevels to " + outputdir)

def exportSNESsublevels():
    filepath, _ = QFileDialog.getOpenFileName(
        AdvWindow.editor, caption="Open SNES ROM",
        directory=os.path.dirname(Adv3Attr.filepath),
        filter="SNES ROM Image (*.sfc, *.smc)")
    if not filepath:
        return

    outputdir = QFileDialog.getExistingDirectory(
        AdvWindow.editor, caption="Extract SNES Sublevels",
        directory=os.path.dirname(filepath))
    if outputdir:
        AdvFile.exportallYIsublevels(filepath, outputdir, console="SNES")
        AdvWindow.statusbar.setActionText(
            "Extracted all sublevels from " + os.path.basename(filepath))

def countitems():
    redcoins = 0
    flowers = 0
    for row in AdvWindow.sublevelscene.layer1.tilemap:
        for tileID in row:
            if tileID in (0x6001, 0xA400, 0x10E16) or tileID>>8 == 0xA3:
                # red coin tile or in poundable post
                redcoins += 1
    for spr in Adv3Attr.sublevel.sprites:
        if spr.ID in (0x065, 0x022, 0x068, 0x05B):
            # stationary sprite, flashing egg, flashing egg block,
            #  Bandit with red coin
            redcoins += 1
        elif spr.ID in (0x0FA, 0x110, 0x0B8):
            # flower, tileset-specific flower, ? cloud with flower
            flowers += 1
        elif spr.ID == 0x12C and not spr.x&1:
            # Fly Guy with red coin, back and forth
            redcoins += 1
        elif spr.ID == 0x08D and spr.parity() == 1:
            # Fly Guy with red coin, timed
            redcoins += 1
        elif spr.ID == 0x067 and spr.parity() == 2:
            # Chomp Rock ? cloud with flower
            flowers += 1
        elif spr.ID == 0x161:
            # reward for killing all enemies
            if spr.parity() == 0:
                redcoins += 1
            elif spr.parity() == 2:
                flowers += 1

    text = "Red coins: {redcoins}<br>Flowers: {flowers}"
    QSimpleDialog(AdvWindow.editor, title="Count Items",
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
        QSimpleDialog(AdvWindow.editor, title="Item Memory Check",
            text="No item memory errors detected.").exec()

def _itemmemorycolcheck(tilemap, x, startY, colstatus=0):
    for y in range(startY, startY+0x10):
        tileID = tilemap[y][x]
        if tileID in (0x6001, 0x10E16) or tileID>>8 == 0xA3:
            # red coin tile or in poundable post: high priority
            if colstatus:
                return False
            colstatus = 2
        elif tileID in (0x6000, 0x7400):
            # normal coins only conflict with high priority
            if colstatus >= 2:
                return False
            colstatus = 1
    return True

def _itemmemoryerror(screen, x):
    text = """Items in the same column detected on screen {screen} at x={x}.
If one item is collected, any others may vanish!"""
    QSimpleDialog(AdvWindow.editor, title="Item Memory Check", text=text.format(
        screen=format(screen, "02X"), x=format(x, "02X"))).exec()

# import only newly defined functions using import *
__all__ = [name for name in (frozenset(globals()) - oldglobals)
           if name[0] != "_"]
