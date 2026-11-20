"""Схемы к статье про дело Кавая → articles/kawai/charts/chart{2,6,7,8}_*.png.

Запуск: ~/.virtualenvs/blog_env/bin/python articles/kawai/scripts/kawai_diagrams.py
Это не графики данных, а поясняющие схемы, поэтому matplotlib, а не altair.
Факты и даты сверяются с data/lac_timeline.csv (assert ниже);
подписи по-русски живут здесь, источник каждой — в data/sources.md.
"""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle, Wedge

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "charts"

# Палитра как у Шрёдера (schroder_salary.py)
SURFACE, INK, INK_MUTED, GRID = "#fcfcfb", "#0b0b0b", "#6f6e69", "#e8e7e3"
BLUE, ORANGE, GREEN, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})

W, H = 100, 62.5  # координаты холста; PNG 1200×750


def read(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


TIMELINE = {r["date"]: r for r in read("lac_timeline.csv")}


def canvas(title, subtitle, footer):
    fig = plt.figure(figsize=(10, 6.25), dpi=120)
    fig.patch.set_facecolor(SURFACE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    ax.text(3, H - 4, title, fontsize=21, weight="bold", va="top")
    ax.text(3, H - 9, subtitle, fontsize=12, color=INK_MUTED, va="top")
    ax.text(3, 1.5, footer, fontsize=8.5, color=INK_MUTED, va="bottom", linespacing=1.4)
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / name, facecolor=SURFACE)
    plt.close(fig)
    print("→", OUT / name)


def box(ax, x, y, w, h, text, fc=SURFACE, ec=INK, fs=11, weight="normal", color=INK, lw=1.4):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=fc, ec=ec, lw=lw))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, weight=weight, color=color, linespacing=1.3)


def arrow(ax, p, q, color=INK, lw=2, style="-|>", rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=16, color=color, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls, shrinkA=4, shrinkB=4))


# ---------------------------------------------------------------- 2. Деньги в обход потолка
def chart2():
    for d in ["2020-08", "2021-08", "2022-01", "2022-04"]:
        assert d in TIMELINE, d
    assert TIMELINE["2021-08"]["amount_usd"] == "18000000"
    assert TIMELINE["2022-01"]["amount_usd"] == "7000000"
    fig, ax = canvas(
        "Деньги в обход потолка",
        "Как, по выводам расследования, «Клипперс» доплачивали Каваю через партнёров клуба",
        "Суммы — по отчёту Wachtell Lipton от 02.09.2026, с. 17–29. Что клуб давал компаниям бизнес и ждал от них\n"
        "контрактов с Каваем, установлено; что консалтинг прямо финансировал выплаты, свидетель говорит про одну компанию.",
    )
    box(ax, 13, 30, 17, 8, "«Клипперс»", fs=15, weight="bold")
    box(ax, 87, 30, 17, 8, "Кавай\nЛеонард", fs=14, weight="bold")
    box(ax, 50, 42.5, 26, 7, "Boingo · Daktronics · Lockton\n2020–2021", fs=11, ec=ORANGE)
    box(ax, 50, 17.5, 26, 7, "Aspiration\n2021–2022", fs=11, ec=ORANGE)

    arrow(ax, (22, 30), (78, 30), color=INK_MUTED, lw=2)
    ax.text(50, 31, "зарплата по контракту — в рамках потолка", ha="center", va="bottom", fontsize=10,
            color=INK_MUTED)

    arrow(ax, (19, 34.5), (36, 42), color=ORANGE, lw=2.5, rad=-0.15)
    ax.text(4, 41.5, "консалтинг: \\$10 + \\$10 + \\$2 млн,\nзаказ табло для новой арены", ha="left",
            va="bottom", fontsize=9.5, color=INK, linespacing=1.3)
    arrow(ax, (64, 42), (81, 34.5), color=ORANGE, lw=2.5, rad=-0.15)
    ax.text(97, 41.5, "«спонсорство»: \\$18 млн,\nвыплачено к августу 2021", ha="right", va="bottom", fontsize=9.5,
            linespacing=1.3)

    arrow(ax, (19, 25.5), (36, 18), color=ORANGE, lw=2.5, rad=0.15)
    ax.text(4, 17.5, "договор по арене «Форум»:\n\\$7 млн в год «назад в бизнес»", ha="left", va="top",
            fontsize=9.5, linespacing=1.3)
    arrow(ax, (64, 18), (81, 25.5), color=ORANGE, lw=2.5, rad=0.15)
    ax.text(97, 17.5, "«спонсорство»: \\$7 млн деньгами\n+ \\$5 млн акциями в год, 4 года", ha="right", va="top",
            fontsize=9.5, linespacing=1.3)

    ax.text(13, 25, "на бумаге —\n«знакомство по просьбе\nкомпании»", ha="center", va="top", fontsize=9,
            color=INK_MUTED, style="italic", linespacing=1.3)
    save(fig, "chart2_money_loop.png")


