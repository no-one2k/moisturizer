import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Второй апрон и середняки: как выросли зарплаты

    Проверка двух тезисов октября 2026-го. **Браун**: CBA-2023 хорошо для максимальщиков
    и плохо для середняков, полное и налоговое MLE почти никто не получает. **НБА**: с
    введения второго апрона число игроков то же, зарплаты выросли почти на \$1,3 млрд,
    около +30% «для всех классов». Бриф и гипотезы — `ideas/brief.md`.

    Сезоны — только итоги сезонов. **2021/22** — база: последний сезон, целиком сыгранный
    до ратификации CBA-2023 (26.04.2023); в конце 2022/23 ГМы уже знали новые правила.
    **2022/23** — правила стали известны к концу сезона; **2023/24** — CBA-2023
    действует, ограничения вводятся поэтапно; **2025/26** — все ограничения действуют.

    Данные — `articles/second_apron/data/`, реестр источников — `data/sources.md`.
    Пересборка: `scripts/fetch_salaries.py`, `scripts/fetch_mle.py`, `scripts/fetch_spotrac.py`.

    Порядок — как в статье: данные и сверки, «Общее для графиков», графики 1–3
    (1 — как читать Q-Q, 2 — немного статистической магии, 3 — настоящие данные),
    затем «Таблицы для выводов». Графики исследовательские (matplotlib): задача — увидеть форму данных.
    """)
    return


@app.cell
def _():
    import re
    from pathlib import Path

    import altair as alt
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import vl_convert as vlc

    DATA = Path(__file__).resolve().parents[1] / "data"
    return DATA, alt, np, pd, plt, re, vlc


@app.cell
def _():
    INK = "#0b0b0b"
    INK_MUTED = "#6f6e69"
    GRID = "#e8e7e3"
    # палитра Шрёдера; цвет закреплён за сезоном
    PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
    SEASONS = ["2021-22", "2022-23", "2023-24", "2025-26"]  # только итоги сезонов
    SEASON_COLOR = {"2021-22": PALETTE[6], "2022-23": PALETTE[3], "2023-24": PALETTE[0],
                    "2024-25": PALETTE[5], "2025-26": PALETTE[1]}
    SEASON_LABEL = {s: s.replace("-", "/") for s in SEASON_COLOR}


    def style_ax(ax):
        ax.grid(color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)


    def millions(x, _pos=None):
        return f"{x / 1e6:.0f}"

    return (
        GRID,
        INK,
        INK_MUTED,
        PALETTE,
        SEASONS,
        SEASON_COLOR,
        SEASON_LABEL,
        millions,
        style_ax,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Данные

    Лимиты — `cap_limits.csv`. Зарплаты — по файлу на сезон, итог сезона: строка —
    контракт игрока с командой; у двусторонних контрактов суммы нет (`TODO`). Для
    распределений строки складываются по игроку. **Пул сравнения** — игроки с суммой за
    сезон не ниже минимума новичка: так отсекаются 10-дневные контракты и хвосты
    отчисленных.
    """)
    return


@app.cell
def _(DATA, pd):
    cap = pd.read_csv(DATA / "cap_limits.csv").set_index("season")

    _files = {"2021-22": "salaries_2122.csv", "2022-23": "salaries_2223.csv",
              "2023-24": "salaries_2324.csv", "2025-26": "salaries_2526.csv"}
    contracts = pd.concat([pd.read_csv(DATA / f, dtype={"salary": str}) for f in _files.values()],
                          ignore_index=True)
    contracts["amount"] = pd.to_numeric(contracts["salary"], errors="coerce")  # TODO -> NaN

    mle = pd.read_csv(DATA / "mle_usage.csv")
    spotrac = pd.read_csv(DATA / "spotrac_team_totals.csv")
    rookie = pd.read_csv(DATA / "rookie_scale.csv")
    return cap, contracts, mle, rookie, spotrac


@app.cell(hide_code=True)
def _(DATA, cap, contracts, mle, mo, re, rookie, spotrac):
    # Каждая строка данных — с ключом и датой сверки, каждый ключ — в реестре.
    # Ключи лимитов живут в реестре Шрёдера: cap_limits.csv скопирован оттуда.
    def _keys_in(path):
        return set(re.findall(r"`([A-Z][A-Z0-9-]+)`", path.read_text(encoding="utf-8")))


    _registry = _keys_in(DATA / "sources.md")
    _schroder = _keys_in(DATA.parents[1] / "schroder" / "data" / "sources.md")
    _frames = {"contracts": contracts, "mle": mle, "spotrac": spotrac, "rookie": rookie}
    for _name, _df in _frames.items():
        assert _df["source_keys"].notna().all() and _df["verified_on"].notna().all(), _name
        _keys = {k for v in _df["source_keys"] for k in v.split(";")}
        assert _keys <= _registry, (_name, _keys - _registry)
    _cap_keys = {k for c in ["source_cap", "source_apron", "source_exceptions", "source_minimums", "source_max"]
                 for v in cap[c] for k in re.split("[;+]", v)} - {"n/a"}
    # HR-MLE-* записаны у Шрёдера диапазоном «HR-MLE-1718 … HR-MLE-2627»
    _missing = {k for k in _cap_keys if k not in _registry | _schroder and not re.fullmatch(r"HR-MLE-\d{4}", k)}
    assert not _missing, _missing
    mo.md(f"Ключи на месте: {len(_registry)} в реестре статьи, ключи лимитов — в реестре Шрёдера.")
    return


@app.cell
def _(SEASONS, cap, contracts):
    players = (contracts.dropna(subset=["amount"])
               .groupby(["season", "player_id"], as_index=False)
               .agg(player=("player", "first"), team=("team", "last"), salary=("amount", "sum")))
    players["cap_share"] = players["salary"] / players["season"].map(cap["salary_cap"])
    players["in_pool"] = players["salary"] >= players["season"].map(cap["vet_min_0y"])
    pool = {s: players.query("season == @s and in_pool")["salary"].to_numpy() for s in SEASONS}
    pool_share = {s: pool[s] / cap.loc[s, "salary_cap"] for s in SEASONS}
    return players, pool


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Сверки

    **Число игроков.** НБА: «число игроков в составах осталось прежним». Ниже — сколько
    строк и игроков в каждом сезоне, сколько из них двусторонних (без суммы), сколько в
    пуле сравнения, и сколько активных игроков насчитывает Spotrac.
    """)
    return


@app.cell
def _(SEASONS, SEASON_LABEL, contracts, pd, players, spotrac):
    _rows = []
    for _s in SEASONS:
        _c = contracts[contracts["season"] == _s]
        _p = players[players["season"] == _s]
        _rows.append({
            "сезон": SEASON_LABEL[_s],
            "строк": len(_c),
            "игроков": _c["player_id"].nunique(),
            "без суммы (two-way)": _c.loc[_c["amount"].isna(), "player_id"].nunique(),
            "с суммой": len(_p),
            "в пуле (≥ мин. новичка)": int(_p["in_pool"].sum()),
            "Spotrac active": int(spotrac.loc[spotrac["season"] == _s, "players_active"].sum()),
        })
    player_counts = pd.DataFrame(_rows).set_index("сезон")
    player_counts
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **BBR против Spotrac по командам.** Сумма зарплат BBR против `active + dead_cap`
    Spotrac. Показаны команды с расхождением больше 1%.
    """)
    return


