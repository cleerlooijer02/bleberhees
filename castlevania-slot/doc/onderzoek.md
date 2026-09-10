# Castlevania (NES) hack - onderzoeksnotities (geparkeerd)

ROM: 131088 bytes, iNES, mapper 2 (UNROM), 8x16KB PRG, CHR-RAM, verticale mirroring
md5 52eb3f7e2c5fc765aa71f21c85f0770e / sha1 7a20c44f302fb2f1b7adffa6b619e3e1cae7b546

## Toolchain (geinstalleerd in deze container)
cc65/ca65, fceux (/usr/games/fceux) + xvfb, python3. Eigen disassembler: disasm.py
Headless draaien:
  xvfb-run -a /usr/games/fceux --sound 0 --no-config 1 --loadlua probe.lua cv_orig.nes
Lua kan geheugen lezen en gui.savescreenshotas() doen -> visuele verificatie werkt.

## Bankindeling
bank 0 = geluidsengine (vrij vanaf $BB01, 1279 bytes)
bank 6 = titel/menu/demo (vrij vanaf $BA3B, 1477 bytes)
bank 7 = vast $C000-$FFFF, praktisch vol. Enige bruikbare gat: $FF2A-$FF3F (22 bytes)
Bankswitch: JSR $C1D8 met Y=bank (bus-conflict-veilig via tabel op $C000)
  $C1D4 = terug naar bank in $24, $C1D6 = zet $27=Y en switch

## Belangrijke adressen
$18 = game mode (0=titel-init, 1=TITELSCHERM, 2=demo-start, 5=gameplay)
$1A = frameteller, $1E = timer, $24 = huidige bank
$04/$05 = pad1/pad2 ingedrukt, $F5/$F6 = nieuw ingedrukt, $F7/$F8 = vorige frame
  bit7=A bit6=B bit5=Select bit4=Start bit3=Up bit2=Down bit1=Left bit0=Right
$FE = waarde die NMI naar $2001 schrijft (PPU mask; emphasis-bits bruikbaar voor tint)

Controller uitlezen: $C8CD (bank 7)
Titel-invoer (Start/Select): $C91C (bank 7)
  $C92F: LDA #$03 / JMP $C37A  <- start het spel. HIER het slot inhaken.
Mode-dispatch: $C1E4 -> $CA6D (inline jump table op $C1F4)
Mode 1 handler: $B823 (bank 6). Bevestigd via emulator: mode=01, bank=06.

## Geluidsengine (bank 0)
Kanaalloop: $83AF-$83D1. X=$AB loopt $80,$90,$A0,$B0,$C0,$D0 (6 zachte kanalen),
Y=$AC loopt 0,4,8,12,0,4 = APU-offset. $AC wordt maar op EEN plek geschreven ($83B5).
  $80->pulse1 $90->pulse2 $A0->triangle $B0->noise $C0/$D0 = SFX over pulse1/2
Volume/duty-schrijfacties: 11x "STA $4000,X" met X=$AC ($8341,$8429,$844D,$84E8,
  $851B,$854A,$85B9,$8620,$86A2,$86C0,$871D,$873D) -> elk 3 bytes, kan 1-op-1
  vervangen door "JSR duty" (ook 3 bytes). Perfecte plek voor duty-randomizer.
Sound trigger: $C1A7 (bank7) -> $8187 (bank 0), A = sound id, $E5 = id.

## Vrij RAM
Zeropage: alleen $5A en $CB lijken ongebruikt (indexed access nog niet uitgesloten).
Pagina $0700 is grotendeels vrij; $07E8-$07EC gekozen als kandidaat (nog te
verifieren met een write-watch tijdens de demo).

## Voorgenomen ontwerp
1) SLOT: alle logica in bank 0 op $BB01, aangehaakt op $8052 (draait elke frame
   met bank 0 gemapt). Houdt code-index + unlocked-vlag in $07E8/$07E9.
   Bank 7 krijgt 1 kleine patch: $C92F -> JMP $FF2A, en op $FF2A een stukje dat
   de unlocked-vlag test en anders RTS doet.
   Feedback: rode PPU-emphasis-tint zolang vergrendeld (via $FE) + pieptoon per toets.
2) MUZIEK: duty-randomizer op de 11 schrijfacties hierboven; per track opnieuw
   gegooid, geseed met de frameteller op het moment dat de code af is.
   Kanaalswap pulse1<->pulse2 kan simpel via $AC-tabel, maar klinkt nauwelijks.

## Nog te doen / open
- $07E8-$07EC echt verifieren als vrij RAM
- $FF2A-$FF3F verifieren als echte padding
- Welke code wil de gebruiker? Hoe wild mag de muziekrandomizer?
- Uitleveren als IPS/BPS-patch, niet als complete ROM.
