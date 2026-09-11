# bleberhees

Patches voor NES-spellen. Per spel een eigen map met de broncode, de bouwtools
en een kant-en-klare IPS-patch.

## Inhoud

* [`castlevania-slot/`](castlevania-slot/) — Castlevania (U): een wachtwoordscherm
  op het titelscherm en een randomizer voor de golfvorm van de pulskanalen.
* [`tools/`](tools/) — gereedschap dat niet aan één spel vastzit. `romcheck.py`
  ontleedt een willekeurige NES-ROM en controleert of de iNES-header klopt met
  wat er werkelijk in het bestand staat.

## Opzet

ROM-bestanden staan niet in deze repo; `.gitignore` houdt `*.nes` buiten de deur.
Wat er wel in staat is de broncode en een IPS-patch die je op je eigen kopie
toepast. Elke map heeft een eigen README met de sha1 van de ROM waar de patch bij
hoort, de stappen om hem zelf te bouwen, en notities over hoe de code in de ROM past.

Een nieuw spel krijgt een eigen map in dezelfde indeling:

    <spel>/
      src/        6502-broncode en linkerconfig
      tools/      build- en patchscripts
      doc/        onderzoeksnotities en screenshots
      README.md
      <spel>.ips

Let op dat de tools per spel bij die cartridge horen: `castlevania-slot` gaat uit
van een UNROM-bord (mapper 2) met CHR-RAM, en de adressen in `tools/build.py`
gelden alleen voor die ene ROM. Een spel op ander mapperbord begint dus met een
eigen ronde onderzoek in `doc/`. Het algemene `romcheck.py` in de bovenste
`tools/` werkt wel op elke ROM.
