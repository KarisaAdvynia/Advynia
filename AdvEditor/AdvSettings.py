"""Advynia Settings
Contains global settings, and handles reading/writing the .cfg file."""

# standard library imports
import ast, os, sys

# import from other files
import AdvMetadata, AdvEditor.Number

_settingspath = os.path.join(AdvMetadata.appdir, "Advynia.cfg")

class Settings:
    # All non-setting attributes/methods start with _ to avoid conflicting with
    #  setting attributes

    _enablecfgwrite = False

    _defaults = {
        "click_insert":[[1, 67108864], [2, 0]],  # control+click, right-click
        "click_selectdrag":[[1, 0]],  # click
        "click_selectmulti":[[1, 33554432]],  # shift+click
        "editor_lastversion":(0, 0, 0),
        "extprefix":"Ex",
        "mouse_resizeradius":3,
        "ROM_autoload":True,
        "ROM_recent":[],
        "ROM_recent_max":10,
        "text_imageoffbyone":True,
        "text_simplified":False,
        "undo_max":500,
        "visual_dimscreens":1,
        "visual_redcoins":True,
        "visual_zoom":100,
        "warn_import_SNES":True,
        "warn_patch_all":True,
        "warn_save_first":True,
        "warn_save_itemmemory":True,
        "warn_save_screencount":True,
        "warn_unsaved":True,
        "window_sidebarpos":1,
        "window_SMA3Editor": (64, 64, 0x400, 0x280),
    }
    from AdvEditor.PatchData import patches as _patches
    for _patchkey in _patches:
        _defaults["warn_patch_" + _patchkey] = True

    _mouseinputs = tuple(_key for _key in _defaults
                         if _key.startswith("mouseinput"))

    _keylen = 1 + max(len(i) for i in _defaults.keys())

    def _validate(self):
        """Ensure settings are valid, in ways that aren't detected by the type
        checker."""
        for key in self._mouseinputs:
            for seq in self._defaults[key]:
                if not isinstance(seq, list) or len(seq) != 2:
                    self._resetsetting(key)
                for item in seq:
                    if not isinstance(item, int):
                        self._resetsetting(key)
        for path in self.ROM_recent:
            if not isinstance(path, str) or not os.path.exists(path):
                self.ROM_recent.remove(path)
        self._capsetting("ROM_recent_max", 0, 100)
        if self.undo_max < 0:
            self.undo_max = 0
        if not 0 <= self.visual_dimscreens < 3:
            self._resetsetting("visual_dimscreens")
        self._capsetting("visual_zoom", 10, 600)

    def __init__(self):
        # load defaults for saved settings
        for key, value in self._defaults.items():
            setattr(self, key, value)

        if not os.path.exists(_settingspath):
            # create new settings file
            self._enablecfgwrite = True
            self._writecfg()
        with open(_settingspath, "r", encoding="UTF-8") as f:
            # import settings from file
            importcount = 0
            for line in f:
                if self._importcfgline(line):
                    importcount += 1
            self._validate()

            self._enablecfgwrite = True
            if importcount < len(self._defaults):
                # overwrite file if not all settings were imported
                self._writecfg()

    def _importcfgline(self, line):
        "Import one setting line from the .cfg file."
        try:
            if not line:
                return
            key, valuestr = (part.strip() for part in line.split("="))
            if hasattr(self, key):
                # load only if settings key exists, and read value is same type
                value = ast.literal_eval(valuestr)
                if not isinstance(value, type(getattr(self, key))):
                    return False
                setattr(self, key, value)
                return True
            return False
        except Exception:
            # ignore line if any errors
            return False

    def _writecfg(self):
        "Write the current settings to the .cfg file."
        if not self._enablecfgwrite:
            return
        output = []
        for key in sorted(self._defaults, key=str.casefold):
            # case-insensitive sort
            output += [key.ljust(self._keylen), "= ", repr(getattr(self, key)),
                       "\n"]
        with open(_settingspath, "w", encoding="UTF-8") as f:
            f.write("".join(output))

    def __setattr__(self, key, value):
        if key[0] != "_" and key not in self._defaults:
            # keys that don't start with underscore should match a setting
            raise AttributeError(
                "'" + key + "' is not a valid Advynia setting.")
        object.__setattr__(self, key, value)
        if self._enablecfgwrite and key in self._defaults:
            # also save to file
            self._writecfg()

    def _capsetting(self, key, minvalue, maxvalue):
        "Ensure an int setting is within a valid range."
        value = getattr(self, key)
        newvalue = AdvEditor.Number.capvalue(value, minvalue, maxvalue)
        if newvalue != value: setattr(self, key, newvalue)

    def _resetsetting(self, key):
        "Reset a setting to default."
        setattr(self, key, self._defaults[key])

    def _ROM_recent_add(self, newpath):
        "Add another file path to self.ROM_recent."
        if newpath in self.ROM_recent:
            self.ROM_recent.remove(newpath)
        self.ROM_recent.insert(0, newpath)
        if len(self.ROM_recent) > self.ROM_recent_max:
            del self.ROM_recent[self.ROM_recent_max:]

sys.modules[__name__] = Settings()
