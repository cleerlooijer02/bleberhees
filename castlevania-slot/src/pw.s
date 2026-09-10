; ---------------------------------------------------------------
; Castlevania (NES) - wachtwoordscherm
; Draait in bank 0, ingehaakt op de NMI-aanroep JSR $800A ($C071)
; ---------------------------------------------------------------
.setcpu "6502"
.segment "CODE"

; --- RAM (geverifieerd vrij: $07CF-$07EF)
PWSTATE = $07D0
CURSOR  = $07D1
ENTLEN  = $07D2
ENTRY   = $07D3         ; 7 bytes -> $07D3..$07D9
PREVCUR = $07DA
FLASH   = $07DB
RNG     = $07DC
LASTSONG= $07DD
LASTMODE= $07DE
DUTY1   = $07E2
DUTY2   = $07E3
T0      = $07DF
T1      = $07E0
T2      = $07E1

; --- hardware / spelvariabelen
PPUCTRL = $2000
PPUSTAT = $2002
PPUADDR = $2006
PPUDATA = $2007
MODE    = $18
PHASE19 = $19
TIMER1E = $1E
MASKSH  = $FE
NEWPAD  = $F5

SFX_SELECT  = $14
SFX_ERASE   = $12
SFX_ERROR   = $1C
SOUNDREQ    = $C1A7

TILE_UNDER  = $34
TILE_CURSOR = $39
NCHARS      = 36

; ===============================================================
hook:
        inc RNG                 ; gratis entropie
        lda MODE
        bne @notinit
        lda #0                  ; mode 0 = titel-init -> slot weer op nul
        sta PWSTATE
        jsr reroll              ; en meteen nieuwe klankkleuren
@notinit:
        lda $60                 ; ander muzieknummer? -> opnieuw gooien
        cmp LASTSONG
        beq @ns
        sta LASTSONG
        jsr reroll
@ns:    lda MODE                ; andere spelfase? -> ook opnieuw gooien
        cmp LASTMODE
        beq @nm
        sta LASTMODE
        jsr reroll
@nm:
        lda PWSTATE
        beq hook_exit
        cmp #1
        bne @n1
        jmp st_enter
@n1:    cmp #2
        bne @n2
        jmp st_build
@n2:    cmp #4
        bne @n3
        jmp st_hand
@n3:    jmp st_run

hook_exit:
        jmp $800A               ; alsnog de originele routine draaien

; ===============================================================
; toestand 1: scherm uit zetten
st_enter:
        lda #$00
        sta MASKSH
        sta $0700               ; PPU-wachtrij van het spel legen
        sta $20
        lda #2
        sta PWSTATE
        jmp hook_exit

; ===============================================================
; toestand 2: alles opbouwen (rendering staat uit, dus tijd zat)
st_build:
        lda #$B0
        sta PPUCTRL             ; increment +1, achtergrond uit $1000
        lda PPUSTAT

        ; --- nieuwe lettertekens naar CHR-RAM
        ldx #0
@gl:    lda glyphs,x
        cmp #$FF
        beq @gldone
        pha
        lsr a
        lsr a
        lsr a
        lsr a
        clc
        adc #$10
        sta PPUADDR
        pla
        asl a
        asl a
        asl a
        asl a
        sta PPUADDR
        inx
        ldy #8
@g2:    lda glyphs,x
        sta PPUDATA
        inx
        dey
        bne @g2
        lda #0
        ldy #8
@g3:    sta PPUDATA
        dey
        bne @g3
        jmp @gl
@gldone:

        jsr clear_nt
        jsr set_palette
        jsr draw_static

        lda #0
        sta CURSOR
        sta ENTLEN
        sta PREVCUR
        sta FLASH
        lda #$0A                ; achtergrond aan, sprites uit
        sta MASKSH
        lda #3
        sta PWSTATE
        jmp hook_exit

; ===============================================================
; toestand 3: invoeren
st_run:
        lda #1
        sta PHASE19             ; titelmodus in de wachtstand houden
        lda #$80
        sta TIMER1E
        jsr set_palette

        lda FLASH
        beq @noflash
        dec FLASH
@noflash:
        lda NEWPAD
        sta T0
        bne @havekey
        jmp @nokey
@havekey:
        and #$01                ; rechts
        beq @nR
        ldx CURSOR
        inx
        cpx #NCHARS
        bne @sc1
        ldx #0
@sc1:   stx CURSOR
@nR:    lda T0
        and #$02                ; links
        beq @nL
        ldx CURSOR
        dex
        bpl @sc2
        ldx #NCHARS-1
@sc2:   stx CURSOR
@nL:    lda T0
        and #$04                ; omlaag
        beq @nD
        lda CURSOR
        clc
        adc #9
        cmp #NCHARS
        bcc @sc3
        sbc #NCHARS