# ---------------------------------------------------------------- 6. Норма без метанормы и с ней
def scales(ax, cx, tilt, left, right):
    """Весы: tilt > 0 — перевешивает левая чаша. left/right — (подпись чаши, [(груз, цвет), ...])."""
    import math
    py, arm, hang, pw = 42, 17, 17, 15
    ax.add_patch(Polygon([(cx - 5, 9), (cx + 5, 9), (cx, 13)], fc=INK_MUTED, ec="none"))
    ax.plot([cx, cx], [12, py], color=INK_MUTED, lw=3, solid_capstyle="round")
    dy = arm * math.tan(math.radians(tilt))
    ends = [(cx - arm, py - dy), (cx + arm, py + dy)]
    ax.plot([e[0] for e in ends], [e[1] for e in ends], color=INK, lw=3, solid_capstyle="round")
    ax.add_patch(Circle((cx, py), 1.0, fc=INK, ec="none"))
    for (ex, ey), (label, weights) in zip(ends, (left, right)):
        pan = ey - hang
        for sx in (ex - pw / 2 + 0.5, ex + pw / 2 - 0.5):
            ax.plot([ex, sx], [ey, pan], color=INK_MUTED, lw=1, zorder=1)
        ax.add_patch(Polygon([(ex - pw / 2, pan), (ex + pw / 2, pan), (ex + pw / 2 - 1.5, pan - 1.2),
                              (ex - pw / 2 + 1.5, pan - 1.2)], fc=INK, ec="none"))
        ax.text(ex, pan - 2.2, label, ha="center", va="top", fontsize=11, weight="bold")
        y = pan + 0.6
        for text, col in weights:
            h = 1.9 * (text.count("\n") + 1) + 0.8
            ax.add_patch(FancyBboxPatch((ex - pw / 2 + 0.75, y), pw - 1.5, h, boxstyle="round,pad=0,rounding_size=0.8",
                                        fc=col, ec="none", zorder=3))
            ax.text(ex, y + h / 2, text, ha="center", va="center", fontsize=8, zorder=4, color="white", weight="bold",
                    linespacing=1.15)
            y += h + 0.4


def chart6():
    fig, ax = canvas(
        "Зачем нужна метанорма?", "", "")
    ax.plot([50, 50], [7, 51], color=GRID, lw=1.5)
    ax.text(25, 49, "Без метанормы", ha="center", va="center", fontsize=15, weight="bold", color=INK_MUTED)
    ax.text(75, 49, "С метанормой", ha="center", va="center", fontsize=15, weight="bold", color=ORANGE)
    silent = [("наказывать\nдорого", INK_MUTED), ("нарушитель\nотомстит", INK_MUTED)]
    scales(ax, 25, 9, ("промолчать", silent), ("наказать", [("порядок\nв группе", BLUE)]))
    scales(ax, 75, -9, ("промолчать", silent[:2]),
           ("наказать", [("порядок\nв группе", BLUE), ("промолчал —\nсам нарушитель", ORANGE),
                         ("накажут\nи меня", ORANGE)]))
    save(fig, "chart6_metanorm.png")


