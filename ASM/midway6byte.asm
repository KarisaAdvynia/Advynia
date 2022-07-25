; 6-byte Midway Entrances
;
; Allows manually specifying the camera bytes in each midway entrance.
; The bytes can still be left as 00 to save/load them with the checkpoint, as
; in vanilla.

.gba
.open "sma3test.gba", "sma3test-6bytemidway.gba", 0x08000000

.org 0x08002ED4
.area @AreaEnd-org()
    ; start: r0: checkpoint ID, r1: pointer to pointer to midway entrance
    ; r3 needs to remain intact, r0 r1 r2 r4 r5 do not
    lsl r4,r0,0x1       ;\
    lsl r0,r0,0x2       ;| multiply checkpoint ID by 6
    add r0,r0,r4        ;/
    ldr r1,[r1]         ; pointer to midway entrance
    add r1,r1,r0        ; offset with checkpoint ID *6
    ldr r0,[0x08002FF4] ; 0x0201B000: screen exit for screen 00
    ldrh r2,[r1]        ;\ copy bytes 0-1,
    strh r2,[r0]        ;/  allowing for 6-byte entrances to be halfword-aligned
    ldrh r2,[r1,0x2]    ;\ copy bytes 2-3
    strh r2,[r0,0x2]    ;/
    ldrh r2,[r1,0x4]    ; load bytes 4-5
    cmp r2,0x0
    beq @LoadVanilla
    strh r2,[r0,0x4]    ; store bytes 4-5
    b @AreaEnd

    @LoadVanilla:       ; if both bytes are 0, load stored bytes from checkpoint
    ldr r2,[0x08003000] ; 0x0202BE84: stored byte 4
    ldrb r1,[r2]        ;\ copy stored byte 4 from 0202BE84
    strb r1,[r0,0x4]    ;/
    ldrb r1,[r2,0x4]    ;\ copy stored byte 5 from 0202BE88
    strb r1,[r0,0x5]    ;/
    b @AreaEnd

    .fill @AreaEnd-org()
.endarea
.org 0x08002F06
@AreaEnd:

.close