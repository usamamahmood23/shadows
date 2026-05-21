#!/usr/bin/env python3
"""Generate Lumina PWA app icons at all required sizes from geometry."""
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
os.makedirs(OUT, exist_ok=True)
MASTER = 1024  # supersample resolution

def hexa(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

def quad(p0, p1, p2, n=28):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts

def flame_outer():
    p = []
    p += quad((256, 90), (220, 160), (215, 222))
    p += quad((215, 222), (215, 274), (256, 284))
    p += quad((256, 284), (297, 274), (297, 222))
    p += quad((297, 222), (292, 160), (256, 90))
    return p

def flame_inner():
    p = []
    p += quad((256, 150), (235, 200), (235, 240))
    p += quad((235, 240), (235, 266), (256, 274))
    p += quad((256, 274), (277, 266), (277, 240))
    p += quad((277, 240), (277, 200), (256, 150))
    return p

STARS = [(92, 110, 3), (420, 80, 3.5), (380, 170, 2),
         (120, 220, 2), (430, 280, 2.5), (70, 340, 2.5), (450, 420, 2)]

def render_master(rounded=True, content_scale=1.0):
    S = MASTER / 512.0
    cx = cy = 256.0

    def sc(x, y):  # scale toward centre in 512-space
        return (cx + (x - cx) * content_scale, cy + (y - cy) * content_scale)

    def D(x, y):  # to master-space
        px, py = sc(x, y)
        return (px * S, py * S)

    def Dpts(pts):
        return [D(x, y) for (x, y) in pts]

    img = Image.new("RGBA", (MASTER, MASTER), (0, 0, 0, 0))

    # vertical gradient background
    top, bot = hexa("#1A1030"), hexa("#0F0A1A")
    grad = Image.new("RGBA", (1, MASTER))
    for y in range(MASTER):
        t = y / (MASTER - 1)
        grad.putpixel((0, y), (
            int(top[0] + (bot[0] - top[0]) * t),
            int(top[1] + (bot[1] - top[1]) * t),
            int(top[2] + (bot[2] - top[2]) * t), 255))
    grad = grad.resize((MASTER, MASTER))

    # shape mask (rounded or square)
    mask = Image.new("L", (MASTER, MASTER), 0)
    md = ImageDraw.Draw(mask)
    if rounded:
        md.rounded_rectangle([0, 0, MASTER - 1, MASTER - 1],
                             radius=int(MASTER * 0.18), fill=255)
    else:
        md.rectangle([0, 0, MASTER - 1, MASTER - 1], fill=255)
    img.paste(grad, (0, 0), mask)

    # warm radial glow behind flame
    glow = Image.new("RGBA", (MASTER, MASTER), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gxy = D(256, 205)
    gr = 150 * S * content_scale
    gd.ellipse([gxy[0] - gr, gxy[1] - gr, gxy[0] + gr, gxy[1] + gr],
               fill=hexa("#E8C4A0", 120))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(85 * S * content_scale)))
    img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    # stars
    for (sx, sy, sr) in STARS:
        x, y = D(sx, sy)
        rr = sr * S * content_scale
        draw.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 255, 130))

    # candle body
    b0 = D(216, 286); b1 = D(296, 456)
    draw.rounded_rectangle([b0[0], b0[1], b1[0], b1[1]],
                           radius=14 * S * content_scale, fill=hexa("#E8C4A0"))
    # subtle side shading
    sh0 = D(216, 286); sh1 = D(236, 456)
    draw.rectangle([sh0[0], sh0[1], sh1[0], sh1[1]], fill=hexa("#000000", 28))
    sh2 = D(280, 286); sh3 = D(296, 456)
    draw.rectangle([sh2[0], sh2[1], sh3[0], sh3[1]], fill=hexa("#000000", 36))

    # candle top ellipse
    t0 = D(216, 279); t1 = D(296, 301)
    draw.ellipse([t0[0], t0[1], t1[0], t1[1]], fill=hexa("#c9a280"))

    # wick
    w0 = D(252, 222); w1 = D(260, 290)
    draw.rectangle([w0[0], w0[1], w1[0], w1[1]], fill=hexa("#3a2818"))

    # flames
    draw.polygon(Dpts(flame_outer()), fill=hexa("#E8C4A0"))
    draw.polygon(Dpts(flame_inner()), fill=hexa("#F5DFC0"))

    # enforce shape (clean rounded corners)
    r, g, b, a = img.split()
    a = ImageChops.multiply(a, mask)
    return Image.merge("RGBA", (r, g, b, a))

def save(master, size, name):
    im = master.resize((size, size), Image.LANCZOS)
    path = os.path.join(OUT, name)
    im.save(path)
    print("wrote", name, f"{size}x{size}")

# Masters
m_round = render_master(rounded=True, content_scale=1.0)
m_square = render_master(rounded=False, content_scale=1.0)
m_mask = render_master(rounded=False, content_scale=0.72)

# Standard "any" maskable=no, rounded icons
for s in [48, 72, 96, 128, 144, 152, 192, 256, 384, 512]:
    save(m_round, s, f"icon-{s}.png")

# Maskable (full-bleed, safe-zone content)
save(m_mask, 192, "icon-maskable-192.png")
save(m_mask, 512, "icon-maskable-512.png")

# Apple touch icon (full square; iOS rounds it itself)
save(m_square, 180, "apple-touch-icon.png")
save(m_square, 167, "apple-touch-icon-167.png")
save(m_square, 152, "apple-touch-icon-152.png")
save(m_square, 120, "apple-touch-icon-120.png")

# Favicons
save(m_round, 32, "favicon-32.png")
save(m_round, 16, "favicon-16.png")

# Multi-size .ico
ico = m_round.resize((256, 256), Image.LANCZOS)
ico.save(os.path.join(OUT, "favicon.ico"),
         sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print("wrote favicon.ico")
print("done")