# ---------------------------------------------------------------- 7. Докуда дотягивается лига
def chart7():
    fig, ax = canvas(
        "Вингспан Сильвера", "", "")
    # закон и налоги — общий круг, лига — внутри него
    ax.add_patch(FancyBboxPatch((3, 6), 94, 41, boxstyle="round,pad=0,rounding_size=4", fc="#f3f2ee", ec=INK_MUTED,
                                lw=1.4))
    ax.text(95, 44.5, "закон и налоги: суд, прокуратура, SEC, налоговая", ha="right", va="center", fontsize=10.5,
            color=INK_MUTED, weight="bold")
    ax.add_patch(Circle((33, 25.5), 19, fc="#e8f0fb", ec=BLUE, lw=2))
    ax.text(33, 41.5, "власть лиги", ha="center", va="center", fontsize=12, weight="bold", color=BLUE)
    # клуб: тонкая защита — устав лиги
    ax.add_patch(Circle((24, 26), 7, fc="none", ec=INK, lw=1, ls=(0, (2, 2))))
    box(ax, 24, 26, 10.5, 4, "«Клипперс»", fs=10.5, weight="bold")
    ax.text(24, 17.5, "5 пиков, \\$30 млн,\nотстранения", ha="center", va="top", fontsize=9, linespacing=1.3)
    # игрок: толстая защита — профсоюз
    ax.add_patch(Wedge((43, 26), 7.4, 0, 360, width=1.8, fc=GREEN, ec="none", alpha=0.8))
    box(ax, 43, 26, 8, 4, "Кавай", fs=11, weight="bold")
    ax.text(43, 36.3, "щит профсоюза", ha="center", va="center", fontsize=9, color=GREEN, weight="bold")
    ax.text(43, 16.8, "\\$700 тыс.", ha="center", va="top", fontsize=9)
    ax.text(24, 34.3, "устав лиги", ha="center", va="center", fontsize=9, color=INK_MUTED)
    # за пределами лиги
    box(ax, 72, 31, 24, 7, "Boingo · Daktronics · Lockton\nAspiration", fs=10, ec=ORANGE)
    ax.text(72, 25.5, "лига не наказывает;\nпрокуратура и SEC — уже интересуются", ha="center", va="top", fontsize=9,
            linespacing=1.3)
    box(ax, 72, 13, 16, 4, "Деннис Робертсон", fs=10, ec=ORANGE)
    ax.text(72, 9.3, "клубам запрещено иметь с ним дело", ha="center", va="top", fontsize=9)
    save(fig, "chart7_silver_reach.png")


# ---------------------------------------------------------------- 8. Комикс по мотивам «Нашей Russia»
SKIN, WALL, WINDOW, PINK, GOLD = "#e2b48e", "#336f48", "#dfe6e6", "#f3a9c6", "#d9a21b"
REF_SKIN, REF_SHIRT, REF_BAND = "#f3d6bd", "#1b1b1b", "#f2c230"  # судья — одинаково на всех панелях


def bubble(ax, x, y, text, tail, fs=11):
    ax.add_patch(Polygon([(x - 2, y - 2.2), (x + 2, y - 2.2), tail], fc="white", ec=INK, lw=1.2, zorder=5))
    box(ax, x, y, 24, 5.2, text, fc="white", ec=INK, fs=fs, weight="bold", lw=1.2)
    ax.add_patch(Rectangle((x - 2.3, y - 2.9), 4.6, 1.2, fc="white", ec="none", zorder=6))


def panel_bg(ax, x0, y0, w, h):
    ax.add_patch(Rectangle((x0, y0), w, h, fc=WALL, ec="none"))
    ax.add_patch(Rectangle((x0 + 2.5, y0 + 17), 7, 17, fc=WINDOW, ec="white", lw=2))
    ax.plot([x0 + 6, x0 + 6], [y0 + 17, y0 + 34], color="white", lw=2)
    ax.plot([x0 + 2.5, x0 + 9.5], [y0 + 25.5, y0 + 25.5], color="white", lw=2)


