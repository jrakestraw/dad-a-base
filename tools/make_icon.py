"""Draws the launcher icon (glasses + mustache on mustard) at every density Android asks for."""
from pathlib import Path
from PIL import Image, ImageDraw

MUSTARD, BROWN, LENS = (224, 165, 38), (43, 26, 16), (251, 243, 226)
res = Path(__file__).resolve().parent.parent / "android" / "res"

def face(size, scale):
    """Glasses and mustache centred in a size x size canvas; scale shrinks them into the adaptive safe zone."""
    S = 4 * size  # supersample, then downscale for smooth edges
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = S * scale / 10000  # the drawing box is scale% of the canvas; 1 unit = 1% of that box
    cx, cy = S / 2, S / 2
    def box(x0, y0, x1, y1): return [cx + x0 * u, cy + y0 * u, cx + x1 * u, cy + y1 * u]
    # brows
    d.rounded_rectangle(box(-40, -36, -8, -28), radius=4 * u, fill=BROWN)
    d.rounded_rectangle(box(8, -36, 40, -28), radius=4 * u, fill=BROWN)
    # glasses
    for x in (-24, 24):
        d.ellipse(box(x - 18, -24, x + 18, 10), fill=BROWN)
        d.ellipse(box(x - 12, -18, x + 12, 4), fill=LENS)
        d.ellipse(box(x - 4, -10, x + 4, -2), fill=BROWN)  # pupils
    d.rectangle(box(-7, -12, 7, -6), fill=BROWN)  # bridge
    # nose
    d.ellipse(box(-10, 2, 10, 20), fill=(196, 110, 70))
    # mustache: two swoops
    d.chord(box(-44, 8, 2, 40), 180, 360, fill=BROWN)
    d.chord(box(-2, 8, 44, 40), 180, 360, fill=BROWN)
    d.ellipse(box(-50, 14, -36, 28), fill=BROWN)
    d.ellipse(box(36, 14, 50, 28), fill=BROWN)
    return im.resize((size, size), Image.LANCZOS)

dens = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
for name, k in dens.items():
    folder = res / f"mipmap-{name}"; folder.mkdir(parents=True, exist_ok=True)
    fg = int(108 * k)
    face(fg, 56).save(folder / "ic_launcher_foreground.png")
    lg = int(48 * k)
    S = lg * 4
    base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(base).rounded_rectangle([0, 0, S - 1, S - 1], radius=S * 0.22, fill=MUSTARD)
    base = base.resize((lg, lg), Image.LANCZOS)
    base.alpha_composite(face(lg, 80))
    base.save(folder / "ic_launcher.png")
(res / "mipmap-anydpi-v26").mkdir(exist_ok=True)
(res / "mipmap-anydpi-v26" / "ic_launcher.xml").write_text(
    '<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
    '    <background android:drawable="@color/ic_launcher_background" />\n'
    '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n</adaptive-icon>\n', encoding="utf-8")

