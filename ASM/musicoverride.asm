; Music Override
;
; Allows customizing the music ID and enabling/disabling pause menu items in 
; every sublevel.

.gba
.open "sma3test.gba", "sma3test-music.gba", 0x08000000

.org 0x0802C2D6
bl @MusicPatch

.org 0x081C1F2A         ; use space from vanilla sublevel 00 main data
@MusicPatch:
    ldr r2,=0x03004BB6
    ldrb r0,[r2]        ; header music ID
    mov r1,0x0E
    cmp r0,r1
    bhs @@MusicOverride

    ; replaced vanilla code
    ldr r2,=0x03007240
    ldr r3,[r2]
    bx lr

    @@MusicOverride:
    bic r0,r1           ; clear 0x0E bits
    ldr r2,=0x030048B8
    strb r0,[r2]        ; use lowest bit of header music as items-disabled flag

    ldr r2,=0x03004CB8
    ldrh r2,[r2]        ; sublevel ID
    ldr r3,=@MusicTable
    ldrb r0,[r3,r2]     ; load music ID, indexed by sublevel ID
    
;    mov r1,0xFF         ;\
;    cmp r0,r1           ;| if music ID is FF...
;    bne @@skip          ;/
;    ;;; should stop the music here
;    @@skip:

    bl 0x812C3B4        ; change music to input r0
    
    pop {r4-r6,pc}      ; skip vanilla subroutine by cloning its return

    .pool

.org 0x081C2000
@MusicTable:
    .fill 0x100,0xFF    ; initialize table to invalid ID

.close