@app.cell
def _(contracts, mo, pd, spotrac):
    _bbr = contracts.groupby(["season", "team"])["amount"].sum().rename("bbr")
    _sp = spotrac.assign(spotrac=spotrac["active"] + spotrac["dead_cap"]).set_index(["season", "team"])["spotrac"]
    team_check = pd.concat([_bbr, _sp], axis=1).reset_index()
    team_check["diff_pct"] = 100 * (team_check["bbr"] / team_check["spotrac"] - 1)
    _league = team_check.groupby("season")[["bbr", "spotrac"]].sum()
    _league["diff_pct"] = (100 * (_league["bbr"] / _league["spotrac"] - 1)).round(1)
    _league["команд с |diff| > 1%"] = team_check.assign(_big=team_check["diff_pct"].abs() > 1).groupby("season")["_big"].sum()
    mo.vstack([
        _league.style.format({"bbr": "{:,.0f}", "spotrac": "{:,.0f}"}),
        team_check.loc[team_check["diff_pct"].abs() > 1].sort_values(["season", "diff_pct"])
        .style.format({"bbr": "{:,.0f}", "spotrac": "{:,.0f}", "diff_pct": "{:+.1f}"}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **«+\$1,3 млрд и +30%».** НБА не говорит, какие сезоны сравнивает. Пересчёт по всем
    парам итогов сезонов по трём суммам: BBR, `active` Spotrac (без dead money) и
    `active + dead` Spotrac.
    """)
    return


@app.cell
def _(SEASONS, SEASON_LABEL, cap, contracts, pd, spotrac):
    _totals = pd.DataFrame({
        "BBR": contracts.groupby("season")["amount"].sum(),
        "Spotrac active": spotrac.groupby("season")["active"].sum(),
        "Spotrac active+dead": spotrac.assign(_t=spotrac["active"] + spotrac["dead_cap"]).groupby("season")["_t"].sum(),
    })
    _rows = []
    for _i, _a in enumerate(SEASONS):
        for _b in SEASONS[_i + 1:]:
            _row = {"пара": f"{SEASON_LABEL[_a]} → {SEASON_LABEL[_b]}",
                    "потолок": f"{100 * (cap.loc[_b, 'salary_cap'] / cap.loc[_a, 'salary_cap'] - 1):+.1f}%"}
            for _src in _totals.columns:
                _d = _totals.loc[_b, _src] - _totals.loc[_a, _src]
                _row[_src] = f"{_d / 1e9:+.2f} млрд ({100 * _d / _totals.loc[_a, _src]:+.1f}%)"
            _rows.append(_row)
    claim_check = pd.DataFrame(_rows).set_index("пара")
    claim_check
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Общее для графиков

    Перцентили 1–99 пула сравнения; середняки — от `MID_LO`-го до `MID_HI`-го перцентиля
    базы (по умолчанию 30–70). Везде, где нужен «рост для всех», — **+38%**: рост всей
    платёжки 2021/22 → 2025/26 (`GROWTH` ≈ 1,377), потолок вырос на столько же (+37,6%).
    «+30%» НБА — от другой базы, 2022/23 (`claim_check`).

    Выдуманные лиги (графики 1–2) строятся на настоящих зарплатах пула 2021/22 (`HYPO_BASE`):
    низ — места до `HYPO_LO`, середина — до `HYPO_HI`, верх — остальные.
    """)
    return


@app.cell
def _(SEASONS, cap, contracts, np, pool):
    PCTS = np.arange(1, 100)
    MID_LO, MID_HI = 30, 70  # «середняки» на Q-Q: перцентили базы
    BASE, END = "2021-22", "2025-26"
    quantiles = {s: np.percentile(pool[s], PCTS) for s in SEASONS}
    _payroll = contracts.groupby("season")["amount"].sum()
    GROWTH = _payroll[END] / _payroll[BASE]  # рост всей платёжки от базы, ≈ ×1,377: «+38%» на графиках


    def cap_growth(a, b):
        return cap.loc[b, "salary_cap"] / cap.loc[a, "salary_cap"]

    return BASE, END, GROWTH, MID_HI, MID_LO, PCTS, cap_growth, quantiles


@app.cell(hide_code=True)
def _(
    BASE,
    END,
    INK_MUTED,
    MID_HI,
    MID_LO,
    PALETTE,
    SEASON_LABEL,
    cap,
    millions,
    np,
    plt,
    pool,
    rookie,
):
    DECILES = np.arange(10, 100, 10)
    CBRT_TICKS = np.array([1, 2, 5, 10, 20, 30, 40, 50, 60]) * 1e6


    def mark_deciles(ax, x, y, color, labels=True):
        """Крупные точки на децилях кривой Q-Q; x, y — значения на перцентилях PCTS."""
        _i = DECILES - 1
        ax.scatter(x[_i], y[_i], s=30, color=color, edgecolor="white", lw=0.8, zorder=4)
        if labels:
            # нечётные — под кривой справа, чётные — над кривой слева: внизу децили тесно
            for _k, (_d, _xd, _yd) in enumerate(zip(DECILES, x[_i], y[_i])):
                ax.annotate(f"{_d}", (_xd, _yd), xytext=(5, -10) if _k % 2 == 0 else (-13, 4),
                            textcoords="offset points", fontsize=7, color=color)


    def mark_middle(ax, x):
        """Полоса середняков: базовые зарплаты от MID_LO-го до MID_HI-го перцентиля; x — на PCTS."""
        ax.axvspan(x[MID_LO - 1], x[MID_HI - 1], color=INK_MUTED, alpha=0.12, lw=0, zorder=0,
                   label=f"середняки: {MID_LO}–{MID_HI}-й перцентиль базы")


    def cbrt_axes(ax, bottom=0.8e6):
        """Обе оси — кубический корень: низ растянут, ноль конечен, прямые через ноль остаются прямыми."""
        for _set in (ax.set_xscale, ax.set_yscale):
            _set("function", functions=(np.cbrt, lambda v: np.power(v, 3)))
        ax.set_xticks(CBRT_TICKS[CBRT_TICKS <= 45e6])
        ax.set_yticks(CBRT_TICKS if bottom > 0 else np.r_[0, CBRT_TICKS])
        ax.set_xlim(left=0.8e6)
        ax.set_ylim(bottom=bottom)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(millions))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(millions))


    _r = rookie.set_index(["season", "pick"])["year1"]
    # Ромбы: настоящие суммы BASE → END — (подпись, сумма в базе, сумма в END)
    CONTRACT_MARKS = [("пик №10, 1-й год", _r.loc[(BASE, 10)], _r.loc[(END, 10)]),
                      ("налоговое MLE", cap.loc[BASE, "mle_taxpayer"], cap.loc[END, "mle_taxpayer"]),
                      ("полное MLE (мид-левел)", cap.loc[BASE, "mle_non_taxpayer"], cap.loc[END, "mle_non_taxpayer"]),
                      ("детская максималка, 25%", cap.loc[BASE, "max_25"], cap.loc[END, "max_25"])]


    def mark_contracts(ax, offsets=(((40, -48), "left"), ((70, -22), "left"), ((40, -60), "left"),
                                    ((-12, 14), "right"))):
        """Ромбы настоящих сумм BASE → END: пик №10 (1-й год), оба MLE, детская максималка.
        По X — сумма в базе, по Y — в END; offsets — смещение и выравнивание подписи каждого ромба."""
        for _i, ((_name, _v0, _v1), (_off, _ha)) in enumerate(zip(CONTRACT_MARKS, offsets)):
            ax.axvline(_v0, color=PALETTE[3], lw=0.8, ls="--", zorder=1)
            ax.scatter([_v0], [_v1], s=60, marker="D", color=PALETTE[3], edgecolor="white", zorder=5,
                       label=f"настоящие суммы: {SEASON_LABEL[BASE]} → {SEASON_LABEL[END]}" if _i == 0 else None)
            ax.annotate(f"{_name}\n{SEASON_LABEL[BASE]}: ${_v0 / 1e6:.2f} млн ({100 * (pool[BASE] < _v0).mean():.0f}-й перц.)\n"
                        f"{SEASON_LABEL[END]}: ${_v1 / 1e6:.2f} млн ({100 * (pool[END] < _v1).mean():.0f}-й перц.)",
                        (_v0, _v1), xytext=_off, textcoords="offset points", ha=_ha, fontsize=8, color=PALETTE[3],
                        arrowprops=dict(arrowstyle="-", color=PALETTE[3], lw=0.6))

    return (
        CONTRACT_MARKS,
        DECILES,
        cbrt_axes,
        mark_contracts,
        mark_deciles,
        mark_middle,
    )