@sc3:   sta CURSOR
@nD:    lda T0
        and #$08                ; omhoog
        beq @nU
        lda CURSOR
        sec
        sbc #9
        bpl @sc4
        clc
        adc #NCHARS
@sc4:   sta CURSOR
@nU:    lda T0
        and #$80                ; A = teken plaatsen
        beq @nA
        ldx ENTLEN
        cpx #7
        bcs @nA
        lda CURSOR
        sta ENTRY,x
        inx
        stx ENTLEN
        lda #SFX_SELECT
        jsr SOUNDREQ
@nA:    lda T0
        and #$40                ; B = wissen
        beq @nB
        ldx ENTLEN
        beq @nB
        dex
        stx ENTLEN
        lda #SFX_ERASE
        jsr SOUNDREQ
@nB:    lda T0
        and #$10                ; Start = controleren
        beq @nokey
        jmp check_code

@nokey:
        jsr draw_entry
        jsr draw_cursor
        lda #$0A
        ldx FLASH
        beq @m1
        ora #$01                ; grijstint als foutmelding
@m1:    sta MASKSH
        jmp hook_exit

; ===============================================================
check_code:
        lda ENTLEN
        cmp #7
        bne @bad
        ldx #0
@cc:    lda ENTRY,x
        cmp password,x
        bne @bad
        inx
        cpx #7
        bne @cc
        ; goed -> scherm uit, volgende frame overdragen
        lda #$00
        sta MASKSH
        sta FLASH
        lda #4
        sta PWSTATE
        jmp hook_exit
@bad:
        lda #SFX_ERROR
        jsr SOUNDREQ
        lda #0
        sta ENTLEN
        lda #40
        sta FLASH
        jsr draw_entry
        jsr draw_cursor
        lda #$0B
        sta MASKSH
        jmp hook_exit

; ===============================================================
; hele nametable leeg + attributen op palet 1 (alleen met rendering uit!)
clear_nt:
        lda PPUSTAT
        lda #$20
        sta PPUADDR
        lda #$00
        sta PPUADDR
        ldy #4
        lda #$00
@cl1:   ldx #240
@cl2:   sta PPUDATA
        dex
        bne @cl2
        dey
        bne @cl1
        lda #$55
        ldx #64
@cl3:   sta PPUDATA
        dex
        bne @cl3
        rts

; ===============================================================
; toestand 4: nette overdracht aan het spel
st_hand:
        lda #$00
        sta MASKSH
        lda FLASH
        bne @tick
        jsr clear_nt
        lda #$03
        jsr $C37A
        lda #48
        sta FLASH
        jmp hook_exit
@tick:  dec FLASH
        bne @out
        lda #0
        sta PWSTATE
        lda #$1E
        sta MASKSH
@out:   jmp hook_exit

; ===============================================================
set_palette:
        lda PPUSTAT
        lda #$3F
        sta PPUADDR
        lda #$00
        sta PPUADDR
        ldx #0
@p:     lda paldata,x
        sta PPUDATA
        inx
        cpx #16
        bne @p
        lda #$20                ; adres weer weg bij het palet
        sta PPUADDR
        lda #$00
        sta PPUADDR
        rts

; ===============================================================
draw_static:
        ldx #0
@s0:    lda strings,x
        beq @sdone
        sta PPUADDR
        inx
        lda strings,x
        sta PPUADDR
        inx
        lda strings,x
        sta T0
        inx
@s1:    lda strings,x
        sta PPUDATA
        inx
        dec T0
        bne @s1
        jmp @s0
@sdone:
        ; tekenrooster: 4 rijen van 9, om en om met een lege tegel
        lda #$21
        sta T1
        lda #$87
        sta T2
        ldy #0
        ldx #4
@gr:    lda T1
        sta PPUADDR
        lda T2
        sta PPUADDR
        stx T0
        ldx #9
@gc:    lda chartile,y
        sta PPUDATA
        iny
        dex
        beq @gcend
        lda #$00
        sta PPUDATA
        jmp @gc
@gcend:
        ldx T0
        lda T2
        clc
        adc #$40
        sta T2
        bcc @nc
        inc T1
@nc:    dex
        bne @gr
        rts

; ===============================================================
draw_entry:
        lda #$21
        sta T1
        lda #$0A
        sta T2
        ldx #0
@de:    lda T1
        sta PPUADDR
        lda T2
        sta PPUADDR
        cpx ENTLEN
        bcs @blank
        ldy ENTRY,x
        lda chartile,y
        jmp @put
@blank: lda #TILE_UNDER
@put:   sta PPUDATA
        lda T2
        clc
        adc #2
        sta T2
        inx
        cpx #7
        bne @de
        rts

; ===============================================================
cur_addr:                       ; A = index -> T1/T2 = PPU-adres
        ldy #0
@d9:    cmp #9
        bcc @done9
        sbc #9
        iny
        jmp @d9
