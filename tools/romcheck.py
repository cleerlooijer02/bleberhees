#!/usr/bin/env python3
"""Bakent een NES-ROM af: header ontleden, blokken opmeten, en controleren of
het iNES-omslag klopt met wat er werkelijk in het bestand zit.

    romcheck.py rom.nes                 lees de ROM uit en geef een oordeel
    romcheck.py rom.nes --nes2 uit.nes  schrijf een kopie met een NES 2.0-header

De controle steunt op drie onafhankelijke bronnen: de iNES-header van 16 bytes
vooraan, de interne Nintendo-header die veel eerste-partijspellen op $FFF0
hebben staan, en de code zelf, want elke mapper heeft eigen registers.
"""
import sys, hashlib, zlib

PRG_CODE = {0: '8/64K', 1: '16K', 2: '32K', 3: '128K', 4: '256K', 5: '512K'}
CHR_CODE = {0: '8K', 1: '16K', 2: '32K', 3: '64/128K', 4: '256K'}

# schrijfacties die een mapper verraden: adres -> (mapper, uitleg)
MAPPER_SPOOR = {
    0x8000: ('MMC1/MMC3', 'bankkeuze'),
    0x8001: ('MMC3', 'bankdata'),
    0xA000: ('MMC1/MMC3', 'spiegeling of CHR-bank'),
    0xA001: ('MMC3', 'PRG-RAM-protect'),
    0xC000: ('MMC1/MMC3', 'IRQ-latch of CHR-bank'),
    0xC001: ('MMC3', 'IRQ-herlaad'),
    0xE000: ('MMC1/MMC3', 'IRQ uit of PRG-bank'),
    0xE001: ('MMC3', 'IRQ aan'),
}


def lees(pad):
    rom = open(pad, 'rb').read()
    if rom[:4] != b'NES\x1a':
        sys.exit('geen iNES-bestand: magic ontbreekt')
    return rom


def ontleed_header(h):
    nes2 = (h[7] & 0x0C) == 0x08
    mapper = (h[6] >> 4) | (h[7] & 0xF0)
    if nes2:
        mapper |= (h[8] & 0x0F) << 8
    return {
        'nes2': nes2,
        'prg': h[4] * 16384,
        'chr': h[5] * 8192,
        'mapper': mapper,
        'spiegeling': 'vier-scherm' if h[6] & 8 else ('verticaal' if h[6] & 1 else 'horizontaal'),
        'vierscherm': bool(h[6] & 8),
        'batterij': bool(h[6] & 2),
        'trainer': bool(h[6] & 4),
        'rommel': h[8:16] if not nes2 else b'',
    }


def interne_header(prg):
    """De tien bytes op $FFF0 in de laatste bank; None als hij niet klopt."""
    if len(prg) < 32:
        return None
    h = prg[-16:-6]
    if sum(prg[-14:-6]) & 0xFF:              # controlebyte op $FFF9
        return None
    lengte = (h[7] & 0x0F) + 1
    naam = prg[-16 - lengte:-16]
    return {
        'naam': naam.decode('ascii', 'replace') if h[6] == 1 else naam.hex(' '),
        'prg_som': h[0] << 8 | h[1],
        'chr_som': h[2] << 8 | h[3],
        'prg_grootte': PRG_CODE.get(h[4] >> 4, '?'),
        'chr_ram': bool(h[4] & 8),
        'chr_grootte': CHR_CODE.get(h[4] & 7, '?'),
        'bord': h[5] & 0x7F,
        'licensee': h[8],
    }


def werk_ram_in_code(prg):
    """Leest of schrijft de code naar $6000-$7FFF? Dan zit er werk-RAM op het bord."""
    n = 0
    for i in range(len(prg) - 2):
        if prg[i] in (0x8D, 0xAD, 0x9D, 0xBD, 0x99, 0xB9):
            adres = prg[i + 1] | prg[i + 2] << 8
            if 0x6000 <= adres < 0x8000:
                n += 1
    return n


def mapper_uit_code(prg):
    """Tel schrijfacties naar mapper-registers, per bank losgeteld."""
    gezien = {}
    for i in range(len(prg) - 2):
        if prg[i] in (0x8D, 0x9D, 0x99):     # STA abs / abs,X / abs,Y
            adres = prg[i + 1] | prg[i + 2] << 8
            if adres in MAPPER_SPOOR:
                gezien[adres] = gezien.get(adres, 0) + 1
    return gezien


