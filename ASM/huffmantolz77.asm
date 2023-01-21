; Huffman to LZ77 Compression
;
; Converts Huffman decompression subroutine calls to LZ77. Only 7 compressed
; data blocks in SMA3 use Huffman compression, and they compress more
; efficiently as LZ77; this allows Advynia to consistently insert graphics using
; a single compression format.

.gba
.open "sma3test.gba", "sma3test-huffmantolz77.gba", 0x08000000

.org 0x0812F6CC
    swi_LZ77_VRAM:

.org 0x081116CA         ; decompress Mario Bros. gameplay layer graphics
    bl swi_LZ77_VRAM
.org 0x081116DE         ; decompress Mario Bros. gameplay sprite graphics
    bl swi_LZ77_VRAM

.org 0x08110C2A         ; decompress Mario Bros. title screen sprite graphics
    bl swi_LZ77_VRAM
.org 0x081186B4         ; decompress Mario Bros. title screen sprite graphics
    bl swi_LZ77_VRAM

.org 0x08112934         ; decompress ??? (082F1968 or 082F1B24 or 082F1D0C)
    bl swi_LZ77_VRAM
.org 0x08112948         ; decompress ??? (082F1F20)
    bl swi_LZ77_VRAM

.close