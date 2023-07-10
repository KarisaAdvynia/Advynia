; Sublevel Sprite Tilesets
;
; A single hex-edit that changes sprite tilesets to be indexed by sublevel ID,
; not header value 7.
;
; This requires both sprite tileset tables (08166044, pointer at 080137A4, and
; 081663C8, pointer at 080137B0) to be expanded from 0x96 to 0xF6 sprite
; tilesets.

.gba
.open "sma3test.gba", "sma3test-stripes.gba", 0x08000000

.org 0x080137A0
.word 0x2AAC

.close