def toon(pad, rom):
    h = ontleed_header(rom[:16])
    begin = 16 + (512 if h['trainer'] else 0)
    prg = rom[begin:begin + h['prg']]
    chr_ = rom[begin + h['prg']:begin + h['prg'] + h['chr']]
    rest = len(rom) - begin - h['prg'] - h['chr']

    print('bestand   %s' % pad)
    print('  grootte %d bytes   crc32 %08X   sha1 %s'
          % (len(rom), zlib.crc32(rom) & 0xFFFFFFFF, hashlib.sha1(rom).hexdigest()))
    print()
    print('afbakening')
    print('  0x%06X - 0x%06X  iNES-header, 16 bytes' % (0, 15))
    if h['trainer']:
        print('  0x%06X - 0x%06X  trainer, 512 bytes' % (16, 527))
    print('  0x%06X - 0x%06X  PRG-ROM, %d KB in %d banken van 16 KB'
          % (begin, begin + h['prg'] - 1, h['prg'] // 1024, h['prg'] // 16384))
    if h['chr']:
        print('  0x%06X - 0x%06X  CHR-ROM, %d KB in %d banken van 8 KB'
              % (begin + h['prg'], begin + h['prg'] + h['chr'] - 1,
                 h['chr'] // 1024, h['chr'] // 8192))
    else:
        print('                          geen CHR-ROM: het spel gebruikt CHR-RAM')
    if rest:
        print('  0x%06X - 0x%06X  ONVERKLAARD, %d bytes over'
              % (begin + h['prg'] + h['chr'], len(rom) - 1, rest))
    print()
    print('iNES-header zegt')
    print('  formaat     %s' % ('NES 2.0' if h['nes2'] else 'iNES'))
    print('  mapper      %d' % h['mapper'])
    print('  spiegeling  %s' % h['spiegeling'])
    print('  batterij    %s' % ('ja' if h['batterij'] else 'nee'))
    if h['rommel'].strip(b'\x00'):
        print('  LET OP      bytes 8-15 zijn niet leeg: %s (%s)'
              % (h['rommel'].hex(' '), h['rommel'].decode('ascii', 'replace')))

    ih = interne_header(prg)
    if ih:
        echt = (sum(prg) - prg[-16] - prg[-15]) & 0xFFFF
        print()
        print('interne Nintendo-header op $FFF0')
        print('  titel       %s' % ih['naam'])
        print('  PRG         %s, checksum $%04X (werkelijk $%04X, %s)'
              % (ih['prg_grootte'], ih['prg_som'], echt,
                 'klopt' if echt == ih['prg_som'] else 'wijkt af'))
        print('  CHR         %s %s, checksum $%04X'
              % (ih['chr_grootte'], 'CHR-RAM' if ih['chr_ram'] else 'CHR-ROM', ih['chr_som']))
        print('  bord %d, licensee $%02X' % (ih['bord'], ih['licensee']))

    wram = werk_ram_in_code(prg)
    sporen = mapper_uit_code(prg)
    if sporen:
        print()
        print('mapper-registers waar de code naartoe schrijft')
        for adres in sorted(sporen):
            naam, uitleg = MAPPER_SPOOR[adres]
            print('  $%04X  %-4d keer   %s: %s' % (adres, sporen[adres], naam, uitleg))
        mmc3 = any(a in sporen for a in (0x8001, 0xA001, 0xC001, 0xE001))
        print('  gedrag past bij %s' % ('MMC3 (mapper 4)' if mmc3 else 'MMC1 (mapper 1) of eenvoudiger'))

    if wram:
        print()
        print('werk-RAM')
        print('  de code raakt $6000-$7FFF %d keer aan: het bord heeft 8 KB werk-RAM%s'
              % (wram, ', met batterij' if h['batterij'] else ', zonder batterij'))

    print()
    print('oordeel')
    fouten, opmerkingen = [], []
    if rest > 0:
        fouten.append('%d bytes staan buiten wat de header aangeeft' % rest)
    elif rest < 0:
        fouten.append('bestand is %d bytes korter dan de header belooft: afgekapt' % -rest)
    if sporen:
        mmc3 = any(a in sporen for a in (0x8001, 0xA001, 0xC001, 0xE001))
        if mmc3 and h['mapper'] != 4:
            fouten.append('code stuurt MMC3 aan maar de header zegt mapper %d' % h['mapper'])
        if not mmc3 and h['mapper'] == 4:
            fouten.append('header zegt MMC3 maar de code gebruikt die registers niet')
    if ih:
        echt = (sum(prg) - prg[-16] - prg[-15]) & 0xFFFF
        if h['chr'] and ih['chr_ram']:
            opmerkingen.append('interne header zegt CHR-RAM terwijl er %d KB CHR-ROM in het bestand '
                               'zit' % (h['chr'] // 1024))
        if echt != ih['prg_som']:
            opmerkingen.append('interne PRG-checksum klopt niet met de werkelijke som')
        if opmerkingen:
            opmerkingen.append('zulke velden staan bij veel eerste-partijspellen verkeerd in de ROM '
                               'omdat het blok uit een eerdere build is blijven staan; vergelijk met '
                               'een bekende dump voordat je hier iets aan verandert')
    for f in fouten:
        print('  FOUT       %s' % f)
    if not fouten:
        print('  header en inhoud sluiten op elkaar aan, geen gaten of resten')
    for o in opmerkingen:
        print('  opmerking  %s' % o)
    return h, begin, prg, chr_, wram


def schrijf_nes2(rom, h, begin, wram, uit):
    """Zelfde data, maar omlijst met een NES 2.0-header die het bord beschrijft."""
    kop = bytearray(16)
    kop[0:4] = b'NES\x1a'
    kop[4] = h['prg'] // 16384
    kop[5] = h['chr'] // 8192
    kop[6] = ((h['mapper'] & 0x0F) << 4) | (8 if h['vierscherm'] else 0) \
        | (2 if h['batterij'] else 0) | (1 if h['spiegeling'] == 'verticaal' else 0)
    kop[7] = (h['mapper'] & 0xF0) | 0x08          # 0x08 = dit is NES 2.0
    kop[8] = (h['mapper'] >> 8) & 0x0F            # submapper 0
    kop[9] = 0                                    # geen extra groottebits nodig
    if wram:                                      # 8 KB werk-RAM: 64 << 7 = 8192
        kop[10] = 0x70 if h['batterij'] else 0x07  # hoge nibble = met batterij
    kop[11] = 0 if h['chr'] else 0x07             # 8 KB CHR-RAM als er geen CHR-ROM is
    kop[12] = 0                                   # NTSC
    open(uit, 'wb').write(bytes(kop) + rom[begin:])
    print()
    print('geschreven: %s (%d bytes, NES 2.0-header)' % (uit, 16 + len(rom) - begin))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rom = lees(sys.argv[1])
    h, begin, prg, chr_, wram = toon(sys.argv[1], rom)
    if '--nes2' in sys.argv:
        schrijf_nes2(rom, h, begin, wram, sys.argv[sys.argv.index('--nes2') + 1])
