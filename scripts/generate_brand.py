"""Erzeugt die Raster-Marken-Assets aus der Zeichen-Geometrie.

Quelle der Wahrheit ist das Familienraster 120x120: Ring R46 · Schicht R27 ·
offener Kern R11 · Klangbogen R36 (~52°, oben rechts) · Linienstärke 4, runde
Enden. App-Kachel mit Verlauf und Bogen; Favicon vereinfacht ohne Bogen.

Aufruf:  python scripts/generate_brand.py
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HIER, "..", "app", "static", "brand")
os.makedirs(OUT, exist_ok=True)

BRAND = (64, 118, 185)     # #4076B9  Markenblau
DEEP = (44, 85, 145)       # #2C5591  Blau tief
WHITE = (255, 255, 255)
S = 4                      # Supersampling für saubere Kanten


def _vertikaler_verlauf(size: int, oben, unten) -> Image.Image:
    img = Image.new("RGB", (size, size), oben)
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / max(1, size - 1)
        c = tuple(round(oben[i] + (unten[i] - oben[i]) * t) for i in range(3))
        d.line([(0, y), (size, y)], fill=c)
    return img


def _kachel_hintergrund(px: int) -> Image.Image:
    """Blaue Kachel mit Verlauf und ~23% Eckenradius, transparent aussen."""
    n = px * S
    grad = _vertikaler_verlauf(n, BRAND, DEEP).convert("RGBA")
    maske = Image.new("L", (n, n), 0)
    ImageDraw.Draw(maske).rounded_rectangle([0, 0, n - 1, n - 1],
                                            radius=int(0.23 * n), fill=255)
    grad.putalpha(maske)
    return grad


def _transform(x, y, mitte, scale):
    """Artboard-Koordinate (120er-Raster, Zentrum 60/60) -> Canvas-Pixel."""
    return (mitte + (x - 60) * scale, mitte + (y - 60) * scale)


def _kreis(d, mitte, scale, r, width, farbe):
    x0, y0 = _transform(60 - r, 60 - r, mitte, scale)
    x1, y1 = _transform(60 + r, 60 + r, mitte, scale)
    d.ellipse([x0, y0, x1, y1], outline=farbe, width=max(1, round(width * scale)))


def _klangbogen(d, mitte, scale, farbe, width):
    r, w = 36, max(1, round(4 * scale))
    pkte = []
    for i in range(28):
        t = math.radians(-72 + (52) * i / 27)   # -72° .. -20°
        x, y = 60 + r * math.cos(t), 60 + r * math.sin(t)
        pkte.append(_transform(x, y, mitte, scale))
    d.line(pkte, fill=farbe, width=w, joint="curve")
    for p in (pkte[0], pkte[-1]):               # runde Enden
        rr = w / 2
        d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=farbe)


def app_kachel(px: int, mit_bogen: bool = True) -> Image.Image:
    n = px * S
    img = _kachel_hintergrund(px)
    d = ImageDraw.Draw(img)
    mitte = n / 2
    scale = (n * (1 - 2 * 0.15)) / 120         # 15% Rand
    for r in (46, 27, 11):
        _kreis(d, mitte, scale, r, 4, WHITE)
    if mit_bogen:
        _klangbogen(d, mitte, scale, WHITE, 4)
    return img.resize((px, px), Image.LANCZOS)


def favicon(px: int) -> Image.Image:
    """Vereinfacht: kein Bogen. 32px zwei Schichten, 16px eine kräftige."""
    n = px * S
    img = _kachel_hintergrund(px)
    d = ImageDraw.Draw(img)
    mitte = n / 2
    scale = (n * (1 - 2 * 0.13)) / 120
    if px >= 24:
        _kreis(d, mitte, scale, 40, 6, WHITE)
        _kreis(d, mitte, scale, 19, 6, WHITE)
        r = round(5 * scale)
        d.ellipse([mitte - r, mitte - r, mitte + r, mitte + r], fill=WHITE)
    else:
        _kreis(d, mitte, scale, 34, 9, WHITE)
        r = round(9 * scale)
        d.ellipse([mitte - r, mitte - r, mitte + r, mitte + r], fill=WHITE)
    return img.resize((px, px), Image.LANCZOS)


def main():
    app_kachel(180).save(os.path.join(OUT, "apple-touch-icon.png"))
    app_kachel(512).save(os.path.join(OUT, "icon-512.png"))
    app_kachel(192).save(os.path.join(OUT, "icon-192.png"))
    f32, f16 = favicon(32), favicon(16)
    f32.save(os.path.join(OUT, "favicon-32.png"))
    f16.save(os.path.join(OUT, "favicon-16.png"))
    f32.save(os.path.join(OUT, "favicon.ico"),
             sizes=[(16, 16), (32, 32), (48, 48)])
    print("Marken-Assets geschrieben nach", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