@app.cell(hide_code=True)
def _(BASE, MID_HI, MID_LO, np, pool):
    HYPO_BASE = np.sort(pool[BASE])
    HYPO_N = len(HYPO_BASE)
    HYPO_LO, HYPO_HI = int(MID_LO / 100 * HYPO_N), int(MID_HI / 100 * HYPO_N)
    return HYPO_BASE, HYPO_HI, HYPO_LO, HYPO_N


@app.cell
def _(GROWTH, mo):
    mo.md(rf"""
    ## График 1. Как читать Q-Q: «всем +{100 * (GROWTH - 1):.0f}% ± шум» (выдумано)

    Q-Q: по X — зарплата на перцентиле в базе 2021/22, по Y — на том же перцентиле
    «после». Здесь «после» выдумано: каждый игрок получил +{100 * (GROWTH - 1):.0f}% (как вся
    платёжка 2021/22 → 2025/26) и случайный шум (±15%, логнормальный), ниже минимума никто
    не опустился. Если всем дали поровну, точки идут вдоль пунктира y = {GROWTH:.2f}x.
    Крупные точки — децили, серая полоса — середняки. Ромбы — настоящие суммы 2021/22 →
    2025/26: пик №10 на первом году, налоговое и полное MLE, детская максималка. Оси —
    кубический корень: низ растянут, но ноль конечен, прямые через ноль остаются прямыми.
    """)
    return


@app.cell
def _(
    GROWTH,
    HYPO_BASE,
    HYPO_N,
    INK,
    INK_MUTED,
    PALETTE,
    PCTS,
    cbrt_axes,
    mark_contracts,
    mark_deciles,
    mark_middle,
    np,
    plt,
    style_ax,
):
    _rng = np.random.default_rng(2026)
    hypo_noise = np.maximum(HYPO_BASE * GROWTH * np.exp(_rng.normal(0, 0.15, HYPO_N)), GROWTH * HYPO_BASE[0])
    _x = np.percentile(HYPO_BASE, PCTS)
    _y = np.percentile(hypo_noise, PCTS)
    _g = f"+{100 * (GROWTH - 1):.0f}%"

    fig_1, _ax = plt.subplots(figsize=(12, 6))
    cbrt_axes(_ax)
    mark_middle(_ax, _x)
    _ax.plot(_x[[0, -1]], _x[[0, -1]], color=INK_MUTED, lw=1, label="без изменений")
    _ax.plot(_x[[0, -1]], GROWTH * _x[[0, -1]], color=INK, lw=1, ls=":", label=f"{_g} всем")
    _ax.plot(_x, _y, color=PALETTE[1], lw=1.8, marker="o", ms=2.5, label=f"{_g} ± шум")
    mark_deciles(_ax, _x, _y, PALETTE[1])
    _ax.scatter([], [], s=30, color=PALETTE[1], edgecolor="white", label="децили: 10-й … 90-й перцентиль")
    mark_contracts(_ax)
    _ax.set_xlabel("до (2021/22), \$ млн")
    _ax.set_ylabel("после, \$ млн")
    _ax.legend(frameon=False, loc="upper left")
    style_ax(_ax)
    fig_1.suptitle(f"График 1. Q-Q, если бы всем дали {_g} ± шум (выдумано); где пик №10, оба MLE и детская максималка",
                   x=0.06, ha="left", fontsize=13)
    fig_1.tight_layout()
    fig_1
    return (hypo_noise,)


