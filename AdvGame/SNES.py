"""SNES General
Classes and functions for reading/writing SNES ROMs."""

# standard library imports
import os

# import from other files
from . import AdvGame

class Open(AdvGame.Open):
    "Wrapper for Python's open() function, for reading SNES ROM images."
    def __init__(self, filepath, *args, **kwargs):
        "Account for the presence or absence of the SMC header."
        super().__init__(filepath, *args, **kwargs)
        self.SMCheader = hasSMCheader(filepath)

    def seek(self, ptr):
        """Seek to a 24-bit SNES ROM pointer. Only the SuperFX ROM mapping is
        supported."""
        bank, addr16 = (ptr // 0x10000) & 0x7F, ptr & 0xFFFF

        if bank < 0x40 and addr16 >= 0x8000:  # LoROM region
            fileaddr = (bank - 1) * 0x8000 + addr16
        elif 0x40 <= bank < 0x60:  # HiROM region
            fileaddr = (bank - 0x40) * 0x10000 + addr16
        else:
            raise ValueError("Address " + format(ptr, "06X") +
                             " is not a valid SNES SuperFX ROM pointer.")
        if self.SMCheader:
            fileaddr += 0x200
        self.fileobj.seek(fileaddr)

def hasSMCheader(filepath):
    size = os.path.getsize(filepath)
    if size % 0x8000 == 0x200:
        return True
    elif size % 0x8000 == 0:
        return False
    else:
        raise ValueError
