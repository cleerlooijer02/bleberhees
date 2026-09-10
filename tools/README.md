# romcheck.py

Bakent een NES-ROM af en controleert of het iNES-omslag klopt met de inhoud.

    python3 tools/romcheck.py rom.nes
    python3 tools/romcheck.py rom.nes --nes2 uit.nes

De controle steunt op drie bronnen die los van elkaar staan, zodat ze elkaar
kunnen tegenspreken:

* de iNES-header van 16 bytes vooraan, die zegt hoe groot PRG en CHR zijn en
  welke mapper erin zit;
* de interne Nintendo-header op `$FFF0` in de laatste bank, die veel
  eerste-partijspellen hebben: titel, formaat, en checksums over PRG en CHR;
* de code zelf, want een spel verraadt zijn mapper door de registers die het
  aanschrijft. `STA $8001` en `STA $A001` horen bij de MMC3, een reeks losse
  schrijfacties naar `$8000` bij de MMC1. Zo ook werk-RAM: raakt de code
  `$6000-$7FFF` aan, dan zit dat geheugen op het bord.

Met `--nes2` schrijft het gereedschap dezelfde data weg met een NES 2.0-header,
waarin ook submapper, werk-RAM, CHR-RAM en beeldnorm passen. De data blijft
byte voor byte gelijk, alleen de eerste 16 bytes veranderen.

## Waarschuwing bij de interne header

Die interne header is regelmatig niet bijgewerkt. Super Mario Bros. 2 (USA) is
het mooiste voorbeeld: het blok op `$FFEB` noemt zichzelf `ZELDA`, meldt
CHR-RAM terwijl het spel 128 KB CHR-ROM heeft, en draagt een PRG-checksum
(`$DFE6`) die niets met de eigen PRG te maken heeft (`$8769`). Het sjabloon van
een eerdere build is gewoon blijven staan. De controlebyte op `$FFF9` klopt wel,
dus het blok is echt Nintendo-materiaal en geen beschadiging.

Kortom: laat de interne header nooit in je eentje beslissen dat een ROM stuk is.
Vergelijk eerst de chiphashes met een bekende dump. Voor SMB2 (USA) revisie 0,
bord NES-TSROM-01, horen deze erbij:

    PRG  crc32 07854B3F  sha1 9BEA58BA97730C84232A4ACBB23C3EA7BCE14EC5
    CHR  crc32 F2BA1170  sha1 D9976B677AD222B76FBDAF31713374E2F283D44E
    data crc32 57AC67AF  sha1 43AC7C7AAF1846EAD7B544302BB9131E4964FD32
