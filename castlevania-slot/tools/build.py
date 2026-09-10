#!/usr/bin/env python3
import sys, os
SRC = os.path.expanduser('~/cvhack/cv_orig.nes')
OUT = os.path.expanduser('~/cvhack/cv_hack.nes')

def off(bank, addr):
    base = 0x8000 if bank < 7 else 0xC000
    assert base <= addr < base + 0x4000, hex(addr)
    return 16 + bank*0x4000 + (addr - base)

rom = bytearray(open(SRC,'rb').read())

def poke(bank, addr, data, expect=None):
    o = off(bank, addr)
    if expect is not None:
        got = bytes(rom[o:o+len(expect)])
        assert got == bytes(expect), 'verwacht %s op %04X, gevonden %s' % (
            expect.hex(), addr, got.hex())
    rom[o:o+len(data)] = data

# 1. wachtwoordcode in bank 0 op $BB01
blob = open(os.path.expanduser('~/cvhack/src/pw.bin'),'rb').read()
assert len(blob) <= 0xC000-0xBB01, 'past niet in bank 0'
free = rom[off(0,0xBB01):off(0,0xBB01)+len(blob)]
assert set(free) == {0xFF}, 'bank 0 doelgebied is niet leeg'
poke(0, 0xBB01, blob)

# 2. haak in de NMI: JSR $800A wordt JSR $BB01 (bank 0 is daar al gemapt)
poke(7, 0xC071, bytes([0x20, 0x01, 0xBB]), expect=bytes([0x20,0x0A,0x80]))

# 3. trampoline in de vaste bank
tramp = bytes([0xAD,0xD0,0x07, 0xD0,0x05, 0xA9,0x01, 0x8D,0xD0,0x07, 0x60])
assert set(rom[off(7,0xFF2A):off(7,0xFF2A)+22]) == {0xFF}, 'gat $FF2A niet leeg'
poke(7, 0xFF2A, tramp)

# 4. Start op het titelscherm start niet meer het spel maar het slot
poke(7, 0xC92F, bytes([0x4C,0x2A,0xFF,0xEA,0xEA]),
     expect=bytes([0xA9,0x03,0x4C,0x7A,0xC3]))

# 5. muziekrandomizer: elke "STA $4000,X" in de geluidsengine wordt
#    een aanroep naar duty_write, dat de golfvorm van de pulskanalen
#    overschrijft met een per nummer opnieuw gegooide waarde
import re
m = re.search(rb'\xE0\x00\xF0.\xE0\x04\xF0.\x9D\x00\x40\x60', blob)
assert m, 'duty_write niet gevonden in de blob'
duty = 0xBB01 + m.start()
SITES = [0x8343, 0x842B, 0x844F, 0x84EA, 0x854C, 0x85BB, 0x86A4, 0x86C2]
for a in SITES:
    poke(0, a, bytes([0x20, duty & 0xFF, duty >> 8]), expect=bytes([0x9D,0x00,0x40]))
print('duty_write op $%04X, %d schrijfacties omgeleid' % (duty, len(SITES)))

open(OUT,'wb').write(rom)
print('geschreven:', OUT, len(rom), 'bytes')