@app.cell(hide_code=True)
def _(
    GROWTH,
    MID_HI,
    MID_LO,
    TRICK_GAP,
    TRICK_LOW_SPREAD,
    TRICK_MAX_LOSERS,
    TRICK_RICH_BAND,
    TRICK_TOP_SPREAD,
    mo,
):
    mo.md(rf"""
    ## График 2. Немного статистической магии (выдумано)

    Фиксируя несколько параметров распределения, мы не управляем его формой. Здесь
    фиксируются ровно те, о которых говорит НБА: число игроков то же, рост среднего для всех
    ×{GROWTH:.3f} и такой же рост среднего у каждой из трёх групп — низа (до {MID_LO}-го
    перцентиля базы), середины и верха (от {MID_HI}-го). Остальное — фокус в три шага, каждый
    игрок остаётся на своём месте в очереди:

    1. Верх выравнивается: самый дорогой и самый дешёвый контракт отличаются на
       \${TRICK_TOP_SPREAD / 1e6:.1f} млн.
    2. Низ выравнивается так же, разброс \${TRICK_LOW_SPREAD / 1e6:.1f} млн.
    3. Середине остаётся коридор между низом и верхом (с зазором \${TRICK_GAP / 1e6:.2f} млн).
       Верхние `TRICK_K` середняков уходят в полосу шириной \${TRICK_RICH_BAND / 1e6:.0f} млн под
       верхом. Остальные остаются при своих, но не ниже пола коридора и не выше `TRICK_C`;
       `TRICK_C` подобран так, чтобы среднее середины выросло ×{GROWTH:.3f}. `TRICK_K` —
       наибольшее, при котором в долларах теряют не больше {TRICK_MAX_LOSERS:.0%} середняков:
       так основная масса стоит как можно ближе к низу.
    """)
    return


@app.cell(hide_code=True)
def _(GROWTH, HYPO_BASE, HYPO_HI, HYPO_LO, np, pd):
    TRICK_TOP_SPREAD = 2e6  # верх: самый дорогой минус самый дешёвый
    TRICK_LOW_SPREAD = 0.5e6  # низ: то же
    TRICK_GAP = 0.25e6  # зазор между группами
    TRICK_RICH_BAND = 2e6  # дорогие середняки — в полосе такой ширины под верхом
    TRICK_MAX_LOSERS = 0.10  # доля середняков, у которых можно урезать зарплату в долларах


    def trick_flatten(base, spread):
        """Выровнять группу: среднее ×GROWTH, разброс spread; base отсортирован, порядок сохраняется."""
        return GROWTH * base.mean() + np.linspace(-spread / 2, spread / 2, len(base))


    def trick_middle(mid, floor, ceil):
        """Середина: среднее ×GROWTH, все в [floor, ceil], две группы. Верхние k — в полосе
        TRICK_RICH_BAND под ceil; остальные — своя зарплата, зажатая в [floor, c], c — под среднее.
        k — наибольшее, при котором в долларах теряют не больше TRICK_MAX_LOSERS. Возвращает (раздача, k, c)."""
        best = None
        for k in range(1, len(mid)):
            rich = np.linspace(ceil - TRICK_RICH_BAND, ceil, k)
            main = mid[:-k]
            need = GROWTH * mid.sum() - rich.sum()
            if not floor * len(main) <= need <= np.maximum(main, floor).sum():
                continue
            lo, hi = floor, main.max()
            for _ in range(60):  # сумма растёт с c — бисекция
                c = (lo + hi) / 2
                lo, hi = (c, hi) if np.clip(main, floor, c).sum() < need else (lo, c)
            after = np.r_[np.clip(main, floor, c), rich]
            if np.mean(after < mid) <= TRICK_MAX_LOSERS:
                best = (after, k, c)
        return best


    _lo, _mid, _hi = HYPO_BASE[:HYPO_LO], HYPO_BASE[HYPO_LO:HYPO_HI], HYPO_BASE[HYPO_HI:]
    _lo_a, _hi_a = trick_flatten(_lo, TRICK_LOW_SPREAD), trick_flatten(_hi, TRICK_TOP_SPREAD)
    _mid_a, TRICK_K, TRICK_C = trick_middle(_mid, _lo_a.max() + TRICK_GAP, _hi_a.min() - TRICK_GAP)
    assert _lo_a.max() < _mid_a.min() and _mid_a.max() < _hi_a.min()
    trick_steps = {
        "1. Выровняли верх": np.r_[GROWTH * _lo, GROWTH * _mid, _hi_a],
        "2. Выровняли низ": np.r_[_lo_a, GROWTH * _mid, _hi_a],
        "3. Переложили середину": np.r_[_lo_a, _mid_a, _hi_a],
    }
    for _a in trick_steps.values():
        assert np.all(np.diff(_a) >= 0)  # каждый на своём месте в очереди

    TRICK_GROUPS = {"низ": slice(0, HYPO_LO), "середина": slice(HYPO_LO, HYPO_HI), "верх": slice(HYPO_HI, None)}
    _mid_ratio = {_n: _a[HYPO_LO:HYPO_HI] / _mid for _n, _a in trick_steps.items()}
    trick_check = pd.DataFrame({
        _n: {"игроков": len(_a),
             "сумма, рост %": round((_a.sum() / HYPO_BASE.sum() - 1) * 100, 1),
             **{f"{_g}, рост среднего %": round((_a[_sl].mean() / HYPO_BASE[_sl].mean() - 1) * 100, 1)
                for _g, _sl in TRICK_GROUPS.items()},
             **{f"{_g}, разброс, млн": round(np.ptp(_a[_sl]) / 1e6, 2) for _g, _sl in TRICK_GROUPS.items()},
             "середняки: прибавка меньше средней, %": round(np.mean(_mid_ratio[_n] < GROWTH - 1e-9) * 100),
             "середняки: без прибавки, %": round(np.mean(np.isclose(_mid_ratio[_n], 1)) * 100),
             "середняки: зарплата упала, %": round(np.mean(_mid_ratio[_n] < 1 - 1e-9) * 100)}
        for _n, _a in trick_steps.items()}).T
    trick_check
    return (
        TRICK_GAP,
        TRICK_GROUPS,
        TRICK_LOW_SPREAD,
        TRICK_MAX_LOSERS,
        TRICK_RICH_BAND,
        TRICK_TOP_SPREAD,
        trick_steps,
    )


