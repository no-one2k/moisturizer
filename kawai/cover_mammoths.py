"""Черновик заглавной картинки: на майке Кавая «RAPTORS» → «MAMMOTHS».

Исходник — Chensiyuan, CC BY-SA 4.0:
https://commons.wikimedia.org/wiki/File:1_kawhi_leonard_2019_nba_finals.jpg
Результат — производная работа, тоже CC BY-SA 4.0, подпись: «Фото: Chensiyuan,
CC BY-SA 4.0, изменено».

Запуск: ~/.virtualenvs/blog_env/bin/python articles/kawai/scripts/cover_mammoths.py <исходник.jpg>
Пишет charts/cover_mammoths.jpg (16:9, Кавай слева, справа трибуны).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as ndi

OUT = Path(__file__).resolve().parents[1] / "charts"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"

# Надпись лежит на дуге окружности (подогнано по центрам букв RAPTORS, координаты полного кадра)
X0, Y0 = 1455, 1720  # левый верхний угол рабочей области на майке
W, H = 705, 485
CX, CY, R = X0 + 383, Y0 + 350, 219
WORD, MID = "MAMMOTHS", -99.0  # середина надписи — чуть левее, чем у RAPTORS (-96.9)
CAP, TRACK = 70, 5  # высота заглавной и зазор между буквами, px


def letters_mask(img):
    """Тёмные нейтральные пиксели надписи в полосе вокруг дуги + обводка."""
    a = img.astype(float)
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / (mx + 1)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    r = np.hypot(xx - CX, yy - CY)
    ang = np.degrees(np.arctan2(yy - CY, xx - CX))
    band = (np.abs(r - R) < 62) & (ang < -15) & (ang > -180) & (yy < CY)
    m = band & (mx < 110) & (sat < 0.35)
    skin = (sat > 0.3) & (mx > 90)  # у тёмных пикселей насыщенность шумит от JPEG, не отсекать их
    m = ndi.binary_dilation(m, iterations=11) & band & ~skin
    m = ndi.binary_fill_holes(ndi.binary_closing(m, iterations=3)) & band & ~skin
    fabric = ndi.binary_closing(((mx > 110) & (sat < 0.22)) | m, iterations=3)
    # правый край майки (дальше рука): по каждой строке — самый правый светлый пиксель ткани
    bright = (mx > 100) & (sat < 0.17) & (xx < X0 + W) & (xx > CX)
    xr = np.where(bright.any(1), a.shape[1] - 1 - np.argmax(bright[:, ::-1], 1), 0)
    xr = ndi.median_filter(xr, 41)
    fabric &= xx <= xr[:, None]
    m &= xx <= xr[:, None] + 3
    return m, sat, fabric


def fill(img, m, sigma=14):
    """Нормированная свёртка: дыры заливаются размытой тканью вокруг."""
    a = img.astype(float)
    mx, mn = a.max(2), a.min(2)
    keep = (~m & (mx > 120) & ((mx - mn) / (mx + 1) < 0.25)).astype(float)  # заливать только тканью, не кожей
    num = np.stack([ndi.gaussian_filter(a[..., k] * keep, sigma) for k in range(3)], -1)
    den = ndi.gaussian_filter(keep, sigma)[..., None] + 1e-6
    f = num / den
    rng = np.random.default_rng(0)
    f += rng.normal(0, 2.5, f.shape)
    out = a.copy()
    out[m] = f[m]
    return out, f


def render_word(shape):
    """Буквы по дуге: альфа заливки и альфа обводки в полном кадре."""
    fill_a = Image.new("L", (shape[1], shape[0]), 0)
    edge_a = Image.new("L", (shape[1], shape[0]), 0)
    font = ImageFont.truetype(FONT, int(CAP * 1.37))
    adv = np.array([font.getlength(ch) for ch in WORD]) + TRACK
    pos = np.cumsum(adv) - adv / 2 - adv.sum() / 2  # центры букв вдоль дуги, px от середины
    for ch, th in zip(WORD, MID + np.degrees(pos / R)):
        t = np.radians(th)
        px, py = CX + R * np.cos(t), CY + R * np.sin(t)
        for layer, stroke in ((edge_a, 2), (fill_a, 0)):
            tile = Image.new("L", (260, 260), 0)
            d = ImageDraw.Draw(tile)
            d.text((130, 130), ch, font=font, fill=255, anchor="mm", stroke_width=stroke, stroke_fill=255)
            tile = tile.rotate(-90 - th, resample=Image.BICUBIC)
            layer.paste(tile, (int(px - 130), int(py - 130)), tile)
    blur = ImageFilter.GaussianBlur(1.0)
    return (np.asarray(fill_a.filter(blur), float) / 255, np.asarray(edge_a.filter(blur), float) / 255)


def credit(img, text="Фото: Chensiyuan, CC BY-SA 4.0, изменено"):
    """Подпись об источнике в правом нижнем углу (требование CC BY-SA)."""
    font = ImageFont.truetype(FONT.replace("Condensed-Bold", ""), img.width // 80)
    d = ImageDraw.Draw(img, "RGBA")
    pad = img.width // 200
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font)
    x, y = img.width - (x1 - x0) - 3 * pad, img.height - (y1 - y0) - 3 * pad
    d.rectangle((x - pad, y - pad, x + x1 - x0 + pad, y + y1 - y0 + pad), fill=(0, 0, 0, 120))
    d.text((x - x0, y - y0), text, font=font, fill=(255, 255, 255, 230))


def main(src):
    full = np.asarray(Image.open(src).convert("RGB"))
    out = full.astype(float)
    m, sat, fabric = letters_mask(full)
    out, shade_src = fill(full, m)
    a_fill, a_edge = render_word(full.shape)
    # рисовать только по ткани: правая буква уходит под руку
    a_fill *= fabric
    a_edge *= fabric
    shade = np.clip(ndi.gaussian_filter(shade_src.mean(2), 6) / 235, 0.5, 1.05)[..., None]
    ink, rim = np.array([34, 34, 38.0]), np.array([150, 150, 152.0])
    out = out * (1 - a_edge[..., None]) + rim * shade * a_edge[..., None]
    out = out * (1 - a_fill[..., None]) + ink * shade * a_fill[..., None]
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    # Ванвлит (слева, тоже «RAPTORS») за кадром: левый край — x 180 в превью шириной 800
    x_l, y_t = int(180 * 3528 / 800), int(205 * 3528 / 800)
    w = 3528 - x_l
    img = img.crop((x_l, y_t, 3528, y_t + int(w * 9 / 16)))
    credit(img)
    img.save(OUT / "cover_mammoths.jpg", quality=90)
    print("→", OUT / "cover_mammoths.jpg")

if __name__ == "__main__":
    main(sys.argv[1])
