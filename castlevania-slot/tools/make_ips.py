#!/usr/bin/env python3
"""Maakt een IPS-patch uit het verschil tussen de originele en de aangepaste ROM."""
import os
a = open(os.path.expanduser('~/cvhack/cv_orig.nes'),'rb').read()
b = open(os.path.expanduser('~/cvhack/cv_hack.nes'),'rb').read()
assert len(a) == len(b), 'ROMs verschillen in lengte'

out = bytearray(b'PATCH')
i, blokken = 0, 0
while i < len(a):
    if a[i] == b[i]:
        i += 1
        continue
    j = i
    gelijk = 0
    while j < len(a) and gelijk < 6:          # kleine gaten meenemen
        gelijk = gelijk + 1 if a[j] == b[j] else 0
        j += 1
    j -= gelijk
    chunk = b[i:j]
    while chunk:
        deel, chunk = chunk[:0xFFFF], chunk[0xFFFF:]
        assert i != 0x454F46, 'offset botst met de EOF-markering'
        out += bytes([i >> 16 & 0xFF, i >> 8 & 0xFF, i & 0xFF])
        out += bytes([len(deel) >> 8, len(deel) & 0xFF]) + deel
        i += len(deel)
        blokken += 1
    i = j
out += b'EOF'
p = os.path.expanduser('~/cvhack/castlevania-slot.ips')
open(p,'wb').write(out)
print('%s geschreven: %d bytes, %d blokken' % (p, len(out), blokken))

# controle: patch terug toepassen op het origineel
d = bytearray(a); k = 5
while d[k:k+3] != b'EOF' if False else out[k:k+3] != b'EOF':
    off = out[k] << 16 | out[k+1] << 8 | out[k+2]
    ln = out[k+3] << 8 | out[k+4]
    d[off:off+ln] = out[k+5:k+5+ln]
    k += 5 + ln
print('controle:', 'IDENTIEK aan cv_hack.nes' if bytes(d) == b else 'AFWIJKING!')