@app.cell(hide_code=True)
def _(
    GROWTH,
    HYPO_BASE,
    HYPO_HI,
    HYPO_LO,
    INK,
    INK_MUTED,
    PALETTE,
    PCTS,
    TRICK_GROUPS,
    cbrt_axes,
    mark_middle,
    np,
    plt,
    style_ax,
    trick_steps,
):
    fig_2, _axes = plt.subplots(3, 1, figsize=(12, 18), sharex=True, sharey=True)
    _x = np.percentile(HYPO_BASE, PCTS)
    _gr = f"+{100 * (GROWTH - 1):.0f}%"
    _prev = GROWTH * HYPO_BASE
    for _ax, (_name, _after) in zip(_axes, trick_steps.items()):
        cbrt_axes(_ax)
        mark_middle(_ax, _x)
        _ax.plot(_x[[0, -1]], _x[[0, -1]], color=INK_MUTED, lw=1, label="без изменений")
        _ax.plot(_x[[0, -1]], GROWTH * _x[[0, -1]], color=INK, lw=1, ls=":", label=f"{_gr} всем")
        _ax.plot(_x, np.percentile(_prev, PCTS), color=PALETTE[0], lw=1.2, alpha=0.5, label="было")
        _ax.plot(_x, np.percentile(_after, PCTS), color=PALETTE[1], lw=1.8, marker="o", ms=2.5, label="стало")
        for _g, _sl in TRICK_GROUPS.items():
            _mx, _my = HYPO_BASE[_sl].mean(), _after[_sl].mean()
            _ax.scatter([_mx], [_my], s=70, marker="s", color=PALETTE[2], edgecolor="white", zorder=5,
                        label="среднее группы" if _g == "низ" else None)
            _ax.annotate(f"{_g}: +{100 * (_my / _mx - 1):.0f}%", (_mx, _my), xytext=(8, -14),
                         textcoords="offset points", fontsize=8, color=PALETTE[2])
        _r = _after[HYPO_LO:HYPO_HI] / HYPO_BASE[HYPO_LO:HYPO_HI]
        _ax.set_title(f"{_name}\nсередняки: прибавка меньше {_gr} у {np.mean(_r < GROWTH - 1e-9):.0%}, "
                      f"зарплата упала у {np.mean(_r < 1 - 1e-9):.0%}", loc="left", fontsize=10)
        _ax.set_ylabel("после, \\$ млн")
        style_ax(_ax)
        _prev = _after
    _axes[-1].set_xlabel("до (2021/22), \\$ млн")
    _axes[0].legend(frameon=False, loc="upper left", fontsize=8)
    fig_2.suptitle(f"График 2. Немного статистической магии (выдумано):\nигроков столько же, у всех и у каждой группы среднее {_gr},\n"
                   "а середина разъехалась на две группы", x=0.06, ha="left", fontsize=13)
    fig_2.tight_layout(rect=(0, 0, 1, 0.97))
    fig_2
    return


@app.cell(hide_code=True)
def _(BASE, END, GROWTH, cap_growth, mo):
    mo.md(rf"""
    ## График 3. Q-Q на настоящих данных: 2021/22 → 2025/26

    Перцентили 1–99 пула сравнения: по оси X — зарплата на перцентиле в базе 2021/22, по
    оси Y — на том же перцентиле в 2025/26. Пунктир — +{100 * (GROWTH - 1):.0f}% всем: так
    выросли вся платёжка (×{GROWTH:.3f}) и потолок (×{cap_growth(BASE, END):.3f}). Децили,
    полоса середняков и ромбы — как на графике 1. Оси — кубический корень.
    """)
    return


