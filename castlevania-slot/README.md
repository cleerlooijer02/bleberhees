# Castlevania (NES) — wachtwoordscherm en muziekrandomizer

Een patch voor Castlevania (U) op de NES. Twee dingen:

1. **Wachtwoordscherm.** Op het titelscherm start Start niet langer het spel,
   maar opent een invoerscherm. Je kiest met het pijlkruis letters en cijfers uit
   een rooster, A plaatst een teken, B wist het laatste, Start controleert.
   Klopt de code, dan begint het spel. Klopt hij niet, dan een foutgeluid,
   een korte grijsflits en het veld is weer leeg.
   De code is standaard **TN9BBCK**.
2. **Muziekrandomizer.** De golfvorm van beide pulskanalen wordt opnieuw
   gegooid bij elke wisseling van spelfase, zodat de muziek per potje en per
   level een andere klankkleur heeft.

## Toepassen

De ROM zit niet in deze repo. Pas de patch toe op je eigen kopie:

    flips castlevania-slot.ips "Castlevania (U).nes" castlevania-hack.nes

of met een willekeurige andere IPS-tool. De patch hoort bij de ROM met
sha1 `7a20c44f302fb2f1b7adffa6b619e3e1cae7b546`.

## Zelf bouwen

    ca65 src/pw.s -o pw.o && ld65 -C src/pw.cfg pw.o -o src/pw.bin
    python3 tools/build.py        # zet alles in de ROM
    python3 tools/make_ips.py     # maakt de IPS-patch

`tools/build.py` controleert bij elke patch of de originele bytes staan waar ze
worden verwacht, dus een verkeerde ROM of een verschoven adres valt meteen op.

## Code aanpassen

In `src/pw.s` staat de tabel `password`. De getallen zijn posities in het
tekenrooster: 0-25 zijn A tot Z, 26-35 zijn 0 tot 9. TN9BBCK is dus
`19,13,35,1,1,2,10`. Wil je een andere lengte dan zeven, pas dan ook de
vergelijkingen op `#7` aan en het aantal vakjes in `draw_entry`.

## Hoe het in de ROM past

De cartridge is een UNROM (mapper 2) met acht banken van 16 KB en CHR-RAM.

* De nieuwe code staat in bank 0, de geluidsbank, in de ongebruikte ruimte
  vanaf `$BB01`.
* De haak zit op de NMI-aanroep `JSR $800A` op `$C071`, die nu naar de nieuwe
  code wijst en daarna alsnog de originele routine draait. Bank 0 is op dat
  moment al gemapt, dus er is geen bankwissel nodig.
* `$C92F` — waar Start vanaf het titelscherm het spel begon — springt nu naar
  een trampoline in het gat op `$FF2A` in de vaste bank, die alleen een vlag zet.
* Omdat het een CHR-RAM-cartridge is, ontbraken de letters G, Q, V, X en Z en
  alle cijfers in het lettertype. Die worden bij het openen van het scherm zelf
  naar de videochip geschreven, in dezelfde stijl als het bestaande lettertype.
* De randomizer vervangt de acht `STA $4000,X` in de geluidsengine door een
  aanroep die er bij de twee pulskanalen een eigen golfvorm in mengt.

Gebruikt RAM: `$07D0`-`$07E3`, geverifieerd ongebruikt door het spel zelf.