def head(ax, cx, hy, hair, beard=False, look=(0, 0.6), mouth="-", skin=SKIN):
    ax.add_patch(Rectangle((cx - 1.6, hy - 6.5), 3.2, 3, fc=skin, ec="none"))
    ax.add_patch(Circle((cx, hy), 4.2, fc=skin, ec="none"))
    ax.add_patch(Wedge((cx, hy + 1.9), 4.35, 0, 180, fc=hair, ec="none"))
    ax.add_patch(Wedge((cx, hy + 1.9), 4.35, 175, 215, fc=hair, ec="none"))
    if beard:
        ax.add_patch(Wedge((cx, hy + 0.3), 4.3, 190, 350, width=1.5, fc=hair, ec="none"))
        ax.plot([cx - 1.6, cx + 1.6], [hy - 1.2, hy - 1.2], color=hair, lw=3.5, solid_capstyle="round")
    if mouth == "o":
        ax.add_patch(Circle((cx, hy - 2.4), 0.75, fc="#7a2a2a", ec="none"))
    elif mouth == "smile":
        ax.add_patch(Wedge((cx, hy - 1.6), 1.4, 200, 340, width=0.35, fc="#7a2a2a", ec="none"))
    else:
        ax.plot([cx - 1, cx + 1], [hy - 2.4, hy - 2.4], color="#7a2a2a", lw=1.6)
    brow = INK if beard else "#a07a30"
    for ex in (cx - 1.5, cx + 1.5):
        ax.add_patch(Circle((ex, hy + 0.4), 0.85, fc="white", ec="none"))
        ax.add_patch(Circle((ex + look[0] * 0.5, hy + 0.4 + look[1] * 0.5), 0.42, fc=INK, ec="none"))
        ax.plot([ex - 0.9, ex + 0.9], [hy + 1.6, hy + 1.8], color=brow, lw=1.6)


def torso(ax, cx, y0, color, trim, skin=SKIN):
    ax.add_patch(Polygon([(cx - 10, y0), (cx + 10, y0), (cx + 9, y0 + 14), (cx + 4.5, y0 + 17),
                          (cx - 4.5, y0 + 17), (cx - 9, y0 + 14)], fc=color, ec="none"))
    ax.add_patch(Polygon([(cx - 2.6, y0 + 17), (cx + 2.6, y0 + 17), (cx, y0 + 13.5)], fc=skin, ec="none"))
    if trim:
        for sx in (-1, 1):
            ax.plot([cx + sx * 8.6, cx + sx * 9.6], [y0 + 13.5, y0], color=trim, lw=2.2)


def comic_man(ax, cx, raise_note, look, mouth):
    torso(ax, cx, 0, PINK, "white")
    ax.plot([cx - 2.6, cx - 0.5, cx + 1.2], [17, 9, 17], color="#c8302c", lw=1.4)
    if raise_note:
        ax.add_patch(Polygon([(cx + 7, 14), (cx + 9.8, 13), (cx + 10.6, 22.5), (cx + 8.2, 23)], fc=PINK, ec="none"))
        ax.plot([cx + 9.6, cx + 10.4], [13.4, 22.6], color="white", lw=1.6)
        ax.add_patch(Polygon([(cx + 7.4, 23.5), (cx + 12.8, 25.5), (cx + 11.6, 29.5), (cx + 6.2, 27.5)],
                             fc="#b8d3c0", ec="#6f8f7a", lw=1))
        ax.add_patch(Circle((cx + 9.4, 24), 1.5, fc=SKIN, ec="none"))
    head(ax, cx, 24, INK, beard=True, look=look, mouth=mouth)