@app.cell(hide_code=True)
def _(
    BASE,
    END,
    GROWTH,
    INK,
    INK_MUTED,
    SEASON_COLOR,
    SEASON_LABEL,
    cbrt_axes,
    mark_contracts,
    mark_deciles,
    mark_middle,
    plt,
    quantiles,
    style_ax,
):
    fig_3, _ax = plt.subplots(figsize=(12, 6))
    _x, _y = quantiles[BASE], quantiles[END]
    cbrt_axes(_ax)
    mark_middle(_ax, _x)
    _ax.plot(_x[[0, -1]], _x[[0, -1]], color=INK_MUTED, lw=1, label="без изменений")
    _ax.plot(_x[[0, -1]], GROWTH * _x[[0, -1]], color=INK, lw=1, ls=":",
             label=f"+{100 * (GROWTH - 1):.0f}% всем: как платёжка и потолок")
    _ax.plot(_x, _y, color=SEASON_COLOR[END], lw=1.8, marker="o", ms=2.5, label=SEASON_LABEL[END])
    mark_deciles(_ax, _x, _y, SEASON_COLOR[END])
    _ax.scatter([], [], s=30, color=SEASON_COLOR[END], edgecolor="white", label="децили: 10-й … 90-й перцентиль")
    mark_contracts(_ax)
    _ax.set_xlabel(f"{SEASON_LABEL[BASE]}, \$ млн")
    _ax.set_ylabel(f"{SEASON_LABEL[END]}, \$ млн")
    _ax.legend(frameon=False, loc="upper left")
    style_ax(_ax)
    fig_3.suptitle(f"График 3. Q-Q зарплат на настоящих данных: {SEASON_LABEL[BASE]} → {SEASON_LABEL[END]}",
                   x=0.06, ha="left", fontsize=13)
    fig_3.tight_layout()
    fig_3
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Публикационные графики

    Altair, русские подписи; только графики с «нужен: да» в ревизии. Оси — кубический корень
    (`pow`, показатель 1/3), суммы в \$ млн. PNG ×2 — в `articles/second_apron/charts/`.
    """)
    return


@app.cell(hide_code=True)
def _(
    CONTRACT_MARKS,
    DECILES,
    GRID,
    GROWTH,
    INK,
    INK_MUTED,
    PALETTE,
    alt,
    np,
    pd,
    vlc,
):
    PUB_FONT = "Noto Sans"
    # Размер вида в пикселях; PNG экспортируется с масштабом 2
    PUB_WIDTH, PUB_HEIGHT = 818, 460
    QQ_TICKS = [1, 2, 5, 10, 20, 30, 40, 60]
    QQ_X_MAX, QQ_Y_MAX = 45, 65
    QQ_GUIDES = ["без изменений", f"+{100 * (GROWTH - 1):.0f}% всем"]
    CONTRACT_SHORT = ["пик №10", "налоговое MLE", "полное MLE", "детская максималка"]


    def halo_text(chart, **props):
        """Подпись с белой обводкой: читается поверх линий и сетки."""
        return [
            chart.mark_text(**props, fill="white", stroke="white", strokeWidth=4, strokeJoin="round"),
            chart.mark_text(**props),
        ]


    def pub_config(chart):
        return (
            chart.configure(font=PUB_FONT, background="white", padding=12)
            .configure_view(stroke=None)
            .configure_title(
                anchor="start", fontSize=20, fontWeight=600, color=INK,
                subtitleFontSize=12, subtitleColor=INK_MUTED, offset=12, subtitlePadding=6,
            )
            .configure_axis(
                labelColor=INK_MUTED, titleColor=INK_MUTED, labelFontSize=12, titleFontSize=12,
                titleFontWeight="normal", gridColor=GRID, domainColor=GRID, ticks=False, labelPadding=6,
            )
            .configure_legend(
                labelColor=INK, labelFontSize=12, orient="bottom", title=None, columnPadding=24, labelLimit=0
            )
        )


    def save_png(chart, path):
        """PNG ×2 через vl-convert с русской локалью чисел; возвращает (ширина, высота)."""
        png = vlc.vegalite_to_png(chart.to_json(), scale=2, format_locale="ru-RU")
        path.write_bytes(png)
        return int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")


    def ru(v):
        return f"{v:.1f}".replace(".", ",")


    def qq_enc(x_title, y_title):
        """Оси Q-Q в $ млн, обе — кубический корень; один и тот же объект на все слои вида."""
        _scale = dict(type="pow", exponent=1 / 3, nice=False, clamp=True)
        return (alt.X("x:Q", title=x_title, scale=alt.Scale(domain=[0.8, QQ_X_MAX], **_scale),
                      axis=alt.Axis(values=QQ_TICKS[:-1])),
                alt.Y("y:Q", title=y_title, scale=alt.Scale(domain=[0.8, QQ_Y_MAX], **_scale),
                      axis=alt.Axis(values=QQ_TICKS)))


    def qq_keys(*series):
        """Общий ключ линий внизу: series — (подпись, цвет, штрих); первыми идут «без изменений» и «+38% всем»."""
        _all = [(QQ_GUIDES[0], INK_MUTED, [1, 0]), (QQ_GUIDES[1], INK, [2, 3]), *series]
        _names = [s[0] for s in _all]
        return (alt.Color("s:N", scale=alt.Scale(domain=_names, range=[s[1] for s in _all]),
                          legend=alt.Legend(symbolStrokeWidth=2.5, symbolSize=300)),
                alt.StrokeDash("s:N", scale=alt.Scale(domain=_names, range=[s[2] for s in _all]), legend=None))


    def qq_frame(enc, keys, x_band):
        """Общие слои: полоса середняков, «без изменений» и «+38% всем»."""
        _x, _y = enc
        _band = alt.Chart(pd.DataFrame({"x": [x_band[0]], "x2": [x_band[1]]})).mark_rect(
            color=INK_MUTED, opacity=0.12).encode(x=_x, x2="x2:Q")
        _mid = ((np.cbrt(x_band[0]) + np.cbrt(x_band[1])) / 2) ** 3
        _band_label = halo_text(alt.Chart(pd.DataFrame({"x": [_mid], "y": [0.92 * QQ_Y_MAX], "t": ["середняки"]}))
                                .encode(x=_x, y=_y, text="t:N"), color=INK_MUTED, fontSize=12)
        _ends = np.array([0.8, QQ_X_MAX])
        _guides = pd.DataFrame({"x": np.r_[_ends, _ends], "y": np.r_[_ends, GROWTH * _ends],
                                "s": [QQ_GUIDES[0]] * 2 + [QQ_GUIDES[1]] * 2})
        return [_band, *_band_label,
                alt.Chart(_guides).mark_line(strokeWidth=1.2).encode(x=_x, y=_y, color=keys[0], strokeDash=keys[1])]


    def qq_line(enc, keys, x, y, name):
        _df = pd.DataFrame({"x": x / 1e6, "y": y / 1e6, "s": name})
        return alt.Chart(_df).mark_line(strokeWidth=2.5).encode(x=enc[0], y=enc[1], color=keys[0], strokeDash=keys[1])


    def qq_deciles(enc, x, y, color):
        _i = DECILES - 1
        _df = pd.DataFrame({"x": x[_i] / 1e6, "y": y[_i] / 1e6, "t": [str(d) for d in DECILES]})
        return [alt.Chart(_df).mark_point(filled=True, size=70, color=color, stroke="white", strokeWidth=1,
                                          opacity=1).encode(x=enc[0], y=enc[1]),
                *halo_text(alt.Chart(_df).encode(x=enc[0], y=enc[1], text="t:N"), align="left", dx=7, dy=10,
                           fontSize=11, color=color)]


    def qq_contracts(enc, placement):
        """Ромбы настоящих сумм BASE → END; placement — (dx, dy, align) подписи каждого ромба."""
        _layers = []
        for (_n, _v0, _v1), _short, (_dx, _dy, _al) in zip(CONTRACT_MARKS, CONTRACT_SHORT, placement):
            _df = pd.DataFrame({"x": [_v0 / 1e6], "y": [_v1 / 1e6], "t": [f"{_short}: {ru(_v0 / 1e6)} → {ru(_v1 / 1e6)}"]})
            _c = alt.Chart(_df).encode(x=enc[0], y=enc[1])
            _layers += [_c.mark_point(shape="diamond", filled=True, size=110, color=PALETTE[3], stroke="white",
                                      strokeWidth=1, opacity=1),
                        *halo_text(_c.encode(text="t:N"), align=_al, dx=_dx, dy=_dy, fontSize=11, color=PALETTE[3])]
        return _layers

    return (
        PUB_HEIGHT,
        PUB_WIDTH,
        halo_text,
        pub_config,
        qq_contracts,
        qq_deciles,
        qq_enc,
        qq_frame,
        qq_keys,
        qq_line,
        save_png,
    )


@app.cell(hide_code=True)
def _(
    GROWTH,
    HYPO_BASE,
    MID_HI,
    MID_LO,
    PALETTE,
    PCTS,
    PUB_HEIGHT,
    PUB_WIDTH,
    alt,
    hypo_noise,
    np,
    pub_config,
    qq_contracts,
    qq_deciles,
    qq_enc,
    qq_frame,
    qq_keys,
    qq_line,
):
    _x, _y = np.percentile(HYPO_BASE, PCTS), np.percentile(hypo_noise, PCTS)
    _enc = qq_enc("до (2021/22), $ млн", "после, $ млн")
    _keys = qq_keys(("после", PALETTE[1], [1, 0]))
    pub_chart_1 = pub_config(alt.layer(
        *qq_frame(_enc, _keys, (_x[MID_LO - 1] / 1e6, _x[MID_HI - 1] / 1e6)),
        qq_line(_enc, _keys, _x, _y, "после"),
        *qq_contracts(_enc, [(-9, -10, "right"), (9, 14, "left"), (-9, -10, "right"), (-9, -10, "right")]),
        *qq_deciles(_enc, _x, _y, PALETTE[1]),
    ).properties(
        title=alt.TitleParams("Что если всем сёстрам по серьгам", subtitle=[
            f"Выдумано: каждому +{100 * (GROWTH - 1):.0f}% и немного случайного шума. Самая большая зарплата «до» — против "
            "самой большой «после» и так далее;",
            "крупные точки — децили. Ромбы — настоящие суммы 2021/22 → 2025/26, в $ млн."]),
        width=PUB_WIDTH, height=PUB_HEIGHT))
    pub_chart_1
    return (pub_chart_1,)


@app.cell(hide_code=True)
def _(
    GROWTH,
    HYPO_BASE,
    HYPO_HI,
    HYPO_LO,
    MID_HI,
    MID_LO,
    PALETTE,
    PCTS,
    PUB_WIDTH,
    TRICK_GROUPS,
    alt,
    halo_text,
    np,
    pd,
    pub_config,
    qq_enc,
    qq_frame,
    qq_keys,
    trick_steps,
):
    _x = np.percentile(HYPO_BASE, PCTS)
    _band = (_x[MID_LO - 1] / 1e6, _x[MID_HI - 1] / 1e6)
    _mid = slice(HYPO_LO, HYPO_HI)
    _n_mid = HYPO_HI - HYPO_LO
    _keys = qq_keys(("было", PALETTE[0], [1, 0]), ("стало", PALETTE[1], [1, 0]))
    _prev = GROWTH * HYPO_BASE
    _panels = []
    for _k, (_name, _after) in enumerate(trick_steps.items()):
        _enc = qq_enc("до (2021/22), $ млн" if _k == len(trick_steps) - 1 else None, "после, $ млн")
        _lines = pd.concat([pd.DataFrame({"x": _x / 1e6, "y": np.percentile(_s, PCTS) / 1e6, "s": _lab})
                            for _s, _lab in [(_prev, "было"), (_after, "стало")]])
        _means = pd.DataFrame([{"x": HYPO_BASE[_sl].mean() / 1e6, "y": _after[_sl].mean() / 1e6,
                                "t": f"{_g}: +{100 * (_after[_sl].mean() / HYPO_BASE[_sl].mean() - 1):.0f}%"}
                               for _g, _sl in TRICK_GROUPS.items()])
        _r = _after[_mid] / HYPO_BASE[_mid]
        _less, _down = int((_r < GROWTH - 1e-9).sum()), int((_r < 1 - 1e-9).sum())
        _sub = (f"середняки: у {_less} из {_n_mid} прибавка меньше +{100 * (GROWTH - 1):.0f}%, у {_down} зарплата упала"
                if _less else f"середняки: всем ровно +{100 * (GROWTH - 1):.0f}%")
        _panels.append(alt.layer(
            *qq_frame(_enc, _keys, _band),
            alt.Chart(_lines).mark_line(strokeWidth=2.5).encode(
                x=_enc[0], y=_enc[1], color=_keys[0], strokeDash=_keys[1],
                opacity=alt.condition("datum.s == 'было'", alt.value(0.45), alt.value(1))),
            alt.Chart(_means).mark_square(size=110, color=PALETTE[2], stroke="white", strokeWidth=1, opacity=1)
            .encode(x=_enc[0], y=_enc[1]),
            *halo_text(alt.Chart(_means).encode(x=_enc[0], y=_enc[1], text="t:N"), align="left", dx=9, dy=12,
                       fontSize=12, color=PALETTE[2]),
        ).properties(title=alt.TitleParams(_name, subtitle=_sub, fontSize=15), width=PUB_WIDTH, height=300))
        _prev = _after
    pub_chart_2 = pub_config(alt.vconcat(*_panels, spacing=28).properties(
        title=alt.TitleParams("Что если кому-то всё, а кому-то ничего", subtitle=[
            f"Выдуманная лига: игроков столько же, у всех и у каждой группы — низа, середины и верха — "
            f"среднее +{100 * (GROWTH - 1):.0f}%.",
            "Квадраты — средние групп. Каждый шаг меняет то, что получилось на прошлом."])))
    pub_chart_2
    return (pub_chart_2,)


@app.cell(hide_code=True)
def _(
    BASE,
    END,
    MID_HI,
    MID_LO,
    PUB_HEIGHT,
    PUB_WIDTH,
    SEASON_COLOR,
    SEASON_LABEL,
    alt,
    pub_config,
    qq_contracts,
    qq_deciles,
    qq_enc,
    qq_frame,
    qq_keys,
    qq_line,
    quantiles,
):
    _x, _y = quantiles[BASE], quantiles[END]
    _enc = qq_enc(f"{SEASON_LABEL[BASE]}, $ млн", f"{SEASON_LABEL[END]}, $ млн")
    _keys = qq_keys((SEASON_LABEL[END], SEASON_COLOR[END], [1, 0]))
    pub_chart_3 = pub_config(alt.layer(
        *qq_frame(_enc, _keys, (_x[MID_LO - 1] / 1e6, _x[MID_HI - 1] / 1e6)),
        qq_line(_enc, _keys, _x, _y, SEASON_LABEL[END]),
        *qq_contracts(_enc, [(-9, -10, "right"), (9, 14, "left"), (-9, -10, "right"), (-9, -10, "right")]),
        *qq_deciles(_enc, _x, _y, SEASON_COLOR[END]),
    ).properties(
        title=alt.TitleParams("Как оно на самом деле", subtitle=[
            f"Зарплата на одном и том же перцентиле: {SEASON_LABEL[BASE]} против {SEASON_LABEL[END]}. "
            "Крупные точки — децили.",
            f"Ромбы — настоящие суммы {SEASON_LABEL[BASE]} → {SEASON_LABEL[END]}, в $ млн."]),
        width=PUB_WIDTH, height=PUB_HEIGHT))
    pub_chart_3
    return (pub_chart_3,)


@app.cell(hide_code=True)
def _(DATA, pd, pub_chart_1, pub_chart_2, pub_chart_3, save_png):
    # Экспорт публикационных графиков: PNG ×2 в articles/second_apron/charts/
    _charts = DATA.parent / "charts"
    _charts.mkdir(exist_ok=True)
    pd.DataFrame([(_name, *save_png(_chart, _charts / _name)) for _name, _chart in {
        "chart1_qq_equal_growth.png": pub_chart_1,
        "chart2_qq_trick.png": pub_chart_2,
        "chart3_qq_real.png": pub_chart_3,
    }.items()], columns=["файл", "ширина", "высота"])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Таблицы для выводов

    Без графиков: границы середины и где в ней новички (`mid_bounds`), подписания по MLE
    (`mle_table`), те же люди через четыре сезона (`cohort_table`).
    """)
    return