@done9: asl a
        clc
        adc #$86
        sta T2
        lda #$21
        sta T1
        cpy #0
        beq @ok
@add:   lda T2
        clc
        adc #$40
        sta T2
        bcc @nc2
        inc T1
@nc2:   dey
        bne @add
@ok:    rts

draw_cursor:
        lda PREVCUR
        jsr cur_addr
        lda T1
        sta PPUADDR
        lda T2
        sta PPUADDR
        lda #$00
        sta PPUDATA
        lda CURSOR
        jsr cur_addr
        lda T1
        sta PPUADDR
        lda T2
        sta PPUADDR
        lda #TILE_CURSOR
        sta PPUDATA
        lda CURSOR
        sta PREVCUR
        rts

; ===============================================================
; --- muziekrandomizer -----------------------------------------
; 8-bits schuifregister voor toevalsgetallen
rand:   lda RNG
        asl a
        bcc @r1
        eor #$1D
@r1:    sta RNG
        rts

; nieuwe golfvorm voor beide pulskanalen
reroll: jsr rand
        and #$C0
        sta DUTY1
        jsr rand
        and #$C0
        sta DUTY2
        rts

; vervangt STA $4000,X in de geluidsengine: dringt bij de twee
; pulskanalen een eigen golfvorm op, de rest gaat ongewijzigd door
duty_write:
        cpx #$00
        beq @p1
        cpx #$04
        beq @p2
        sta $4000,x
        rts
@p1:    pha
        and #$3F
        ora DUTY1
        sta $4000
        pla
        rts
@p2:    pha
        and #$3F
        ora DUTY2
        sta $4004
        pla
        rts

; ===============================================================
; gegevens
paldata:
        .byte $0F,$0F,$0F,$0F
        .byte $0F,$20,$10,$00
        .byte $0F,$20,$10,$00
        .byte $0F,$20,$10,$00

; index 0-25 = A-Z, 26-35 = 0-9
chartile:
        .byte $E5,$E6,$E7,$E8,$E9,$EA,$08,$EC,$ED   ; A B C D E F G H I
        .byte $EE,$EF,$F0,$F1,$F2,$F3,$F4,$F5,$F6   ; J K L M N O P Q R
        .byte $F7,$F8,$F9,$FA,$FB,$09,$FC,$0A,$CE   ; S T U V W X Y Z 0
        .byte $CF,$D0,$D1,$D2,$D3,$D4,$D5,$D9,$DC   ; 1 2 3 4 5 6 7 8 9

password:
        .byte 19,13,35,1,1,2,10                     ; T N 9 B B C K

strings:
        ; "PASSWORD" op rij 4, kolom 12
        .byte $20,$8C,8
        .byte $F4,$E5,$F7,$F7,$FB,$F3,$F6,$E8
        ; "A SELECT  B ERASE  START OK" op rij 22, kolom 2
        .byte $22,$C2,27
        .byte $E5,$00,$F7,$E9,$F0,$E9,$E7,$F8,$00,$00
        .byte $E6,$00,$E9,$F6,$E5,$F7,$E9,$00,$00
        .byte $F7,$F8,$E5,$F6,$F8,$00,$F3,$EF
        .byte $00

glyphs:
        .byte $08, $1E,$33,$60,$67,$63,$33,$1E,$00  ; G
        .byte $09, $63,$63,$36,$1C,$36,$63,$63,$00  ; X
        .byte $0A, $7F,$06,$0C,$18,$30,$60,$7F,$00  ; Z
        .byte $F5, $3E,$63,$63,$63,$6B,$66,$3B,$00  ; Q
        .byte $FA, $63,$63,$63,$63,$63,$36,$1C,$00  ; V
        .byte $CE, $3E,$63,$67,$6B,$73,$63,$3E,$00  ; 0
        .byte $CF, $0C,$1C,$0C,$0C,$0C,$0C,$3F,$00  ; 1
        .byte $D0, $3E,$63,$03,$0E,$18,$30,$7F,$00  ; 2
        .byte $D1, $3E,$63,$03,$1E,$03,$63,$3E,$00  ; 3
        .byte $D2, $06,$0E,$1E,$36,$7F,$06,$06,$00  ; 4
        .byte $D3, $7F,$60,$7E,$03,$03,$63,$3E,$00  ; 5
        .byte $D4, $1E,$30,$60,$7E,$63,$63,$3E,$00  ; 6
        .byte $D5, $7F,$03,$06,$0C,$18,$18,$18,$00  ; 7
        .byte $D9, $3E,$63,$63,$3E,$63,$63,$3E,$00  ; 8
        .byte $DC, $3E,$63,$63,$3F,$03,$06,$3C,$00  ; 9
        .byte $34, $00,$00,$00,$00,$00,$00,$7F,$00  ; _
        .byte $39, $60,$30,$18,$0C,$18,$30,$60,$00  ; cursor
        .byte $FF