def chart8():
    w, h = 30, 42
    W_IN, M, G, TOP, BOT = 8.0, 0.25, 0.15, 0.25, 0.45  # дюймы
    pw_in = (W_IN - 2 * M - G) / 2
    ph_in = pw_in * h / w
    H_IN = TOP + 2 * ph_in + G + BOT
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=120)
    fig.patch.set_facecolor(SURFACE)
    fig.text(M / W_IN, 0.15 / H_IN, "Перерисовано по мотивам скетча про футбол из «Нашей Russia» (ТНТ).",
             fontsize=8.5, color=INK_MUTED)
    axes = []
    for i in range(4):
        col, row = i % 2, i // 2
        left = M + col * (pw_in + G)
        bottom = BOT + (1 - row) * (ph_in + G)
        ax = fig.add_axes([left / W_IN, bottom / H_IN, pw_in / W_IN, ph_in / H_IN])
        ax.set_xlim(0, w)
        ax.set_ylim(0, h)
        ax.set_aspect("equal")
        ax.axis("off")
        panel_bg(ax, 0, 0, w, h)
        axes.append(ax)
    # 1. «…ысяча …ублей» — купюра поднята, глаза к потолку
    comic_man(axes[0], 16, True, (0.3, 1), "o")
    bubble(axes[0], w / 2, 37.5, "«…ысяча …ублей»", (15, 30))
    # 2. «Я — честный судья!» — блондин в чёрном, кубок
    ax = axes[1]
    ax.add_patch(Rectangle((21, 0), 9, 8, fc=BLUE, ec="none"))
    ax.add_patch(Polygon([(22.5, 18), (28.5, 18), (27, 13.5), (24, 13.5)], fc=GOLD, ec="none"))
    ax.add_patch(Rectangle((25, 9.5), 1, 4, fc=GOLD, ec="none"))
    ax.add_patch(Rectangle((23.5, 8), 4, 1.6, fc="#c0392b", ec="none"))
    for hx in (22.9, 28.1):
        ax.add_patch(Circle((hx, 16.4), 1.2, fc="none", ec=GOLD, lw=2))
    torso(ax, 13, 0, REF_SHIRT, None, skin=REF_SKIN)
    ax.add_patch(Rectangle((3, 0), 20, 2.2, fc=REF_BAND, ec="none"))
    head(ax, 13, 24, "#e6c27a", look=(0.6, 0), mouth="smile", skin=REF_SKIN)
    bubble(ax, w / 2, 37.5, "«Я — честный судья!»", (14, 30))
    # 3. «…ять …ысяч …ублей» — руки опущены, взгляд в сторону
    comic_man(axes[2], 16, False, (1, 0), "-")
    bubble(axes[2], w / 2, 37.5, "«…ять …ысяч …ублей»", (17, 30))
    # 4. Рукопожатие: розовое плечо слева, чёрное справа, ладонь судьи светлее, между ладонями купюра
    ax = axes[3]
    ax.add_patch(Circle((-2, 2), 12, fc=PINK, ec="none", zorder=3))
    ax.add_patch(Polygon([(1, 9), (7, 15), (14, 23), (10.5, 25.5), (3, 17), (-1, 13)], fc=PINK, ec="none",
                         zorder=3))
    ax.plot([2.5, 12], [16, 24.3], color="white", lw=2.5, zorder=3)
    ax.add_patch(Circle((32, 2), 12, fc=REF_SHIRT, ec="none", zorder=3))
    ax.add_patch(Polygon([(29, 9), (23, 15), (16, 23), (19.5, 25.5), (27, 17), (31, 13)], fc=REF_SHIRT, ec="none",
                         zorder=3))
    ax.add_patch(Rectangle((20, 0), 10, 2.2, fc=REF_BAND, ec="none", zorder=4))
    ax.add_patch(Polygon([(11, 26), (17.5, 28), (16.6, 32.5), (10.1, 30.5)], fc="#b8d3c0", ec="#6f8f7a", lw=1.2,
                         zorder=4))
    # ладонь бородача снизу, ладонь судьи сверху с большим пальцем поверх
    ax.add_patch(Ellipse((14.2, 25.3), 9, 6, angle=-15, fc=SKIN, ec="#b88a66", lw=1.2, zorder=5))
    ax.add_patch(Ellipse((16.4, 26.2), 8.5, 6.2, angle=20, fc=REF_SKIN, ec="#c9a585", lw=1.2, zorder=6))
    ax.add_patch(Ellipse((13.2, 28.2), 5, 1.9, angle=-10, fc=REF_SKIN, ec="#c9a585", lw=1.2, zorder=7))
    for dx in (0, 1.6, 3.2):
        ax.plot([16.2 + dx, 17.2 + dx], [23.6 + dx * 0.35, 26.4 + dx * 0.35], color="#c9a585", lw=1.1, zorder=7)
    save(fig, "chart8_comic.png")

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    chart2()
    chart6()
    chart7()
    chart8()
