; World 6 Tileset Flag
;
; Adds a high digit to the layer 1 tileset, allowing for IDs > 0xF.

.gba
.open "sma3test.gba", "sma3test-w6.gba", 0x08000000

.org 0x08013480
.area @AreaEnd-org()
    ; r0-r6 are all free to use
    ; r4 is expected to end with world ID, r6 with tileset*3, but those are skipped
    ldr r0,=0x03004B9E
    ldrh r1,[r0]        ; layer 1 tileset
    ldr r0,=0x03004CB8
    ldrh r0,[r0]        ; sublevel ID
    ldr r2,=@HighDigitTable
    ldrb r2,[r2,r0]     ; tileset high digit
    lsl r2,r2,0x4       ; tileset high digit *0x10
    orr r1,r2           ; r1 = tileset ID, with high digit

    lsl r0,r1,0x3       ;\
    lsl r1,r1,0x2       ;| multiply tileset by 0xC
    add r1,r0,r1        ;/
    ldr r0,=0x08165C44  ; pointer table to layer 1 graphics
    add r5,r1,r0        ; r5 = start of 3 pointers for current tileset's graphics
    
    ldr r0,[r5]
    ldr r0,[r0]         ; load from pointer twice
    ldr r1,=0x06002000  ; VRAM destination
    bl 0x0812F6CC       ; LZ77 decompress (VRAM)
    ldr r0,[r5,0x4]
    ldr r0,[r0]         ; load from pointer twice
    ldr r1,=0x06003000  ; VRAM destination
    bl 0x0812F6CC       ; LZ77 decompress (VRAM)
    ldr r0,[r5,0x8]
    ldr r0,[r0]         ; load from pointer twice
    ldr r1,=0x06000000  ; VRAM destination
    bl 0x0812F6CC       ; LZ77 decompress (VRAM)

    b @AreaEnd
    
    .pool
    .fill @AreaEnd-org()
.endarea
.org 0x080134E8
@AreaEnd:

.org 0x08013510
    b 0x080135B2        ; skip remaining world 6 tileset checks
    
.org 0x08013882
    b 0x80138C0         ; skip world 6 palette checks

.org 0x081C2354         ; use space from vanilla sublevel 00/3A sprite data
@HighDigitTable:
    .fill 0x100
.org @HighDigitTable+0x2D :: .byte 1   ; set flags for vanilla 6-1/6-6 sublevels
.org @HighDigitTable+0x32 :: .byte 1
.org @HighDigitTable+0x64 :: .byte 1
.org @HighDigitTable+0x69 :: .byte 1
.org @HighDigitTable+0x90 :: .byte 1
.org @HighDigitTable+0x95 :: .byte 1
.org @HighDigitTable+0xB5 :: .byte 1

.close