@app.cell(hide_code=True)
def _(BASE, MID_HI, MID_LO, SEASON_LABEL, cap, mo, np, pd, pool, rookie):
    def _m(v):
        return f"${v / 1e6:.2f} млн"


    def _pct_in(s, v):
        return f"{100 * (pool[s] < v).mean():.0f}-й"


    _rows = {}
    for _s in [BASE, "2025-26"]:
        _lo, _hi = np.percentile(pool[_s], [MID_LO, MID_HI])
        _cap = cap.loc[_s, "salary_cap"]
        _r = rookie[rookie["season"] == _s].set_index("pick")
        _in = _r.index[(_r["year1"] >= _lo) & (_r["year1"] <= _hi)]
        _above4 = _r.index[_r["year4"] > _hi]
        _rows[SEASON_LABEL[_s]] = {
            f"граница середины: {MID_LO}-й перцентиль": f"{_m(_lo)} ({_lo / _cap:.1%} потолка)",
            f"граница середины: {MID_HI}-й перцентиль": f"{_m(_hi)} ({_hi / _cap:.1%} потолка)",
            "пик №1, 1-й год": f"{_m(_r.loc[1, 'year1'])}, {_pct_in(_s, _r.loc[1, 'year1'])} перцентиль",
            "пики в середине, 1-й год": f"№{_in.min()}–{_in.max()}",
            "пики выше середины на 4-м году": f"№1–{_above4.max()}",
            "детская максималка, 25% потолка": f"{_m(cap.loc[_s, 'max_25'])}, {_pct_in(_s, cap.loc[_s, 'max_25'])} перцентиль",
        }
    mid_bounds = pd.DataFrame(_rows)
    mo.vstack([
        mo.md(f"""
    ### Кто попадает в середину ({MID_LO}–{MID_HI}-й перцентиль)

    Границы середины в долларах для базы и конца, и где на этой шкале новички. Пики — 120%
    шкалы драфта этого года (`rookie_scale.csv`); «на 4-м году» — та же шкала, четвёртый
    год контракта, сравнение с границей того же сезона приблизительное. Детская максималка —
    продление после новичкового контракта, 25% потолка (до 30% по правилу Деррика Роуза).
    """),
        mid_bounds,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### MLE: кто его получает (H3)

    Трекеры Hoops Rumors: стартовая зарплата каждого подписания по MLE (non-taxpayer и
    taxpayer) и room exception, в долях потолка. Сделки, где исключение поглотило игрока в
    обмене, отмечены отдельно. 2024/25 есть только в этих данных — в зарплатах его нет.
    """)
    return


@app.cell
def _(SEASON_LABEL, cap, mle, pd):
    MLE_SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
    mle_signed = mle.loc[mle["player"].notna() & (mle["amount"] > 0)].copy()
    mle_signed["cap_share"] = mle_signed["amount"] / mle_signed["season"].map(cap["salary_cap"])
    mle_signed["tax_mle"] = mle_signed["season"].map(cap["mle_taxpayer"])
    mle_signed["full_mle"] = mle_signed["season"].map(cap["mle_non_taxpayer"])

    _rows = []
    for _s in MLE_SEASONS:
        _m = mle_signed[(mle_signed["season"] == _s) & (mle_signed["via_trade"] == "no")]
        _teams = mle[mle["season"] == _s]
        _rows.append({
            "сезон": SEASON_LABEL[_s],
            "подписаний (MLE + room)": len(_m),
            "≥ налог. MLE": int((_m["amount"] >= _m["tax_mle"]).sum()),
            "≥ 90% полного MLE": int((_m["amount"] >= 0.9 * _m["full_mle"]).sum()),
            "≥ \$6 млн": int((_m["amount"] >= 6e6).sum()),
            "≥ 5% потолка": int((_m["cap_share"] >= 0.05).sum()),
            "сумма, \$ млн": round(_m["amount"].sum() / 1e6),
            "команд без MLE (над 2-м апроном)": int(_teams["team_note"].fillna("")
                                                  .str.contains("second (?:tax )?apron").groupby(_teams["team"]).any().sum()),
        })
    mle_table = pd.DataFrame(_rows).set_index("сезон")
    mle_table
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Те же люди (абляция «класс — это человек, а не квантиль»)

    НБА говорит о классах как о квантилях: «середина» 2025/26 зарабатывает больше
    «середины» 2021/22. Браун — о людях: середняк 2021/22 в 2025/26 может оказаться на
    минимуме или вне лиги. Корзины — по зарплате в 2021/22; дальше — где эти же игроки
    через четыре сезона. Возраст не учтён: из корзины «< 2%» многие растут просто потому,
    что заканчиваются новичковые контракты.
    """)
    return


@app.cell(hide_code=True)
def _(SEASON_LABEL, np, pd, players):
    SHARE_EDGES = [0, 0.02, 0.05, 0.10, 0.20, 0.25, 1.0]
    SHARE_LABELS = ["< 2%", "2–5%", "5–10%", "10–20%", "20–25%", "≥ 25%"]
    OUTCOMES = ["доля потолка выросла >10%", "± 10%", "доля потолка упала >10%", "нет в лиге / two-way"]
    COHORTS = [("2021-22", "2025-26", "CBA-2023")]


    def cohort(base, later):
        _b = players.loc[players["in_pool"] & (players["season"] == base),
                              ["player_id", "player", "salary", "cap_share"]].copy()
        _b["share_bucket"] = pd.cut(_b["cap_share"], SHARE_EDGES, labels=SHARE_LABELS, right=False)
        _l = players.loc[players["season"] == later].set_index("player_id")["cap_share"]
        _b["share_later"] = _b["player_id"].map(_l)
        _b["outcome"] = np.select(
            [_b["share_later"].isna(), _b["share_later"] < 0.9 * _b["cap_share"],
             _b["share_later"] > 1.1 * _b["cap_share"]], OUTCOMES[3:] + OUTCOMES[2:3] + OUTCOMES[:1],
            default=OUTCOMES[1])
        return _b


    cohorts = {base: cohort(base, later) for base, later, _ in COHORTS}
    cohort_table = pd.concat(
        {f"{SEASON_LABEL[b]} → {SEASON_LABEL[l]}":
         (pd.crosstab(cohorts[b]["share_bucket"], cohorts[b]["outcome"], normalize="index")
          .reindex(columns=OUTCOMES, fill_value=0) * 100).round(0)
         .assign(игроков=cohorts[b]["share_bucket"].value_counts())
         for b, l, _ in COHORTS}, axis=1)
    cohort_table
    return


if __name__ == "__main__":
    app.run()
