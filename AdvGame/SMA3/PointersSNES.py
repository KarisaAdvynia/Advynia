"""SNES YI Pointers
Locations of SMW2:YI (V1.0 U) data pointers, used for extracting data from the
SNES version."""

from AdvGame.AdvGame import PtrRef

### Movable pointers, so that the code can still find the data if it's been
###  moved to another location

sublevelptrs = PtrRef(0x01B08F, 0x10DA6F, vdest=0x17F7C3)  # pointer table

entrancemainoffsets = PtrRef(0x01AFF4, 0x10DA5C, 0x17A89B, vdest=0x17F3E7)
entrancemaintable = PtrRef(0x01B015, 0x10DA61, vdest=0x17F471)
entrancemidwaybank = PtrRef(0x01E657, vdest=0x17)
entrancemidwayoffsets = PtrRef(0x01E66A, vdest=0xF551)
entrancemidwaytable = PtrRef(0x01E677, vdest=0xF5DB)

text = {
    "Level name": 0x5149BC,
    "Standard message": 0x5110DB,
    "Story intro": PtrRef(0x0FCC8F, 0x0FCCF9, vdest=0x0FCD56),
    "Ending": PtrRef(0x0DF3D3, vdest=0x0DF3E8),
    }
