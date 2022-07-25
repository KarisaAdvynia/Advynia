; Object 65: Arbitrary Single Tile
;
; Adds a 7-byte custom object that can generate a rectangle of any specified 
; 16x16 tile ID.

.gba
.open "sma3test.gba", "sma3test-obj65.gba", 0x08000000

.org 0x0816828C + 0x65*4
    .word @Object65Init+1

.org 0x08168AAC + 0x65*4
    .word @Object65Main+1

.org 0x081C19D8 + 0x65
    .byte 0x06          ; set to 5-byte object (02), with signal flag,
                        ;  so Advynia loads it as 7-byte

.org 0x081C1FC0         ; use space from vanilla sublevel 00 main data
@Object65Init:
    push {r4-r5,lr}
    ldrh r3,[r0,0x36]   ; offset of next object to process, if this were 5 bytes
    ldr r4,=0x03004D14
    ldr r4,[r4]         ; pointer to sublevel main data
    ldrb r5,[r4,r3]     ; load low byte of 2-byte extension
    add r3,1            ;  (can't load halfword due to alignment risk)
    ldrb r4,[r4,r3]     ; load high byte of 2-byte extension
    add r3,1
    strh r3,[r0,0x36]   ; add 2 to offset, to account for 7-byte object

    lsl r4,r4,0x8       ;\
    orr r4,r5           ;/ combine high and low bytes
    strh r4,[r0,0x3A]   ; store tile ID to scratch RAM
    bl 0x0801A070       ; Object processing main, slope=0, no relative Y threshold
    pop {r4-r5,pc}

@Object65Main:
    ldrh r2,[r0,0x3A]   ; retrieve tile ID from scratch RAM
    add r0,0x4A
    ldrh r0,[r0]        ; offset to layer 1 tilemap
    ldr r1,=0x03007010  ; Layer 1 tilemap EWRAM (0200000C)
    ldr r1,[r1]
    strh r2,[r1,r0]     ; update tilemap
    bx lr

.pool
  
.close