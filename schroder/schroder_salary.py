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
    # Шрёдер и Иш Смит: зарплата, продукт, излишек

    Три части, все на одних и тех же CSV из `writing/data/`.

    **1. Контракты.** Ставки по контрактам в долларах на фоне MLE и минимума
    ветерана, с отметками обменов и отчислений. Дальше — по годам карьеры, Шрёдер
    против Иша.

    **2. Излишек: продукт против цены.** Доля игрока в продукте команды против доли
    потолка, которую он стоит. Инструментальная проверка гипотезы А8. Плюс два
    варианта формы графика и вариант на PIE вместо долей.

    **3. На фоне защитников лиги.** Тот же продукт — боксплотом по всей когорте
    защитников, сезон за сезоном.

    Зарплата везде — база по контракту (`salary_by_season`), кэп-хит не используется.
    Данные: `writing/data/*_contracts.csv`, `writing/data/nba_cap_limits.csv`,
    `writing/data/*_stats_basic.csv`, `writing/data/nba_league_averages.csv`,
    `writing/data/nba_pg_cohort.csv`, `writing/data/schroder_moves.csv`,
    `writing/data/ish_smith.csv`, `writing/data/schroder_stats_advanced.csv`.

    Прогнозные сезоны на кривые не выводятся. У Шрёдера это 2027/28: потолок там
    взят из проекции лиги, а сезон гарантирован лишь на $4 350 000. В таблице и в
    сверке он остаётся.
    """)
    return


@app.cell(hide_code=True)
def doc_sources(mo):
    mo.md(r"""
    ## Данные: источники и процесс сборки

    Файлы двух происхождений. Всё сверено 19–20.08.2026, ссылки на каждый ключ —
    в [`writing/data/sources.md`](../data/sources.md); здесь только сводка.

    ### 1. Выгружено скриптом `writing/scripts/fetch_stats.py`

    Библиотека `nba_api`, эндпоинты stats.nba.com. Одна команда пересобирает все
    семь CSV: `~/.virtualenvs/blog_env/bin/python writing/scripts/fetch_stats.py`.

    | эндпоинт | параметры | что берётся |
    |---|---|---|
    | `PlayerCareerStats` | `PlayerID` 203471 / 202397, `PerMode36=Totals`, набор `SeasonTotalsRegularSeason` | базовая статистика Шрёдера и Иша |
    | `LeagueDashPlayerStats` | `MeasureType=Base` и `Advanced`, `PerMode=PerGame`, `Season` | все игроки сезона — из них когорта защитников |
    | `LeagueDashTeamStats` | `Base&PerMode=Totals` и `Advanced&PerMode=PerGame`, `Season` | лига по сезонам |
    | `PlayerIndex` | `Historical=1`, `LeagueID=00` | позиции игроков, 5206 строк одним запросом |

    Всюду `SeasonType = Regular Season`: плей-офф в задачу не входил и не выгружался.
    Сезоны — с 2010/11 (дебют Иша) по 2025/26.

    ### 2. Собрано руками по публичным источникам

    - **Лимиты лиги** (`nba_cap_limits.csv`) — сезонные релизы pr.nba.com (потолок,
      налоговая линия, минимальная платёжка, три MLE), плюс справочники по апронам,
      би-аннуалу и минимуму ветерана по стажу.
    - **Контракты** (`schroder_contracts.csv`, `ish_smith_contracts.csv`) —
      SalarySwish, Basketball-Reference, ESPN, HoopsRumors: клуб, дата, срок,
      объявленная и гарантированная суммы, зарплата по годам, механизм подписания.

    ### Как собирается

    Сырые ответы кладутся в дисковый кэш (`--cache-dir`), между запросами пауза
    1,2 с, при отказе три попытки с нарастающим ожиданием — у stats.nba.com жёсткий
    рейт-лимит. Полная выгрузка — 105 запросов, около четырёх минут. Кэш можно
    удалять в любой момент.

    ### Как склеивается

    - **Отрезки внутри сезона.** `PlayerCareerStats` отдаёт и строку на каждый клуб
      (`row_type = season_team`), и итог сезона (`TOT` → `season_total`); в CSV
      сохраняются обе, схлопывание оставлено ноутбуку.
    - **Когорта.** `Base` и `Advanced` за сезон мёржатся по `PLAYER_ID`, позиция
      подтягивается из `PlayerIndex` по тому же идентификатору.
    - **Клуб отрезка пишется из параметра запроса, а не из ответа.**
      `LeagueDashPlayerStats` с `TeamID` считает статистику верно, но в
      `TEAM_ABBREVIATION` возвращает последний клуб игрока: иначе все отрезки
      2025/26 оказались бы приписаны «Кливленду».
    - **Лига.** TS% и eFG% считаются от сумм по всем тридцати командам, а не как
      среднее командных процентов; `pace` — среднее командных значений.

    ### Как фильтруется

    - **Когорта защитников:** `POSITION = G` (чистые защитники, без `G-F` и `F-G`)
      и не меньше 8 минут за игру в среднем — 124–209 человек за сезон, 2723 строки
      за шестнадцать сезонов. Серверный фильтр `PlayerPosition=G` не используется:
      он включает `G-F` и `F-G` (Дерозан попадал в выборку).
      На графике 6 и в калибровке PIE к этому добавляется порог от 15 матчей за сезон: он ставится в
      ноутбуке, а не в скрипте, поэтому в CSV остаются все 2723 строки, а на график
      идут 2444 — 119–182 человека за сезон.
    - **`PlayerIndex` только с `Historical=1`:** без флага на 2010/11 приходит
      74 строки вместо 582 — одни действующие игроки.
    - **Чего нет:** PER, BPM, VORP, Win Shares. Это метрики Basketball-Reference,
      в `nba_api` их не существует; колонок под них в файлах не оставлено.
    """)
    return


@app.cell(hide_code=True)
def doc_files_manual(mo):
    mo.md(r"""
    ## Файлы данных: собранные руками

    ### `nba_cap_limits.csv` — 18 строк (2010/11 – 2027/28), строка на сезон

    Происхождение: релизы pr.nba.com плюс справочники по минимумам и исключениям.

    | колонка | тип | единицы |
    |---|---|---|
    | `season` | str | сезон вида `2013-14` — ключ мёржа со всеми остальными файлами |
    | `salary_cap` | int | $ за сезон |
    | `tax_level`, `min_team_salary`, `first_apron`, `second_apron` | str | $; строка, а не число, из-за меток `TODO` и `n/a` (апронов до CBA-2011 не существовало) |
    | `mle_non_taxpayer` | int | $ |
    | `mle_taxpayer`, `mle_room` | float | $; пусто там, где величины ещё не было |
    | `bi_annual_exception` | str | $ / `n/a` |
    | `vet_min_0y` … `vet_min_9y`, `vet_min_10plus_y` | int | $, минимум ветерана по стажу |
    | `vet_min_cap_hit_1yr_deal` | int | $, кэп-хит однолетнего минимального контракта |
    | `cba` | int | год соглашения: 2005, 2011, 2017, 2023 |
    | `status` | str | `final` или `projected` (2026/27 и 2027/28 — проекция лиги) |
    | `source_cap`, `source_apron`, `source_exceptions`, `source_minimums` | str | ключи источников из `sources.md` |
    | `verified_on` | str | дата сверки, ISO |

    В ноутбуке берутся `season`, `salary_cap`, `mle_non_taxpayer` и колонки
    `vet_min_*`.

    ### `schroder_contracts.csv` (6 строк) и `ish_smith_contracts.csv` (11 строк)

    Строка на контракт, одна схема на оба файла. Происхождение: SalarySwish,
    Basketball-Reference, ESPN, HoopsRumors.

    | колонка | тип | единицы |
    |---|---|---|
    | `contract_no` | int | порядковый номер контракта в карьере |
    | `signing_team` | str | клуб, подписавший контракт (по-русски) |
    | `signing_date`, `end_date` | str | дата, ISO |
    | `years` | int / str | срок в сезонах; у Иша строка — в контракте №2 стоит `TODO` |
    | `seasons_covered` | str | диапазон вида `2013-14..2016-17` |
    | `announced_total_usd`, `guaranteed_usd` | int / str | $ за весь контракт; у Иша строка из-за `TODO` |
    | `salary_by_season` | str | **главная колонка для ноутбука**: пары `сезон:доллары` через `;` |
    | `options` | str | опции клуба и игрока, текстом |
    | `mechanism` | str | механизм подписания: новичковая шкала, минимум, MLE, Non-Bird, room exception, место под потолком |
    | `cba_benchmark` | str | с каким эталоном CBA сверялась сумма |
    | `benchmark_value_usd` | float | $ эталона; пусто, где эталона нет |
    | `matches_benchmark_exactly` | str | совпадение с эталоном, текстом |
    | `guarantees_and_triggers`, `how_it_ended` | str | гарантии и триггеры; чем контракт закончился |
    | `teams_played_under_this_contract` | str | клубы под этим контрактом, через `;` |
    | `source_keys`, `verified_on` | str | ключи источников, дата сверки |

    Метка `TODO` означает «величину не удалось подтвердить источником» и стоит
    в одном контракте Иша; числовые колонки из-за неё читаются как строки.
    """)
    return


@app.cell(hide_code=True)
def doc_files_api(mo):
    mo.md(r"""
    ## Файлы данных: выгруженные из `nba_api`

    ### `nba_league_averages.csv` — 16 строк, строка на сезон

    | колонка | тип | единицы |
    |---|---|---|
    | `season` | str | `2013-14` |
    | `teams` | int | команд в лиге |
    | `games_per_team` | str | матчей на команду; строка, потому что бывает диапазон: `82`, `81-82`, `66`, `72`, `64-75` |
    | `pts_per_team_game` | float | очков на команду за игру — **знаменатель доли очков** |
    | `ast_per_team_game`, `reb_per_team_game`, `tov_per_team_game` | float | то же для передач, подборов, потерь |
    | `pace` | float | владений за 48 минут |
    | `ts_pct`, `efg_pct`, `fg3a_share` | float | доли 0–1 |
    | `shortened_season`, `season_note` | str | `да`/`нет` и причина: локаут-2011/12, COVID-2019/20 и 2020/21 |
    | `source_keys`, `verified_on` | str | ключ источника, дата сверки |

    ### `schroder_stats_basic.csv` (22 строки) и `ish_smith_stats_basic.csv` (26 строк)

    38 колонок, только регулярный сезон. Строк на сезон может быть несколько:
    по одной на клуб плюс итог.

    | колонка | тип | единицы |
    |---|---|---|
    | `player`, `player_id` | str, int | имя по-русски и идентификатор NBA |
    | `season` | str | `2013-14` |
    | `row_type` | str | `season_team` — отрезок за один клуб, `season_total` — итог сезона (`TOT`) |
    | `team`, `team_abbr`, `team_id` | str, str, int | клуб по-русски, трёхбуквенный код, идентификатор |
    | `age` | float | лет на сезон |
    | `gp`, `gs` | int | матчей сыграно / в старте |
    | `min_total` | int | минут за сезон |
    | `min_per_game` | float | минут за игру |
    | `pts`, `ast`, `reb`, `oreb`, `dreb`, `stl`, `blk`, `tov`, `pf` | int | суммы за сезон |
    | `fgm`, `fga`, `fg3m`, `fg3a`, `ftm`, `fta` | int | попадания и попытки за сезон |
    | `fg_pct`, `fg3_pct`, `ft_pct` | float | доли 0–1 |
    | `pts_per_game`, `ast_per_game`, `reb_per_game` | float | за игру |
    | `pts_per36`, `ast_per36`, `reb_per36` | float | в пересчёте на 36 минут |
    | `source_keys`, `verified_on` | str | ключ источника, дата сверки |

    В ноутбуке используются `season`, `row_type`, `team_abbr`, `gp`,
    `min_per_game`, `pts_per_game`.

    ### `nba_pg_cohort.csv` — 2723 строки, строка на «защитник × сезон»

    Сырая выборка, из которой считаются боксплоты. Определение выборки в строках
    не дублируется — оно одно на файл и записано в `sources.md` и в
    `nba_pg_baseline.csv`.

    | колонка | тип | единицы |
    |---|---|---|
    | `season` | str | `2013-14` |
    | `player_id`, `player` | int, str | идентификатор и имя латиницей, как отдаёт API |
    | `team_abbr` | str | клуб по ответу API — для отрезков внутри сезона не годится |
    | `gp` | int | матчей за сезон |
    | `pts`, `ast`, `min` | float | за игру |
    | `usg_pct`, `ts_pct`, `pie` | float | доли 0–1 |
    | `net_rating` | float | очков на 100 владений |

    ### `nba_pg_baseline.csv` — 16 строк, строка на сезон

    Та же когорта, схлопнутая в медиану и среднее. В ноутбуке нужен только для
    сверки: `season` (str), `sample_definition` (str — определение выборки),
    `sample_size` (int — человек в выборке), по паре `*_median` / `*_mean` (float)
    для `pts`, `ast`, `min` (за игру), `usg_pct`, `ts_pct`, `pie` (доли 0–1) и
    `net_rating` (очков на 100 владений), плюс `source_keys` и `verified_on`.
    """)
    return


@app.cell(hide_code=True)
def doc_transforms(mo):
    mo.md(r"""
    ## Трансформации внутри ноутбука

    С диска читается ровно то, что описано выше; всё остальное считается здесь.

    1. **`build_player` — контракты в строки «контракт × сезон».** Колонка
       `salary_by_season` разворачивается по `;` и `:` в отдельные строки, из сезона
       берётся `start_year`. Стаж считается по правилам лиги от сезона дебюта
       (`service_years = start_year − debut_year`), по стажу выбирается нужная
       колонка `vet_min_*`. Мёрж с `nba_cap_limits` по `season` даёт `salary_cap` и
       `mle_non_taxpayer`, из них — `pct_of_cap` (% потолка) и `in_mle` (в размерах
       полного MLE). Сезоны намеренно не схлопываются: у Иша 2011/12 и 2014/15
       покрыты сразу тремя контрактами, и каждый остаётся своей строкой.
    2. **`_mechanism` — механизмы Иша в пять категорий.** Одиннадцать контрактов не
       влезают в восемь категориальных слотов палитры, поэтому цвет назначается по
       механизму: минимум, Non-Bird, место под потолком, MLE, room exception.
    3. **`_rows_by_career_year` — выравнивание по годам карьеры (графики 3 и 4).**
       На год берётся строка контракта с максимальной годовой ставкой (целая строка,
       чтобы доля потолка считалась по тому же контракту, что и доллары),
       `career_year = start_year − debut_year + 1`. Таблицы Шрёдера и Иша мёржатся
       по `career_year`, считаются отношения `ratio_usd` и `ratio_pct`.
    4. **`season_rows` — ровно одна строка на сезон.** Берётся `season_total`, где он
       есть, иначе единственный `season_team`.
    5. **`add_shares` — доли продукта.** `minutes_share = min_per_game / 240`
       (240 = 5 игроков × 48 минут), `points_share = pts_per_game / pts_per_team_game`
       (мёрж с `nba_league_averages` по сезону), `product` — среднее двух долей.
       Всё за игру: сезонного знаменателя нет у 2019/20.
    6. **`surplus_data` — цена и излишек.** `price = salary / salary_cap`,
       `surplus = product − price`, `index = product / price`,
       `surplus_usd = surplus × salary_cap`. Отдельно строятся отрезки внутри сезона:
       доля сыгранных матчей `gp_share` и координаты `x0`, `x1` для ступенчатой
       кривой. Делится только продукт — цена годовая и следует за игроком в обмене.
    7. **`cohort_data` — тот же `add_shares` для когорты.** У когорты `min` и `pts`
       уже за игру, поэтому колонки передаются явно. Шрёдер и Иш переиндексируются
       по сезону, чтобы лечь точками поверх боксплотов. Для графика 6 когорта
       режется по матчам: `cohort_chart` — только строки с `gp ≥ COHORT_MIN_GP`
       (15); она же идёт в калибровку PIE. Сверка с базовой линией берёт CSV целиком.
    8. **`cohort_check` — сверка сырой когорты со схлопнутой базовой линией.** Число
       строк в сезоне против `sample_size`, медианы по семи метрикам против
       `*_median`. Округление — питоновским `round`, как в скрипте выгрузки:
       `Series.round` из pandas на ровных половинках даёт другой знак, и семь медиан
       из 112 «разошлись» бы на единицу последнего разряда.
    9. **`moves_data` — обмены и отчисления.** Из `schroder_moves.csv` берутся
       обмены (включая sign-and-trade), из `ish_smith.csv` — отрезки, закончившиеся
       обменом или отчислением; события одного дня сливаются. Дата переводится на
       ось сезонов (сезон — с 1 июля), клуб — в трёхбуквенный код по таблицам
       статистики. На графике 5 обмен ставится не по дате, а на начало отрезка
       нового клуба (`surplus_trades`): там сезон делится по сыгранным матчам.
    10. **`metric_data` — кандидаты в сводную метрику.** К отрезкам Шрёдера
        подмёрживаются PIE, USG% и NET_RATING из `schroder_stats_advanced.csv` по
        сезону и клубу; `possession_share = usg_pct × min_per_game / 48`. По когорте графика 6
        считаются медианы PIE и долевого продукта (`metric_scale`) и корреляции
        кандидатов с продуктом (`metric_corr`).

    ## Графики по порядку

    1. **Шрёдер: контракты и обмены** — ставки в долларах на фоне MLE и минимума ветерана.
    2. **Иш Смит: контракты, обмены и отчисления** — то же самое, для сравнения.
    3. **Год карьеры против года карьеры: ставка по контракту** — в долларах.
    4. **Год карьеры против года карьеры: доля потолка** — та же пара в долях потолка.
       Графики 3–4 в статью не идут, от них остаётся примечание об одном годе стажа.
    5. **Шрёдер: продукт против цены** — проверка гипотезы А8. Варианты: **5а** —
       гантелями по отрезкам, **5б** — излишек в долларах, **5в** — PIE вместо долей.
    6. **На фоне защитников лиги** — тот же продукт боксплотом по всей когорте.
    """)
    return


@app.cell
def _():
    import textwrap
    from datetime import date
    from pathlib import Path

    import altair as alt
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import vl_convert as vlc
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    DATA = Path(__file__).resolve().parents[1] / "data"
    return (
        DATA,
        FuncFormatter,
        MaxNLocator,
        alt,
        date,
        np,
        pd,
        plt,
        textwrap,
        vlc,
    )


@app.cell
def _(DATA, pd):
    caps = pd.read_csv(DATA / "nba_cap_limits.csv")
    return (caps,)


@app.cell
def _(caps, pd):
    def build_player(contracts, debut_year, color_key):
        """Контракты → строка на «контракт × сезон», состыкованная с лимитами лиги.

        Сезоны намеренно не схлопываются: у Иша Смита 2011/12 и 2014/15 покрыты
        сразу тремя контрактами, и каждый остаётся своей строкой.
        """
        rows = [
            {
                "contract_no": int(row["contract_no"]),
                "season": chunk.split(":")[0],
                "salary": int(chunk.split(":")[1]),
                "color_key": color_key(row),
            }
            for _, row in contracts.iterrows()
            for chunk in row["salary_by_season"].split(";")
        ]
        df = pd.DataFrame(rows)
        df["start_year"] = df["season"].str.slice(0, 4).astype(int)

        # Стаж по правилам лиги: сезон-новичок — ноль лет, дальше по одному.
        # Считается от сезона, а не от номера строки: у Иша строк больше, чем сезонов.
        df["service_years"] = df["start_year"] - debut_year
        df["vet_min_col"] = [
            f"vet_min_{y}y" if y < 10 else "vet_min_10plus_y" for y in df["service_years"]
        ]

        df = df.merge(
            caps[["season", "salary_cap", "mle_non_taxpayer"]], on="season", how="left"
        )
        df["vet_min"] = [
            int(caps.loc[caps["season"] == s, col].iloc[0])
            for s, col in zip(df["season"], df["vet_min_col"])
        ]
        df["pct_of_cap"] = df["salary"] / df["salary_cap"] * 100
        df["in_mle"] = df["salary"] / df["mle_non_taxpayer"]
        return df

    return (build_player,)


@app.cell
def _(DATA, build_player, pd):
    def _mechanism(row):
        """11 контрактов Иша не влезают в 8 категориальных слотов — красим механизм."""
        text = row["mechanism"].lower()
        if "non-bird" in text:
            return "Исключение Non-Bird"
        if "room exception" in text:
            return "Room exception"
        if "среднего уровня" in text or "mle" in text:
            return "MLE"
        if "место под потолком" in text:
            return "Место под потолком"
        return "Минимум"

    schroder_contracts = pd.read_csv(DATA / "schroder_contracts.csv")
    ish_contracts = pd.read_csv(DATA / "ish_smith_contracts.csv")

    schroder = build_player(schroder_contracts, 2013, lambda row: int(row["contract_no"]))
    ish = build_player(ish_contracts, 2010, _mechanism)
    return ish, ish_contracts, schroder, schroder_contracts


@app.cell
def moves_data(DATA, date, ish_basic, pd, schroder_basic):
    def _season_start(iso):
        """Сезон идёт с 1 июля по 30 июня: год старта сезона, на который приходится дата."""
        d = date.fromisoformat(iso)
        return d.year if d.month >= 7 else d.year - 1


    def _season_x(iso):
        """Дата на оси сезонов: целая часть — сезон, дробная — доля года с 1 июля."""
        year = _season_start(iso)
        return year + (date.fromisoformat(iso) - date(year, 7, 1)).days / 365


    # Коды клубов — из статистики: там у каждого клуба есть и имя, и код.
    # «Шарлотт» есть только у Иша, за этот клуб Шрёдер ещё не играл.
    TEAM_ABBR = dict(
        pd.concat([schroder_basic, ish_basic])[["team", "team_abbr"]].drop_duplicates().values
    )

    # Шрёдер: только обмены, включая sign-and-trade. Подписание свободным агентом
    # меняет клуб, но обменом не является.
    _moves = pd.read_csv(DATA / "schroder_moves.csv")
    schroder_trades = _moves.loc[_moves["type"].str.contains("обмен"), ["date", "to_team"]].copy()
    schroder_trades["abbr"] = schroder_trades["to_team"].map(TEAM_ABBR)
    schroder_trades["season_start"] = schroder_trades["date"].map(_season_start)
    schroder_trades["x"] = schroder_trades["date"].map(_season_x)
    schroder_trades["kind"] = "обмен"
    schroder_trades["label"] = "→" + schroder_trades["abbr"]

    # Иш: обмены и отчисления из отрезков по клубам. Обмен подписывается клубом,
    # куда ушёл, отчисление — клубом, который отчислил. События одного дня
    # (обменян в «Новый Орлеан» и отчислен им же) сливаются в одну отметку.
    _stints = pd.read_csv(DATA / "ish_smith.csv").query("record_type == 'stint'")
    _stints = _stints.assign(next_franchise=_stints["franchise"].shift(-1))
    _events = pd.DataFrame(
        [
            {"date": s.left_date, "kind": "обмен", "label": "→" + TEAM_ABBR[s.next_franchise]}
            if s.left_how.startswith("обменян")
            else {"date": s.left_date, "kind": "отчисление", "label": "✕" + TEAM_ABBR[s.franchise]}
            for s in _stints.itertuples()
            if s.left_how.startswith(("обменян", "отчислен"))
        ]
    )
    ish_events = _events.groupby("date", as_index=False).agg(
        kind=("kind", lambda kinds: "обмен" if "обмен" in set(kinds) else "отчисление"),
        label=("label", " ".join),
    )
    ish_events["x"] = ish_events["date"].map(_season_x)
    return ish_events, schroder_trades


@app.cell
def _(mo):
    mo.md(r"""
    ## Сверка чисел
    """)
    return


@app.cell
def _(DATA, mo, pd, schroder):
    def _parse_c1():
        text = (DATA / "by_season.md").read_text(encoding="utf-8")
        block = text.split("### C1.")[1].split("\n\n")[1]
        rows = []
        for line in block.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 4 or not cells[0][:4].isdigit():
                continue
            rows.append(
                {
                    "season": cells[0],
                    "md_salary": int(cells[1].replace(" ", "")),
                    "md_pct": float(cells[2].rstrip("%")),
                    "md_mle": float(cells[3]),
                }
            )
        return pd.DataFrame(rows)

    check = schroder.merge(_parse_c1(), on="season", how="outer")
    check["ok_salary"] = check["salary"] == check["md_salary"]
    check["ok_pct"] = (check["pct_of_cap"].round(2) - check["md_pct"]).abs() < 0.005
    check["ok_mle"] = (check["in_mle"].round(2) - check["md_mle"]).abs() < 0.005

    bad = check[~(check["ok_salary"] & check["ok_pct"] & check["ok_mle"])]
    mo.md(
        f"**Шрёдер.** Все {len(check)} сезонов совпали с §C1 `by_season.md`."
        if bad.empty
        else f"**Шрёдер. Расхождения: {len(bad)}** — {', '.join(bad['season'])}"
    )
    return (bad,)


@app.cell
def _(bad):
    bad
    return


@app.cell
def _(ish, ish_contracts, mo):
    def _ish_report():
        # Отдельной таблицы по деньгам Иша в by_season.md нет, поэтому сверяем
        # с тем, что задокументировано в sources.md §4a.
        announced = ish_contracts["announced_total_usd"]
        announced_sum = announced[announced.str.isdigit()].astype(int).sum()

        exact = ish_contracts[ish_contracts["matches_benchmark_exactly"].str.startswith("да")]
        first_year = ish.sort_values("start_year").groupby("contract_no").first()
        hits = [
            first_year.loc[int(no), "salary"] == first_year.loc[int(no), "vet_min"]
            for no in exact["contract_no"]
        ]

        by_season = ish.groupby("season")["salary"].sum().sum()
        return [
            f"- сумма объявленных сумм: **${announced_sum:,}**".replace(",", " ")
            + f" — {'сходится' if announced_sum == 50065844 else 'НЕ сходится'}"
            + " с `sources.md` §4a ($50 065 844; контракт №2 там без суммы)",
            f"- контрактов, совпавших с минимумом ветерана до цента: **{sum(hits)} из {len(hits)}**"
            " заявленных в CSV — стаж по сезонам восстановлен верно",
            f"- сумма `salary_by_season` по всем строкам: **${by_season:,}**".replace(",", " ")
            + " против задокументированных $47 226 186 заработка. Разница —"
            " контракты, разорванные до конца сезона (в 2011/12 и 2014/15 их по три);"
            " ставки в CSV годовые, поэтому складывать их нельзя.",
        ]

    mo.md("**Иш Смит.**\n" + "\n".join(_ish_report()))
    return


@app.cell
def _(FuncFormatter, MaxNLocator, plt):
    SURFACE = "#fcfcfb"
    INK = "#0b0b0b"
    INK_MUTED = "#6f6e69"
    GRID = "#e8e7e3"

    # Категориальные слоты 1–8, порядок фиксирован и не циклится.
    PALETTE = [
        "#2a78d6",
        "#eb6834",
        "#1baf7a",
        "#eda100",
        "#e87ba4",
        "#008300",
        "#4a3aa7",
        "#e34948",
    ]

    # Обмены и отчисления — серыми вертикалями, различаются штрихом, а не цветом:
    # цвет на графиках зарплат уже занят контрактами.
    EVENT_STYLES = {"обмен": (0, (4, 3)), "отчисление": (0, (1, 2))}
    EVENT_LEGEND = {"обмен": "обмен: →куда ушёл", "отчисление": "отчисление: ✕кто отчислил"}


    def _step(ax, sub, column, color, **kwargs):
        xs = list(sub["start_year"]) + [sub["start_year"].iloc[-1] + 1]
        ys = list(sub[column]) + [sub[column].iloc[-1]]
        ax.step(xs, ys, where="post", color=color, solid_capstyle="round", **kwargs)


    def _ref_step(ax, pdf, column, style, label, anchor_year, dy):
        """Ориентир лиги: подпись ставится прямо у линии, не в легенду."""
        seasons = pdf.drop_duplicates("start_year").sort_values("start_year")
        _step(ax, seasons, column, INK_MUTED, lw=1.5, ls=style, alpha=0.8, zorder=2)
        anchor = seasons.loc[seasons["start_year"] == anchor_year, column].iloc[0]
        ax.annotate(
            label,
            xy=(anchor_year + 0.5, anchor),
            xytext=(0, dy),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=INK_MUTED,
        )


    def make_figure(pdf, events, order, labels, title, refs_anchors, note=None):
        """Ставки по контрактам в долларах на фоне MLE и минимума ветерана.

        `order` задаёт порядок слотов палитры. `events` — обмены и отчисления:
        колонки `x` (дата на оси сезонов), `kind` и `label`.
        """
        color_of = dict(zip(order, PALETTE))
        seasons = pdf.drop_duplicates("start_year").sort_values("start_year")

        fig, ax = plt.subplots(figsize=(11, 6.8 if note else 5.8))
        fig.patch.set_facecolor(SURFACE)
        ax.set_facecolor(SURFACE)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color=GRID, lw=1)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.tick_params(colors=INK_MUTED, labelsize=9, length=0)
        ax.set_ylabel("млн $", fontsize=9, color=INK_MUTED)

        mle_year, vet_year = refs_anchors
        _ref_step(ax, pdf, "mle_non_taxpayer", "-", "MLE неналогоплательщика", mle_year, 8)
        _ref_step(ax, pdf, "vet_min", ":", "минимум ветерана по стажу", vet_year, -16)

        # Отрезок на контракт: в сезонах с несколькими контрактами они лягут
        # друг над другом — это и есть картина сезона с двумя-тремя клубами.
        for _, sub in pdf.groupby("contract_no"):
            color = color_of[sub["color_key"].iloc[0]]
            _step(ax, sub, "salary", color, lw=2, zorder=3)
            ax.plot(
                sub["start_year"] + 0.5,
                sub["salary"],
                "o",
                ms=6,
                color=color,
                mec=SURFACE,
                mew=1.5,
                zorder=4,
            )

        # Подписи событий в три ряда: у Иша в 2014–2015 они идут через два-три месяца.
        for i, row in enumerate(events.sort_values("x").itertuples()):
            ax.axvline(row.x, color=INK_MUTED, lw=1, ls=EVENT_STYLES[row.kind], alpha=0.6, zorder=1)
            ax.annotate(
                row.label,
                xy=(row.x, 1),
                xycoords=("data", "axes fraction"),
                xytext=(0, -2 - 11 * (i % 3)),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=7.5,
                color=INK,
                bbox=dict(boxstyle="square,pad=0.1", fc=SURFACE, ec="none"),
            )

        # Общий ноль, сверху — место под три ряда подписей событий.
        ax.set_ylim(0, ax.get_ylim()[1] * 1.22)
        # steps без 2,5: иначе шаг 2,5 млн печатается как 0 / 2 / 5 / 8 / 10.
        ax.yaxis.set_major_locator(MaxNLocator(nbins=8, steps=[1, 2, 5, 10]))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1e6:.0f}"))

        ax.set_xlim(seasons["start_year"].min() - 0.15, seasons["start_year"].max() + 1.15)
        ax.set_xticks(seasons["start_year"] + 0.5)
        ax.set_xticklabels([s.replace("-", "/")[2:] for s in seasons["season"]], fontsize=9)

        handles = [
            plt.Line2D([], [], color=color_of[key], lw=2, label=label)
            for key, label in zip(order, labels)
        ] + [
            plt.Line2D([], [], color=INK_MUTED, lw=1, ls=style, label=EVENT_LEGEND[kind])
            for kind, style in EVENT_STYLES.items()
            if kind in set(events["kind"])
        ]
        legend = fig.legend(
            handles=handles,
            loc="lower center",
            ncol=2,
            frameon=False,
            fontsize=9,
            bbox_to_anchor=(0.5, -0.01),
        )
        for text in legend.get_texts():
            text.set_color(INK)

        fig.suptitle(title, x=0.125, ha="left", fontsize=14, color=INK)
        if note:
            fig.text(0.125, 0.925, note, ha="left", va="top", fontsize=8, color=INK_MUTED)
        fig.tight_layout(rect=(0, 0.16, 1, 0.80 if note else 0.95))
        return fig

    return (
        EVENT_LEGEND,
        EVENT_STYLES,
        GRID,
        INK,
        INK_MUTED,
        PALETTE,
        SURFACE,
        make_figure,
    )


@app.cell
def pub_style(GRID, INK, INK_MUTED, alt, vlc):
    # Публикационные графики (altair): общий стиль, ось сезонов и экспорт в PNG.
    PUB_FONT = "Noto Sans"
    # Размер вида в пикселях; PNG экспортируется с масштабом 2 — около 1636×764.
    PUB_WIDTH, PUB_HEIGHT = 818, 382
    SEASON_LABEL = (
        "slice(toString(floor(datum.value)), 2) + '/' + slice(toString(floor(datum.value) + 1), 2)"
    )


    def tint(color, alpha):
        """Непрозрачный цвет «color с прозрачностью alpha на белом» — в легенде тот же цвет, что на графике."""
        rgb = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
        return "#" + "".join(f"{round(255 - (255 - c) * alpha):02x}" for c in rgb)


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


    def pub_fit(chart, title, subtitle=alt.Undefined, height=PUB_HEIGHT):
        """Один вид (слой) целиком — с заголовком, осями и легендой — в PUB_WIDTH × height."""
        return pub_config(
            chart.properties(
                title=alt.TitleParams(title, subtitle=subtitle),
                width=PUB_WIDTH,
                height=height,
                autosize=alt.AutoSizeParams(type="fit", contains="padding"),
            )
        )


    def season_x(field, first, last, pad):
        """Ось сезонов: целое — начало сезона, подпись «13/14» в середине сезона."""
        return alt.X(
            f"{field}:Q",
            title=None,
            scale=alt.Scale(domain=[first - pad, last + 1 + pad], nice=False, zero=False),
            axis=alt.Axis(values=[y + 0.5 for y in range(first, last + 1)], labelExpr=SEASON_LABEL, grid=False),
        )


    def save_png(chart, path):
        """PNG ×2 через vl-convert с русской локалью чисел; возвращает (ширина, высота)."""
        png = vlc.vegalite_to_png(chart.to_json(), scale=2, format_locale="ru-RU")
        path.write_bytes(png)
        return int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")


    return PUB_HEIGHT, halo_text, pub_config, pub_fit, save_png, season_x, tint


@app.cell
def pub_salary_plot(
    EVENT_LEGEND,
    EVENT_STYLES,
    INK,
    INK_MUTED,
    PALETTE,
    PUB_HEIGHT,
    alt,
    halo_text,
    pd,
    pub_fit,
    season_x,
):
    def pub_salary_chart(pdf, events, order, labels, refs_anchors, ymax, yticks, title,
                         subtitle=alt.Undefined, height=PUB_HEIGHT):
        """Публикационная версия make_figure: ставки в $ млн на фоне ИСУ и минимума ветерана.

        `refs_anchors` — сезоны, над которыми подписаны линии ИСУ и минимума: их
        выбирают там, где нет вертикалей событий. `ymax` оставляет сверху место под
        три ряда подписей событий.
        """
        df = pdf.assign(v=pdf["salary"] / 1e6, series=pdf["color_key"].map(dict(zip(order, labels))))
        first, last = int(df["start_year"].min()), int(df["start_year"].max())
        x = season_x("x", first, last, 0.15)
        y = alt.Y("v:Q", title="$ млн", scale=alt.Scale(domain=[0, ymax], nice=False), axis=alt.Axis(values=yticks))
        color_scale = alt.Scale(domain=labels, range=PALETTE[: len(labels)])

        # Ступенька: у каждой строки «контракт × сезон» точка в начале и в конце сезона.
        steps = pd.concat([
            df.assign(x=df["start_year"], key=2 * df["start_year"]),
            df.assign(x=df["start_year"] + 1, key=2 * df["start_year"] + 1),
        ])
        lines = alt.Chart(steps).mark_line(strokeWidth=2.5).encode(
            x, y,
            alt.Color("series:N", scale=color_scale,
                      legend=alt.Legend(columns=2, symbolType="stroke", symbolStrokeWidth=2.5)),
            detail="contract_no:N", order="key:Q",
        )
        dots = alt.Chart(df.assign(x=df["start_year"] + 0.5)).mark_circle(
            size=50, opacity=1, stroke="white", strokeWidth=1.5
        ).encode(x, y, alt.Color("series:N", scale=color_scale, legend=None))

        # Ориентиры лиги. Штрих — свойство марки, а не канал: канал strokeDash в слое
        # общий, и он занят легендой обменов и отчислений.
        seasons = steps.drop_duplicates("key")
        refs, ref_labels = [], []
        for col, dash, text, year in [
            ("mle_non_taxpayer", [1, 0], "ИСУ неналогоплательщика", refs_anchors[0]),
            ("vet_min", [2, 3], "минимум ветерана по стажу", refs_anchors[1]),
        ]:
            refs.append(
                alt.Chart(seasons.assign(v=seasons[col] / 1e6))
                .mark_line(strokeWidth=1.5, color=INK_MUTED, opacity=0.8, strokeDash=dash)
                .encode(x, y, order="key:Q")
            )
            anchor = pd.DataFrame({
                "x": [year + 0.5],
                "v": [df.loc[df["start_year"] == year, col].iloc[0] / 1e6],
                "t": [text],
            })
            ref_labels += halo_text(alt.Chart(anchor).encode(x, y, text="t:N"),
                                    fontSize=11, color=INK_MUTED, baseline="bottom", dy=-3)

        # Обмены и отчисления: вертикаль на всю высоту, подпись в одном из трёх рядов
        # под верхним краем. Легенда — над графиком, рядом с самими подписями.
        ev = events.sort_values("x").reset_index(drop=True)
        ev = ev.assign(row=ev.index % 3, v=ymax, legend=ev["kind"].map(EVENT_LEGEND))
        kinds = [k for k in EVENT_LEGEND if k in set(ev["kind"])]
        rules = alt.Chart(ev).mark_rule(strokeWidth=1, color=INK_MUTED, opacity=0.7).encode(
            x,
            alt.StrokeDash(
                "legend:N",
                scale=alt.Scale(domain=[EVENT_LEGEND[k] for k in kinds],
                                range=[list(EVENT_STYLES[k][1]) for k in kinds]),
                legend=alt.Legend(orient="top", symbolType="stroke", symbolStrokeColor=INK_MUTED),
            ),
        )
        event_labels = []
        for row in range(3):
            event_labels += halo_text(alt.Chart(ev[ev["row"] == row]).encode(x, y, text="label:N"),
                                      baseline="top", dy=3 + 14 * row, fontSize=11, color=INK)

        chart = alt.layer(*refs, rules, lines, dots, *ref_labels, *event_labels)
        return pub_fit(chart, title, subtitle, height)


    return (pub_salary_chart,)


@app.cell
def _(make_figure, schroder, schroder_trades):
    make_figure(
        schroder[schroder["start_year"] <= 2026],
        schroder_trades,
        order=[1, 2, 3, 4, 5, 6],
        labels=[
            "1. Атланта, 2013 — новичковая шкала",
            "2. Атланта, 2016 — продление",
            "3. Бостон, 2021 — MLE налогоплательщика",
            "4. Лейкерс, 2022 — минимум ветерана",
            "5. Торонто, 2023 — полный MLE",
            "6. Детройт/Сакраменто, 2025 — полный MLE",
        ],
        title="График 1. Деннис Шрёдер: контракты и обмены",
        refs_anchors=(2019, 2019),
    )
    return


@app.cell
def pub_figure1(pub_salary_chart, schroder, schroder_trades):
    pub_chart1 = pub_salary_chart(
        schroder[schroder["start_year"] <= 2026],
        schroder_trades,
        order=[1, 2, 3, 4, 5, 6],
        labels=[
            "1. Атланта, 2013 — новичковая шкала",
            "2. Атланта, 2016 — продление",
            "3. Бостон, 2021 — ИСУ налогоплательщика",
            "4. Лейкерс, 2022 — минимум ветерана",
            "5. Торонто, 2023 — полное ИСУ",
            "6. Детройт/Сакраменто, 2025 — полное ИСУ",
        ],
        refs_anchors=(2015, 2019),
        ymax=20,
        yticks=[0, 5, 10, 15],
        title="Контракты Денниса Шрёдера",
    )
    pub_chart1
    return (pub_chart1,)


@app.cell
def _(mo):
    mo.md(r"""
    ## Иш Смит, 2010/11 – 2023/24

    Одиннадцать контрактов вместо шести, поэтому цвет несёт не номер контракта, а
    механизм, по которому контракт подписан. Семь из одиннадцати — исключение
    минимальной зарплаты.

    Сезоны 2011/12 и 2014/15 покрыты сразу тремя контрактами: его отчисляли и он
    переподписывался по ходу сезона. Такие сезоны не схлопываются в одно число —
    каждый контракт рисуется своим отрезком, и в этих столбцах отрезков несколько.
    Ставки в CSV годовые, так что вертикальный разброс внутри сезона — это разные
    ставки, а не сумма заработка. С кем был каждый из этих контрактов и на какой
    срок — в подписи над графиком.
    """)
    return


@app.cell
def _(date, ish, ish_contracts, ish_events, make_figure, textwrap):
    def _multi_contract_note():
        """Сезоны, покрытые несколькими контрактами: с кем подписан каждый и на какой срок."""

        def _dmy(iso):
            return date.fromisoformat(iso).strftime("%d.%m.%Y")

        def _years(value):
            # У контракта №2 срок — TODO: SalarySwish его не ведёт.
            if not str(value).isdigit():
                return "срок не подтверждён"
            return f"{value} {'год' if int(value) == 1 else 'года'}"  # в данных 1–3 года

        lines = []
        for season, sub in ish.groupby("season"):
            if len(sub) < 2:
                continue
            contracts = ish_contracts[ish_contracts["contract_no"].isin(sub["contract_no"])]
            parts = [
                f"{c.signing_team}, {_dmy(c.signing_date)}–{_dmy(c.end_date)}, {_years(c.years)}"
                for c in contracts.itertuples()
            ]
            text = f"{season.replace('-', '/')} — {len(parts)} контракта: " + " · ".join(parts)
            lines.append(textwrap.fill(text, width=125, subsequent_indent="    "))
        return "\n".join(lines)


    make_figure(
        ish,
        ish_events,
        order=[
            "Минимум",
            "Исключение Non-Bird",
            "Место под потолком",
            "MLE",
            "Room exception",
        ],
        labels=[
            "Исключение минимальной зарплаты (7 контрактов)",
            "Исключение Non-Bird (2012, «Орландо»)",
            "Место под потолком (2016, «Детройт»)",
            "MLE (2019, «Вашингтон»)",
            "Room exception (2021, «Шарлотт»)",
        ],
        title="График 2. Иш Смит: контракты, обмены и отчисления",
        refs_anchors=(2013, 2019),
        note=_multi_contract_note(),
    )
    return


@app.cell
def pub_figure2(ish, ish_events, pub_salary_chart):
    pub_chart2 = pub_salary_chart(
        ish,
        ish_events,
        order=["Минимум", "Исключение Non-Bird", "Место под потолком", "MLE", "Room exception"],
        labels=[
            "Исключение минимальной зарплаты (7 контрактов)",
            "Исключение без прав Бёрда (2012, «Орландо»)",
            "Место под потолком (2016, «Детройт»)",
            "ИСУ (2019, «Вашингтон»)",
            "Исключение для команд под потолком (2021, «Шарлотт»)",
        ],
        refs_anchors=(2017, 2019),
        ymax=16,
        yticks=[0, 2, 4, 6, 8, 10, 12, 14],
        title="Контракты Иша Смита",
    )
    pub_chart2
    return (pub_chart2,)


@app.cell
def pub_figure2_note(ish, ish_contracts, mo):
    def _ish_note():
        """Текст под графиком 2: сезоны с несколькими контрактами — с кем подписан каждый и на какой срок."""

        def _years(value):
            # У контракта №2 срок — TODO: SalarySwish его не ведёт.
            if not str(value).isdigit():
                return "срок не подтверждён"
            return f"{value} {'год' if int(value) == 1 else 'года'}"  # в данных 1–3 года

        lines = []
        for season, sub in ish.groupby("season"):
            if len(sub) < 2:
                continue
            contracts = ish_contracts[ish_contracts["contract_no"].isin(sub["contract_no"])]
            parts = [
                f"«{c.signing_team.rsplit(' ', 1)[0]}», {_years(c.years)}"
                for c in contracts.itertuples()
            ]
            lines.append(f"- **{season.replace('-', '/')}** — {len(parts)} контракта: " + "; ".join(parts))
        return "Сезоны Иша Смита, покрытые несколькими контрактами:\n\n" + "\n".join(lines)


    mo.md(_ish_note())
    return


@app.cell
def vs_intro(mo):
    mo.md(r"""
    ## Шрёдер против Иша: год карьеры против года карьеры

    Первый сезон одного против первого сезона другого, и так далее. У Шрёдера отсчёт
    идёт с 2013/14, у Иша — с 2010/11, так что одна и та же точка на оси — это разные
    календарные сезоны. Обоим хватает по 14 лет: у Шрёдера прогнозный 2027/28 отброшен,
    у Иша карьера кончилась в 2023/24.

    **Что берётся за зарплату сезона.** Годовая ставка действующего контракта, то есть
    максимум по контрактам, покрывающим сезон. У Иша 2011/12 и 2014/15 покрыты тремя
    контрактами каждый, но полноценная годовая ставка там только одна: остальные
    подписаны «пропорционально остатку сезона» или до конца сезона и годовой ставкой не
    являются. Максимум как раз выбирает нужную. Эти два сезона помечены на графике
    пустыми точками.
    """)
    return


@app.cell
def vs_data(ish, schroder):
    def _rows_by_career_year(df, debut_year, last_year):
        """Строка сезона = контракт с максимальной годовой ставкой.

        Берётся целая строка, а не только зарплата, чтобы доля потолка считалась
        по тому же контракту, что и доллары.
        """
        sub = df[df["start_year"] <= last_year]
        picked = sub.loc[sub.groupby("start_year")["salary"].idxmax()].copy()
        picked["career_year"] = picked["start_year"] - debut_year + 1
        picked["contracts"] = sub.groupby("start_year")["contract_no"].nunique().values
        return picked


    career_cmp = _rows_by_career_year(schroder, 2013, 2026).merge(
        _rows_by_career_year(ish, 2010, 2023),
        on="career_year",
        suffixes=("_d", "_i"),
    )
    career_cmp["ratio_usd"] = career_cmp["salary_d"] / career_cmp["salary_i"]
    career_cmp["ratio_pct"] = career_cmp["pct_of_cap_d"] / career_cmp["pct_of_cap_i"]
    career_cmp[
        [
            "career_year",
            "season_d", "salary_d", "pct_of_cap_d",
            "season_i", "salary_i", "pct_of_cap_i", "contracts_i",
            "ratio_usd", "ratio_pct",
        ]
    ]
    return (career_cmp,)


@app.cell
def vs_plot(
    FuncFormatter,
    GRID,
    INK,
    INK_MUTED,
    MaxNLocator,
    PALETTE,
    SURFACE,
    career_cmp,
    plt,
):
    def make_vs_figure(col_d, col_i, panel_title, ylabel, tick_fmt, ratio_ylabel,
                           number):
        """Две панели по годам карьеры: сами величины и их отношение.

        Отношение всегда на логарифмической шкале: ×2 вверх и ×2 вниз должны
        читаться одинаково, иначе провал ниже паритета схлопывается в ноль.
        Подписи пика и участка ниже единицы считаются из данных, а не вписаны.
        """
        den, sh = PALETTE[0], PALETTE[1]
        years = list(career_cmp["career_year"])
        ratio = career_cmp[col_d] / career_cmp[col_i]
        multi = (career_cmp["contracts_i"] > 1).values

        def step(ax, ys, color):
            ax.step(years + [years[-1] + 1], list(ys) + [list(ys)[-1]], where="post",
                    color=color, lw=2, solid_capstyle="round", zorder=3)

        def dots(ax, ys, color, hollow=None):
            xs = career_cmp["career_year"] + 0.5
            ax.plot(xs, ys, "o", ms=6, color=color, mec=SURFACE, mew=1.5, zorder=4)
            if hollow is not None:
                ax.plot(xs[hollow], ys[hollow], "o", ms=6, mfc=SURFACE, mec=color,
                        mew=1.8, zorder=5)

        fig, axes = plt.subplots(2, 1, figsize=(11, 7.6), sharex=True,
                                 height_ratios=[1.3, 1])
        fig.patch.set_facecolor(SURFACE)
        for ax in axes:
            ax.set_facecolor(SURFACE)
            ax.set_axisbelow(True)
            ax.grid(axis="y", color=GRID, lw=1)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            for side in ("left", "bottom"):
                ax.spines[side].set_color(GRID)
            ax.tick_params(colors=INK_MUTED, labelsize=9, length=0)

        top = axes[0]
        top.set_title(panel_title, loc="left", fontsize=11, color=INK, pad=10)
        top.set_ylabel(ylabel, fontsize=9, color=INK_MUTED)
        step(top, career_cmp[col_d], den)
        step(top, career_cmp[col_i], sh)
        dots(top, career_cmp[col_d], den)
        dots(top, career_cmp[col_i], sh, hollow=multi)
        top.set_ylim(bottom=0)
        top.yaxis.set_major_locator(MaxNLocator(nbins=6, steps=[1, 2, 5, 10]))
        top.yaxis.set_major_formatter(FuncFormatter(tick_fmt))
        for label, value in (("Шрёдер", career_cmp[col_d].iloc[-1]),
                             ("Иш Смит", career_cmp[col_i].iloc[-1])):
            top.annotate(label, xy=(years[-1] + 1, value), xytext=(6, 0),
                         textcoords="offset points", va="center", fontsize=9, color=INK)

        bot = axes[1]
        bot.set_title("Во сколько раз больше у Шрёдера", loc="left", fontsize=11,
                      color=INK, pad=10)
        bot.set_ylabel(ratio_ylabel, fontsize=9, color=INK_MUTED)
        bot.set_yscale("log")
        low, high = min(ratio.min(), 1) / 1.7, max(ratio.max(), 1) * 1.6
        bot.set_ylim(low, high)
        bot.axhspan(low, 1, color=sh, alpha=0.08, zorder=0)
        bot.axhline(1, color=INK_MUTED, lw=1.2, ls="--", alpha=0.7, zorder=1)
        step(bot, ratio, INK)
        dots(bot, ratio, INK, hollow=multi)
        bot.set_yticks([t for t in (0.25, 0.5, 1, 2, 5, 10, 20) if low <= t <= high])
        bot.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _: ("×" + f"{v:g}").replace(".", ","))
        )
        bot.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
        bot.annotate("паритет", xy=(1.05, 1), xytext=(0, 5), textcoords="offset points",
                     fontsize=8, color=INK_MUTED)
        bot.set_xlabel("год карьеры", fontsize=9, color=INK_MUTED)

        peak = ratio.idxmax()
        peak_year = int(career_cmp.loc[peak, "career_year"])
        bot.annotate(f"год {peak_year}: ×{ratio[peak]:.1f}".replace(".", ","),
                     xy=(peak_year + 0.5, ratio[peak]), xytext=(0, 10),
                     textcoords="offset points", ha="center", fontsize=8.5, color=INK)

        under = career_cmp.loc[ratio < 1, "career_year"].tolist()
        if under:
            span = f"год {under[0]}" if len(under) == 1 else f"годы {under[0]}–{under[-1]}"
            bot.annotate(f"{span}:\nИш зарабатывал больше",
                         xy=(under[-1] + 1.65, (low * 1) ** 0.5), ha="left",
                         va="center", fontsize=8.5, color=INK)

        axes[-1].set_xlim(years[0] - 0.15, years[-1] + 1.85)
        axes[-1].set_xticks(career_cmp["career_year"] + 0.5)
        axes[-1].set_xticklabels(career_cmp["career_year"], fontsize=9)

        handles = [
            plt.Line2D([], [], color=den, lw=2, label="Шрёдер, 2013/14 → 2026/27"),
            plt.Line2D([], [], color=sh, lw=2, label="Иш Смит, 2010/11 → 2023/24"),
            plt.Line2D([], [], color=sh, lw=0, marker="o", ms=6, mfc=SURFACE, mew=1.8,
                       label="у Иша в сезоне несколько контрактов"),
        ]
        legend = fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
                            fontsize=9, bbox_to_anchor=(0.5, -0.02))
        for text in legend.get_texts():
            text.set_color(INK)

        fig.suptitle(f"График {number}. Год карьеры против года карьеры", x=0.125, ha="left",
                     fontsize=14, color=INK)
        fig.tight_layout(rect=(0, 0.07, 1, 0.95))
        return fig

    return (make_vs_figure,)


@app.cell
def vs_figure_usd(make_vs_figure):
    make_vs_figure(
        "salary_d",
        "salary_i",
        "Ставка по контракту",
        "млн $",
        lambda v, _: f"{v / 1e6:.0f}",
        "× ставки Иша",
        number=3,
    )
    return


@app.cell
def vs_pct_intro(mo):
    mo.md(r"""
    ### То же самое в долях потолка

    Доллары сравнивают карьеры, разнесённые во времени: сезоны Шрёдера пришлись на
    более поздний и более богатый потолок. Тот же счёт в долях потолка снимает рост
    лиги — и разрыв заметно сжимается. Пик падает с ×15,6 до ×9,9, последний год
    карьеры — с ×4,6 до ×3,8.

    Провал ниже паритета остаётся на тех же годах 9–10: он не про инфляцию, а про
    то, что Шрёдер тогда играл за налогоплательщицкое MLE и минимум ветерана, а Иш
    сидел на ровных $6 000 000 от «Вашингтона».
    """)
    return


@app.cell
def vs_figure_pct(make_vs_figure):
    make_vs_figure(
        "pct_of_cap_d",
        "pct_of_cap_i",
        "Доля потолка лиги",
        "% потолка",
        lambda v, _: f"{v:.0f}",
        "× доли Иша",
        number=4,
    )
    return


@app.cell
def vs_note(career_cmp, ish_contracts, mo, schroder_contracts):
    def _career_year_note():
        """Примечание вместо графиков 3–4: год стажа, где Иш зарабатывал заметно больше.

        Год выбирается по данным: из лет ниже паритета — тот, где разрыв в долях
        потолка самый глубокий. Остальные годы ниже паритета называются отдельно.
        """

        def _num(value, places=2):
            return f"{value:.{places}f}".replace(".", ",")

        def _usd(value):
            return f"${int(value):,}".replace(",", " ")

        below = career_cmp[career_cmp["ratio_usd"] < 1]
        year = below.loc[below["ratio_pct"].idxmin()]
        others = below.drop(year.name)
        den = schroder_contracts.set_index("contract_no").loc[year["contract_no_d"]]
        ish_c = ish_contracts.set_index("contract_no").loc[year["contract_no_i"]]

        parity = " ".join(
            f"В {int(r.career_year)}-м году стажа ставки почти сравнялись: ×{_num(r.ratio_usd)}"
            f" в долларах и ×{_num(r.ratio_pct)} в долях потолка."
            for r in others.itertuples()
        )
        return mo.md(rf"""
        ### Примечание вместо графиков 3–4

        Графики 3 и 4 в статью не идут, от них остаётся одно примечание.

        > За {len(career_cmp)} лет стажа Иш Смит зарабатывал заметно больше Шрёдера
        > только в {int(year["career_year"])}-м. Шрёдер в {year["season_d"].replace("-", "/")}
        > получал {_usd(year["salary_d"])} ({_num(year["pct_of_cap_d"], 1)}% потолка) —
        > «{den["signing_team"]}», {den["mechanism"]}. Иш в {year["season_i"].replace("-", "/")}
        > получал {_usd(year["salary_i"])} ({_num(year["pct_of_cap_i"], 1)}% потолка) —
        > «{ish_c["signing_team"]}», {ish_c["mechanism"]}. Это в {_num(1 / year["ratio_usd"], 1)}
        > раза больше в долларах и в {_num(1 / year["ratio_pct"], 1)} раза в долях потолка.

        {parity} Во все остальные годы стажа больше зарабатывал Шрёдер.
        """)


    _career_year_note()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Таблицы под графиками

    Подписи на панелях выборочные, поэтому числа целиком — здесь.
    """)
    return


@app.cell
def _(schroder):
    schroder[
        [
            "season",
            "contract_no",
            "salary",
            "salary_cap",
            "pct_of_cap",
            "mle_non_taxpayer",
            "in_mle",
            "vet_min",
        ]
    ]
    return


@app.cell
def _(ish):
    ish[
        [
            "season",
            "contract_no",
            "color_key",
            "salary",
            "salary_cap",
            "pct_of_cap",
            "mle_non_taxpayer",
            "in_mle",
            "vet_min",
        ]
    ]
    return


@app.cell
def surplus_intro(mo):
    mo.md(r"""
    ## Излишек: продукт против цены

    Дальше — инструментальная проверка гипотезы А8: он почти никогда не нёс излишка.
    Вместо BPM/VORP, которых в `nba_api` нет и не будет (это метрики
    Basketball-Reference), продуктивность выражена через **долю игрока в продукте
    команды**, а цена — через долю потолка. Пять строк, считаются по CSV на диске:

    ```
    minutes_share = min_per_game / 240              # 240 = 5 игроков x 48 минут
    points_share  = pts_per_game / pts_per_team_game # средняя команда лиги за сезон
    product       = (minutes_share + points_share) / 2
    price         = salary_by_season / salary_cap
    surplus       = product - price
    ```

    Всё **за игру**, а не за сезон: сезонного знаменателя нет везде — у 2019-20
    `games_per_team` записан как `"64-75"` (COVID оборвал сезон). За игру 2019-20
    считается на равных со всеми, без пропусков.

    Знаменатель очков — средняя команда лиги, а не его собственный клуб. Это
    сознательное упрощение: на медленных командах доля завышена, на результативных
    занижена. Оговорка вынесена на график.

    Индекс 2–5 в 2013/14–2016/17 — механика новичковой шкалы, а не его заслуга: цену
    там назначает драфт, а не рынок.
    """)
    return


@app.cell
def surplus_sources(DATA, pd):
    league_avg = pd.read_csv(DATA / "nba_league_averages.csv")
    schroder_basic = pd.read_csv(DATA / "schroder_stats_basic.csv")
    schroder_advanced = pd.read_csv(DATA / "schroder_stats_advanced.csv")
    ish_basic = pd.read_csv(DATA / "ish_smith_stats_basic.csv")
    guard_cohort = pd.read_csv(DATA / "nba_pg_cohort.csv")
    return (
        guard_cohort,
        ish_basic,
        league_avg,
        schroder_advanced,
        schroder_basic,
    )


@app.cell
def surplus_shares(league_avg, pd):
    def season_rows(df):
        """Строка на сезон: `season_total` там, где он есть, иначе единственный клуб."""
        total = df[df["row_type"] == "season_total"]
        solo = df[(df["row_type"] == "season_team") & (~df["season"].isin(total["season"]))]
        return pd.concat([solo, total]).sort_values("season")


    def add_shares(df, min_col="min_per_game", pts_col="pts_per_game"):
        """Доли продукта. Минуты — от 240 на матч, очки — от средней команды лиги."""
        out = df.merge(league_avg[["season", "pts_per_team_game"]], on="season")
        out["minutes_share"] = out[min_col] / 240
        out["points_share"] = out[pts_col] / out["pts_per_team_game"]
        out["product"] = (out["minutes_share"] + out["points_share"]) / 2
        out["start_year"] = out["season"].str.slice(0, 4).astype(int)
        return out

    return add_shares, season_rows


@app.cell
def surplus_data(
    add_shares,
    schroder,
    schroder_basic,
    schroder_trades,
    season_rows,
):
    surplus_season = add_shares(season_rows(schroder_basic)).merge(
        schroder[["season", "salary", "salary_cap"]], on="season"
    )
    surplus_season["price"] = surplus_season["salary"] / surplus_season["salary_cap"]
    surplus_season["surplus"] = surplus_season["product"] - surplus_season["price"]
    surplus_season["index"] = surplus_season["product"] / surplus_season["price"]
    surplus_season["surplus_usd"] = surplus_season["surplus"] * surplus_season["salary_cap"]

    # Отрезки внутри сезона: сезон делится между клубами пропорционально сыгранным
    # матчам. Цена годовая и следует за игроком в обмене, поэтому не делится.
    # Порядок отрезков — порядок строк в CSV, он хронологический (сверено со
    # schroder_moves.csv: БОС→ХЬЮ, ТОР→БРУ, БРУ→ГСВ→ДЕТ, САК→КЛИ).
    surplus_stints = add_shares(
        schroder_basic[schroder_basic["row_type"] == "season_team"]
    ).merge(surplus_season[["season", "price"]], on="season")
    surplus_stints["gp_share"] = (
        surplus_stints["gp"] / surplus_stints.groupby("season")["gp"].transform("sum")
    )
    surplus_stints["x1"] = (
        surplus_stints["start_year"] + surplus_stints.groupby("season")["gp_share"].cumsum()
    )
    surplus_stints["x0"] = surplus_stints["x1"] - surplus_stints["gp_share"]

    # Обмены на оси графика 5. Сезон там делится по сыгранным матчам, а не по
    # календарю, поэтому отметка встаёт на начало отрезка клуба, куда он ушёл;
    # межсезонный обмен ложится на границу сезонов. Обмен в «Шарлотт» (август 2026)
    # матчей за новый клуб не дал и на ось не попадает.
    surplus_trades = schroder_trades.merge(
        surplus_stints[["start_year", "team_abbr", "x0"]],
        left_on=["season_start", "abbr"],
        right_on=["start_year", "team_abbr"],
    )[["date", "label", "x0"]]
    return surplus_season, surplus_stints, surplus_trades


@app.cell
def surplus_plot(
    EVENT_STYLES,
    FuncFormatter,
    GRID,
    INK,
    INK_MUTED,
    MaxNLocator,
    PALETTE,
    SURFACE,
    np,
    plt,
):
    SURPLUS_GREEN, OVERPAY_RED = PALETTE[2], PALETTE[7]

    _SURPLUS_NOTE = (
        "Всё за игру. Знаменатель очков — средняя команда лиги за сезон, а не его клуб:"
        " на медленных командах доля завышена, на результативных занижена.\n"
        "Сезоны с обменами разбиты по клубам пропорционально сыгранным матчам;"
        " цена годовая и внутри сезона не делится."
    )


    def _stint_steps(stints, column):
        """Ступенька по отрезкам: каждый отрезок — своя пара точек [x0, x1]."""
        xs, ys = [], []
        for _, row in stints.iterrows():
            xs += [row["x0"], row["x1"]]
            ys += [row[column], row[column]]
        return np.array(xs), np.array(ys)


    def surplus_axes(ax, stints, trades):
        """Оси графика 5 и его вариантов: границы сезонов, клубы, обмены.

        Клуб подписан на каждом отрезке, включая сезоны без обмена. Граница
        сезона — светлая сплошная линия, обмен — штрих с ▼ над осью.
        """
        ax.set_facecolor(SURFACE)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color=GRID, lw=1)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.tick_params(colors=INK_MUTED, labelsize=9, length=0)
        # steps без 2,5: иначе шаг 2,5% печатается как 2 / 5 / 8 / 10.
        ax.yaxis.set_major_locator(MaxNLocator(nbins=8, steps=[1, 2, 5, 10]))

        years = stints.drop_duplicates("season").sort_values("start_year")
        first, last = years["start_year"].min(), years["start_year"].max() + 1
        for year in range(first + 1, last):
            ax.axvline(year, color=GRID, lw=1.2, zorder=0.2)
        for _, row in stints.iterrows():
            ax.annotate(
                row["team_abbr"],
                xy=((row["x0"] + row["x1"]) / 2, 1),
                xycoords=("data", "axes fraction"),
                xytext=(0, -3),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=7,
                color=INK_MUTED,
            )
        for _, row in trades.iterrows():
            ax.axvline(row["x0"], color=INK, lw=1, ls=EVENT_STYLES["обмен"], alpha=0.5, zorder=3)
            ax.annotate(
                "▼",
                xy=(row["x0"], 1),
                xycoords=("data", "axes fraction"),
                ha="center",
                va="bottom",
                fontsize=8,
                color=INK,
            )

        ax.set_xlim(first - 0.1, last + 0.1)
        ax.set_xticks(years["start_year"] + 0.5)
        ax.set_xticklabels([s.replace("-", "/")[2:] for s in years["season"]], fontsize=9)


    def finish_surplus_figure(fig, handles, title, note):
        """Легенда с отметкой обмена, заголовок и оговорка — одинаково во всех вариантах."""
        handles = handles + [
            plt.Line2D([], [], color=INK, lw=1, ls=EVENT_STYLES["обмен"], marker="v", ms=5,
                       label="обмен: ▼ над осью, клуб — на отрезке"),
        ]
        legend = fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
                            fontsize=9, bbox_to_anchor=(0.5, -0.02))
        for text in legend.get_texts():
            text.set_color(INK)

        fig.suptitle(title, x=0.09, ha="left", fontsize=14, color=INK)
        fig.text(0.09, 0.905, note, ha="left", va="top", fontsize=8.2, color=INK_MUTED)
        fig.tight_layout(rect=(0, 0.10, 1, 0.85))
        return fig


    def make_surplus_figure(
        stints,
        trades,
        product="product",
        product_label="продукт: (доля минут + доля очков) / 2",
        fork=("minutes_share", "points_share"),
        title="График 5. Шрёдер: продукт против цены",
        note=_SURPLUS_NOTE,
    ):
        """Продукт против цены, заливка между кривыми по знаку.

        Кривая продукта внутри сезона разбита по клубам пропорционально сыгранным
        матчам; цена годовая и внутри сезона постоянна, поэтому её линия единая.
        `product` — колонка продукта, `fork` — пара долей для вилки или `None`.
        """
        xs, product_ys = _stint_steps(stints, product)
        price = _stint_steps(stints, "price")[1]

        fig, ax = plt.subplots(figsize=(11, 5.6))
        fig.patch.set_facecolor(SURFACE)
        surplus_axes(ax, stints, trades)

        if fork:
            # Вилка между двумя долями: видно, чем именно набран продукт.
            ax.fill_between(xs, _stint_steps(stints, fork[0])[1], _stint_steps(stints, fork[1])[1],
                            color=INK, alpha=0.07, lw=0, zorder=0.5)
        ax.fill_between(xs, product_ys, price, where=product_ys >= price,
                        color=SURPLUS_GREEN, alpha=0.22, lw=0, zorder=1)
        ax.fill_between(xs, product_ys, price, where=product_ys <= price,
                        color=OVERPAY_RED, alpha=0.22, lw=0, zorder=1)
        ax.plot(xs, product_ys, color=INK, lw=2.4, zorder=5)
        ax.plot(xs, price, color=PALETTE[0], lw=2.2, zorder=4)

        # Сверху — место под подписи клубов.
        ax.set_ylim(0, 0.21)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v * 100:.0f}%"))

        handles = [
            plt.Line2D([], [], color=INK, lw=2.4, label=product_label),
            plt.Line2D([], [], color=PALETTE[0], lw=2.2, label="цена: зарплата в долях потолка"),
        ]
        if fork:
            handles.append(plt.Rectangle((0, 0), 1, 1, color=INK, alpha=0.07,
                                         label="вилка: доля минут ↔ доля очков"))
        handles += [
            plt.Rectangle((0, 0), 1, 1, color=SURPLUS_GREEN, alpha=0.22, label="излишек"),
            plt.Rectangle((0, 0), 1, 1, color=OVERPAY_RED, alpha=0.22, label="переплата"),
        ]
        return finish_surplus_figure(fig, handles, title, note)

    return (
        OVERPAY_RED,
        SURPLUS_GREEN,
        finish_surplus_figure,
        make_surplus_figure,
        surplus_axes,
    )


@app.cell
def surplus_figure(make_surplus_figure, surplus_stints, surplus_trades):
    make_surplus_figure(surplus_stints, surplus_trades)
    return


@app.cell
def pub_figure5(
    EVENT_STYLES,
    GRID,
    INK,
    INK_MUTED,
    OVERPAY_RED,
    PALETTE,
    SURPLUS_GREEN,
    alt,
    halo_text,
    np,
    pd,
    pub_fit,
    season_x,
    surplus_stints,
    surplus_trades,
    tint,
):
    def _pub_surplus(stints, trades):
        """Публикационная версия графика 5: полезность против контракта, заливка по знаку."""
        st = stints.sort_values("x0").reset_index(drop=True)
        first, last = int(st["start_year"].min()), int(st["start_year"].max())
        x0 = season_x("x0", first, last, 0.1)
        x = season_x("x", first, last, 0.1)
        ymax = 0.22  # сверху — место под два ряда подписей клубов
        y = alt.Y("v:Q", title=None, scale=alt.Scale(domain=[0, ymax], nice=False),
                  axis=alt.Axis(values=[0, 0.05, 0.1, 0.15, 0.2], format=".0%"))

        # Заливки непрозрачные и смешиваются умножением: пересечение вилки и излишка
        # темнее, а цвет в легенде совпадает с цветом на графике.
        fill_names = ["излишек", "переплата", "вилка: доля минут ↔ доля очков"]
        fill = alt.Fill(
            "f:N",
            scale=alt.Scale(domain=fill_names,
                            range=[tint(SURPLUS_GREEN, 0.25), tint(OVERPAY_RED, 0.25), tint(INK, 0.08)]),
            legend=alt.Legend(symbolType="square", symbolStrokeWidth=0, direction="vertical"),
        )
        boundaries = alt.Chart(pd.DataFrame({"x": range(first + 1, last + 1)})).mark_rule(
            color=GRID, strokeWidth=1.2).encode(x)
        fork = alt.Chart(st.assign(v=st["minutes_share"], f=fill_names[2])).mark_rect(blend="multiply").encode(
            x0, x2="x1:Q", y=y, y2="points_share:Q", fill=fill)
        gap = alt.Chart(
            st.assign(v=st["product"], f=np.where(st["product"] >= st["price"], fill_names[0], fill_names[1]))
        ).mark_rect(blend="multiply").encode(x0, x2="x1:Q", y=y, y2="price:Q", fill=fill)

        # Кривые — ступенькой по отрезкам «сезон × клуб»: у отрезка точка в начале и в конце.
        series = ["полезность: (доля минут + доля очков) / 2", "контракт: зарплата в долях потолка"]
        color = alt.Color("series:N", scale=alt.Scale(domain=series, range=[INK, PALETTE[0]]),
                          legend=alt.Legend(symbolType="stroke", symbolStrokeWidth=2.5, direction="vertical"))
        pts = pd.concat([st.assign(x=st["x0"], key=2 * st.index), st.assign(x=st["x1"], key=2 * st.index + 1)])
        price_line = alt.Chart(pts.assign(v=pts["price"], series=series[1])).mark_line(strokeWidth=2.4).encode(
            x, y, color, order="key:Q")
        product_line = alt.Chart(pts.assign(v=pts["product"], series=series[0])).mark_line(strokeWidth=2.4).encode(
            x, y, color, order="key:Q")

        # Клуб — одна подпись на подряд идущие отрезки одного клуба, в два ряда.
        runs = (
            st.assign(run=(st["team_abbr"] != st["team_abbr"].shift()).cumsum())
            .groupby("run")
            .agg(team=("team_abbr", "first"), x0=("x0", "min"), x1=("x1", "max"))
            .reset_index(drop=True)
        )
        runs = runs.assign(x=(runs["x0"] + runs["x1"]) / 2, v=ymax, row=runs.index % 2)
        clubs = []
        for row in range(2):
            clubs += halo_text(alt.Chart(runs[runs["row"] == row]).encode(x, y, text="team:N"),
                               baseline="top", dy=3 + 13 * row, fontSize=10, color=INK_MUTED)

        tr = trades.assign(x=trades["x0"], v=ymax, legend="обмен ▼")
        trade_rules = alt.Chart(tr).mark_rule(strokeWidth=1, color=INK, opacity=0.5).encode(
            x, alt.StrokeDash("legend:N", scale=alt.Scale(domain=["обмен ▼"], range=[list(EVENT_STYLES["обмен"][1])]),
                              legend=alt.Legend(symbolType="stroke", symbolStrokeColor=INK)))
        trade_marks = alt.Chart(tr).mark_text(text="▼", baseline="bottom", dy=-1, fontSize=10, color=INK).encode(x, y)

        chart = alt.layer(boundaries, fork, gap, price_line, product_line, trade_rules, *clubs, trade_marks)
        return pub_fit(chart, "Сравнение полезности и контракта")


    pub_chart5 = _pub_surplus(surplus_stints, surplus_trades)
    pub_chart5
    return (pub_chart5,)


@app.cell
def surplus_table(surplus_season):
    def _surplus_table():
        """Числа под графиком: в статью пойдут индекс и доллары, на график — проценты."""
        out = surplus_season[[
            "season", "team_abbr", "gp", "minutes_share", "points_share",
            "product", "price", "index", "surplus_usd",
        ]].copy()
        for column in ("minutes_share", "points_share", "product", "price"):
            out[column] = (out[column] * 100).round(1)
        out["index"] = out["index"].round(2)
        out["surplus_usd"] = (out["surplus_usd"] / 1e6).round(1)
        return out.rename(columns={
            "team_abbr": "клуб", "minutes_share": "доля минут, %",
            "points_share": "доля очков, %", "product": "продукт, %", "price": "цена, %",
            "index": "индекс продукт/цена", "surplus_usd": "излишек, млн $",
        })


    _surplus_table()
    return


@app.cell(hide_code=True)
def surplus_variants_intro(mo):
    mo.md(r"""
    ### Варианты графика 5

    Тот же расчёт, другая форма. На графике 5 излишек читается по заливке между двумя
    ступеньками — глазу приходится сравнивать площади. Два варианта убирают это
    сравнение: **5а** рисует разрыв «продукт − цена» одной палкой на отрезок,
    **5б** переводит его в доллары и оставляет один знак — вверх или вниз.

    Во всех трёх одинаковая ось: светлые вертикали — границы сезонов, ▼ со штрихом —
    обмен, над каждым отрезком — клуб. Отметки обменов стоят не по календарю, а на
    начале отрезка нового клуба: сезон здесь делится по сыгранным матчам.
    """)
    return


@app.cell
def surplus_variant_a(
    FuncFormatter,
    INK,
    INK_MUTED,
    OVERPAY_RED,
    PALETTE,
    SURFACE,
    SURPLUS_GREEN,
    finish_surplus_figure,
    plt,
    surplus_axes,
    surplus_stints,
    surplus_trades,
):
    def _dumbbell_figure():
        """Вариант 5а: на каждый отрезок — «гантель» от цены до продукта.

        Вместо заливки между ступеньками — одна вертикальная палка на отрезок: её
        длина и цвет и есть излишек или переплата, подпись — индекс продукт/цена.
        """
        xs = (surplus_stints["x0"] + surplus_stints["x1"]) / 2
        product, price = surplus_stints["product"], surplus_stints["price"]
        surplus = product >= price

        fig, ax = plt.subplots(figsize=(11, 5.6))
        fig.patch.set_facecolor(SURFACE)
        surplus_axes(ax, surplus_stints, surplus_trades)

        for mask, color in ((surplus, SURPLUS_GREEN), (~surplus, OVERPAY_RED)):
            ax.vlines(xs[mask], price[mask], product[mask], color=color, lw=5, alpha=0.5, zorder=2)
        ax.plot(xs, price, "o", ms=7, color=PALETTE[0], mec=SURFACE, mew=1.4, zorder=4)
        ax.plot(xs, product, "o", ms=7, color=INK, mec=SURFACE, mew=1.4, zorder=5)
        # В сезонах с двумя-тремя клубами подписи соседних отрезков идут в два ряда.
        rows = surplus_stints.groupby("season").cumcount() % 2
        for x, p, q, row in zip(xs, product, price, rows):
            ax.annotate(f"×{p / q:.1f}".replace(".", ","), xy=(x, min(p, q)), xytext=(0, -7 - 9 * row),
                        textcoords="offset points", ha="center", va="top", fontsize=7,
                        color=INK_MUTED)

        ax.set_ylim(0, 0.21)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v * 100:.0f}%"))

        handles = [
            plt.Line2D([], [], color=INK, lw=0, marker="o", ms=7, mec=SURFACE,
                       label="продукт: (доля минут + доля очков) / 2"),
            plt.Line2D([], [], color=PALETTE[0], lw=0, marker="o", ms=7, mec=SURFACE,
                       label="цена: зарплата в долях потолка"),
            plt.Line2D([], [], color=SURPLUS_GREEN, lw=5, alpha=0.5, label="излишек"),
            plt.Line2D([], [], color=OVERPAY_RED, lw=5, alpha=0.5, label="переплата"),
        ]
        return finish_surplus_figure(
            fig,
            handles,
            "График 5а. Шрёдер: продукт против цены, по отрезкам",
            "Тот же расчёт, что на графике 5. Палка — разрыв между продуктом и ценой на отрезке,"
            " подпись под ней — индекс продукт/цена.\n"
            "Отрезок стоит в середине своей доли сыгранных матчей сезона.",
        )


    _dumbbell_figure()
    return


@app.cell
def surplus_variant_b(
    FuncFormatter,
    INK,
    INK_MUTED,
    MaxNLocator,
    OVERPAY_RED,
    SURFACE,
    SURPLUS_GREEN,
    finish_surplus_figure,
    np,
    plt,
    surplus_axes,
    surplus_season,
    surplus_stints,
    surplus_trades,
):
    def _surplus_bars_figure():
        """Вариант 5б: излишек в долларах столбиками, ширина — доля сыгранных матчей.

        Один знак вместо двух кривых: вверх — излишек, вниз — переплата. Высота —
        излишек в пересчёте на целый сезон, ширина — доля сезона за клубом, поэтому
        площадь столбика пропорциональна излишку, набранному за этим клубом.
        """
        stints = surplus_stints.merge(surplus_season[["season", "salary_cap"]], on="season")
        stints["surplus_usd"] = (stints["product"] - stints["price"]) * stints["salary_cap"]
        positive = stints["surplus_usd"] >= 0

        fig, ax = plt.subplots(figsize=(11, 5.6))
        fig.patch.set_facecolor(SURFACE)
        surplus_axes(ax, stints, surplus_trades)

        ax.bar(stints["x0"] + 0.03, stints["surplus_usd"], width=stints["gp_share"] - 0.06,
               align="edge", color=np.where(positive, SURPLUS_GREEN, OVERPAY_RED), alpha=0.75,
               zorder=2)
        ax.axhline(0, color=INK_MUTED, lw=1, zorder=3)
        for row in stints.itertuples():
            up = row.surplus_usd >= 0
            ax.annotate(f"{row.surplus_usd / 1e6:+.1f}".replace(".", ",").replace("-", "−"),
                        xy=((row.x0 + row.x1) / 2, row.surplus_usd), xytext=(0, 3 if up else -3),
                        textcoords="offset points", ha="center", va="bottom" if up else "top",
                        fontsize=7, color=INK)

        ax.set_ylim(min(stints["surplus_usd"].min(), 0) - 2.5e6, stints["surplus_usd"].max() * 1.3)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=8, steps=[1, 2, 5, 10]))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1e6:.0f}"))
        ax.set_ylabel("млн $ в пересчёте на сезон", fontsize=9, color=INK_MUTED)

        handles = [
            plt.Rectangle((0, 0), 1, 1, color=SURPLUS_GREEN, alpha=0.75,
                          label="излишек: продукт больше цены"),
            plt.Rectangle((0, 0), 1, 1, color=OVERPAY_RED, alpha=0.75,
                          label="переплата: цена больше продукта"),
        ]
        return finish_surplus_figure(
            fig,
            handles,
            "График 5б. Шрёдер: излишек в долларах",
            "Излишек = (продукт − цена) × потолок сезона, продукт — как на графике 5."
            " Высота — в пересчёте на целый сезон.\n"
            "Ширина — доля сыгранных матчей за клубом, поэтому площадь столбика — излишек,"
            " набранный за этим клубом.",
        )


    _surplus_bars_figure()
    return


@app.cell
def metric_data(cohort_chart, schroder_advanced, surplus_stints):
    # Кандидаты в сводную метрику продукта — по тем же отрезкам «сезон × клуб».
    _advanced = schroder_advanced[schroder_advanced["row_type"] == "season_team"]
    metric_stints = surplus_stints.merge(
        _advanced[["season", "team_abbr", "pie", "usg_pct", "net_rating"]],
        on=["season", "team_abbr"],
    )
    # USG% считается только за его минуты на площадке, поэтому доля владений
    # команды за весь матч — это USG%, умноженный на долю матча, которую он сыграл.
    metric_stints["possession_share"] = metric_stints["usg_pct"] * metric_stints["min_per_game"] / 48
    for _column in ("pie", "possession_share"):
        metric_stints["index_" + _column] = metric_stints[_column] / metric_stints["price"]
    metric_stints["index_product"] = metric_stints["product"] / metric_stints["price"]

    # Годятся ли кандидаты на ту же шкалу, что и цена: сверка по когорте защитников —
    # той же, что на графике 6 (от 8 минут за игру и от COHORT_MIN_GP матчей).
    _cohort = cohort_chart.assign(
        possession_share=cohort_chart["usg_pct"] * cohort_chart["min"] / 48
    )
    metric_scale = _cohort.groupby("season").agg(
        product_median=("product", "median"),
        pie_median=("pie", "median"),
        possession_median=("possession_share", "median"),
    )
    metric_scale["pie_to_product"] = metric_scale["pie_median"] / metric_scale["product_median"]
    metric_corr = _cohort[["pie", "possession_share", "net_rating"]].corrwith(_cohort["product"])
    return metric_corr, metric_scale, metric_stints


@app.cell
def metric_intro(
    COHORT_MIN_GP,
    metric_corr,
    metric_scale,
    metric_stints,
    mo,
    textwrap,
):
    def _metric_intro():
        """Числа и вердикты в тексте считаются из `metric_stints` и `metric_scale`."""

        def _num(value, places=2):
            return f"{value:.{places}f}".replace(".", ",")

        def _span(values):
            return _num(values.min()) if len(values) == 1 else f"{_num(values.min())}–{_num(values.max())}"

        def _verdict(values):
            # Полоса 0,9–1,1 — «около нуля», как в оговорке к графику 5.
            if values.max() < 0.9:
                return "переплата"
            if values.min() > 1.1:
                return "излишек"
            if values.min() >= 0.9 and values.max() <= 1.1:
                return "около нуля"
            if values.max() <= 1.1:
                return "от переплаты до нуля"
            return "смешанная картина"

        def _line(label, rows):
            shares, pie = rows["index_product"], rows["index_pie"]
            return (
                f"- {label}: по долям {_verdict(shares)} ({_span(shares)}),"
                f" по PIE {_verdict(pie)} ({_span(pie)})"
            )

        lines = ";\n".join([
            _line("четыре года контракта на $70 млн (2017/18 – 2020/21)",
                  metric_stints[metric_stints["season"].between("2017-18", "2020-21")]),
            _line("2022/23 в «Лейкерс»", metric_stints[metric_stints["season"] == "2022-23"]),
            _line("2023/24 («Торонто» и «Бруклин»)", metric_stints[metric_stints["season"] == "2023-24"]),
        ]) + "."

        # Шапка и хвост с отступом, строки списка — без: dedent у каждой части свой,
        # иначе общий отступ нулевой и шапка уходит в блок кода.
        head = textwrap.dedent(rf"""
        ### Сводная метрика вместо долей

        Долевой продукт — эвристика: минуты и очки, без передач, подборов, потерь и
        эффективности. Из уже собранного `schroder_stats_advanced.csv` (класс A) на
        роль сводной метрики пробовались три колонки. Мерило одно: метрика должна
        быть **долей**, иначе её нельзя поставить на одну шкалу с ценой — долей
        потолка — без произвольного коэффициента.

        | кандидат | доля ли это | корреляция с долевым продуктом по когорте | вердикт |
        |---|---|---|---|
        | **PIE** | да: доля статистических событий матча за игроком — очки, подборы, передачи, перехваты, блоки минус промахи, потери и фолы | {_num(metric_corr["pie"])} | **берём в график 5в**: единственный кандидат, который добавляет информацию |
        | **USG% × минуты / 48** | да: доля владений команды за матч, которые он закончил | {_num(metric_corr["possession_share"])} | не берём: почти копия долевого продукта — тот же объём, без эффективности |
        | **NET_RATING** | нет: разница очков команды на 100 владений, пока он на площадке | {_num(metric_corr["net_rating"])} | не берём: меряет пятёрку, а не игрока, и на шкалу цены не ставится |

        **Шкала PIE сверена по когорте графика 6** — защитники от 8 минут за игру и
        от {COHORT_MIN_GP} матчей за сезон. Медиана PIE в каждом сезоне
        составляет {_span(metric_scale["pie_to_product"])} от медианы долевого
        продукта, поэтому PIE ложится на ту же ось без пересчёта. Для других позиций
        это не проверялось.

        **Что меняет PIE** (индекс продукт/цена по отрезкам; таблица и график 5в ниже):

        """)
        tail = textwrap.dedent(r"""

        Оговорка остаётся прежней: PIE, как и доли, считается от событий матча, а не
        от вклада в победу, и BPM/VORP в данных по-прежнему нет.
        """)
        return mo.md(head + lines + tail)


    _metric_intro()
    return


@app.cell
def metric_table(metric_stints):
    def _metric_table():
        """Три индекса продукт/цена рядом: по долям, по PIE, по доле владений."""
        out = metric_stints[[
            "season", "team_abbr", "gp", "product", "pie", "possession_share", "price",
            "index_product", "index_pie", "index_possession_share", "net_rating",
        ]].copy()
        for column in ("product", "pie", "possession_share", "price"):
            out[column] = (out[column] * 100).round(1)
        for column in ("index_product", "index_pie", "index_possession_share"):
            out[column] = out[column].round(2)
        return out.rename(columns={
            "team_abbr": "клуб", "product": "продукт по долям, %", "pie": "PIE, %",
            "possession_share": "доля владений, %", "price": "цена, %",
            "index_product": "индекс по долям", "index_pie": "индекс по PIE",
            "index_possession_share": "индекс по владениям",
        })


    _metric_table()
    return


@app.cell
def surplus_variant_pie(
    make_surplus_figure,
    metric_scale,
    metric_stints,
    surplus_trades,
):
    _low, _high = metric_scale["pie_to_product"].min(), metric_scale["pie_to_product"].max()

    make_surplus_figure(
        metric_stints,
        surplus_trades,
        product="pie",
        product_label="продукт: PIE — доля событий матча за ним",
        fork=None,
        title="График 5в. Шрёдер: PIE против цены",
        note=(
            "PIE — доля статистических событий матча за игроком: очки, подборы, передачи,"
            " перехваты и блоки минус промахи, потери и фолы.\n"
            f"Медиана PIE защитников лиги (когорта графика 6) — {_low:.0%}–{_high:.0%} медианы долевого продукта,"
            " поэтому шкала с ценой общая, без пересчёта."
        ),
    )
    return


@app.cell
def cohort_intro(mo):
    mo.md(r"""
    ## На фоне защитников лиги

    Второй график — только продукт, без цены: зарплат когорты ни в одном CSV нет,
    и в этой задаче мы за ними не идём. Боксплот на сезон показывает всё
    распределение; медиана и среднее из `nba_pg_baseline.csv` его не показывают,
    поэтому сюда добавлена сырая выборка `nba_pg_cohort.csv` — 2723 строки
    «защитник × сезон» за 2010/11 – 2025/26.

    Когорта — **все чистые защитники** (`POSITION = G`, без `G-F` и `F-G`) от восьми
    минут за игру и от 15 матчей за сезон. Порог по матчам ставится здесь, в
    ноутбуке: в CSV его нет, и без него верх распределения держат игроки с парой
    матчей и большими минутами. Не только разыгрывающие: `nba_api` не делит PG и SG в
    `PlayerIndex`. Поэтому и в подписи, и в тексте статьи — «защитники», а не
    «разыгрывающие»; имя файла `nba_pg_baseline.csv` здесь вводит в заблуждение.

    ⚠️ Шрёдер и Иш сами входят в когорту — их точки являются членами собственной
    выборки. При N ≈ 150 на квартили это не влияет, но сказать об этом надо;
    исключать их не будем.
    """)
    return


@app.cell
def cohort_data(
    add_shares,
    guard_cohort,
    ish_basic,
    schroder_basic,
    season_rows,
):
    cohort_shares = add_shares(guard_cohort, min_col="min", pts_col="pts")
    cohort_seasons = sorted(cohort_shares["season"].unique())

    # График 6 — только игроки хотя бы с 15 матчами за сезон. В CSV порога по
    # матчам нет, и без него верх распределения держат игроки с парой матчей и
    # большими минутами. Та же когорта идёт в калибровку PIE (ячейка metric_data);
    # сверка с nba_pg_baseline.csv берёт CSV целиком.
    COHORT_MIN_GP = 15
    cohort_chart = cohort_shares[cohort_shares["gp"] >= COHORT_MIN_GP]

    schroder_shares = add_shares(season_rows(schroder_basic)).set_index("season")
    ish_shares = add_shares(season_rows(ish_basic)).set_index("season")
    return (
        COHORT_MIN_GP,
        cohort_chart,
        cohort_seasons,
        cohort_shares,
        ish_shares,
        schroder_shares,
    )


@app.cell
def cohort_check(DATA, guard_cohort, mo, pd):
    def _cohort_check():
        """Сырая когорта против схлопнутой базовой линии — та же выборка или нет.

        Округление здесь то же, что в `fetch_stats.py` (питоновский `round`):
        `Series.round` из pandas на ровных половинках даёт другой знак — 8,95 → 9,0
        против 8,9, и семь медиан из 112 «разошлись» бы на единицу последнего знака.
        """
        digits = {"pts": 1, "ast": 1, "min": 1, "usg_pct": 3, "ts_pct": 3,
                  "pie": 3, "net_rating": 1}
        baseline = pd.read_csv(DATA / "nba_pg_baseline.csv").set_index("season")
        bad_rows = []
        for season, group in guard_cohort.groupby("season"):
            if len(group) != baseline.loc[season, "sample_size"]:
                bad_rows.append(f"{season}: строк {len(group)}, а sample_size"
                                f" {baseline.loc[season, 'sample_size']}")
            for metric, places in digits.items():
                got = round(float(group[metric].median()), places)
                want = baseline.loc[season, metric + "_median"]
                if got != want:
                    bad_rows.append(f"{season} / {metric}: {got} против {want}")
        return bad_rows


    mo.md(
        f"**Когорта сверена с `nba_pg_baseline.csv`.** {len(guard_cohort)} строк,"
        f" {guard_cohort['season'].nunique()} сезонов; число строк в каждом сезоне равно"
        " `sample_size`, медианы по всем семи метрикам совпадают до последнего знака."
        f" Пустых значений: {int(guard_cohort.isna().sum().sum())}."
        if not _cohort_check()
        else "**Когорта НЕ сходится с `nba_pg_baseline.csv`:**\n"
        + "\n".join("- " + line for line in _cohort_check())
    )
    return


@app.cell
def cohort_plot(FuncFormatter, GRID, INK, INK_MUTED, SURFACE, plt):
    COHORT_PANELS = [
        ("minutes_share", "Доля минут команды (за игру, от 240)"),
        ("points_share", "Доля очков средней команды лиги (за игру)"),
    ]


    def make_cohort_figure(cohort, seasons, highlights, min_gp):
        """Боксплот по сезонам для двух долей; выделенные игроки — точками поверх.

        `highlights` — список (таблица по сезонам, цвет, подпись). Точки соединены
        тонкой линией: без неё траектория за 16 сезонов не читается. `min_gp` —
        порог по матчам, которым уже отфильтрована `cohort`; нужен только для подписи.
        """
        sizes = cohort.groupby("season").size()
        fig, axes = plt.subplots(2, 1, figsize=(11.5, 8.4), sharex=True)
        fig.patch.set_facecolor(SURFACE)

        for ax, (column, panel_title) in zip(axes, COHORT_PANELS):
            ax.set_facecolor(SURFACE)
            ax.set_axisbelow(True)
            ax.grid(axis="y", color=GRID, lw=1)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            for side in ("left", "bottom"):
                ax.spines[side].set_color(GRID)
            ax.tick_params(colors=INK_MUTED, labelsize=9, length=0)
            ax.set_title(panel_title, loc="left", fontsize=11, color=INK, pad=10)

            boxes = ax.boxplot(
                [cohort.loc[cohort["season"] == s, column].values for s in seasons],
                positions=range(len(seasons)), widths=0.62, patch_artist=True, zorder=2,
            )
            for box in boxes["boxes"]:
                box.set(facecolor="#eceae5", edgecolor=GRID, lw=1)
            for part in ("whiskers", "caps"):
                for item in boxes[part]:
                    item.set(color=INK_MUTED, lw=0.9, alpha=0.7)
            for median in boxes["medians"]:
                median.set(color=INK_MUTED, lw=1.6)
            for flier in boxes["fliers"]:
                flier.set(marker="o", ms=2.2, mfc=INK_MUTED, mec="none", alpha=0.35)

            # Медиана подписана прямо у последнего боксплота, чтобы не путать её с квартилями.
            last_median = cohort.loc[cohort["season"] == seasons[-1], column].median()
            ax.annotate("медиана", xy=(len(seasons) - 1 + 0.31, last_median), xytext=(4, 0),
                        textcoords="offset points", va="center", fontsize=8, color=INK_MUTED)

            for table, color, _ in highlights:
                xs = [i for i, s in enumerate(seasons) if s in table.index]
                ys = [table.loc[s, column] for s in seasons if s in table.index]
                ax.plot(xs, ys, color=color, lw=1.2, alpha=0.55, zorder=4)
                ax.plot(xs, ys, "o", ms=7, color=color, mec=SURFACE, mew=1.4, zorder=5)

            ax.set_ylim(bottom=0)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v * 100:.0f}%"))

        # Справа — место под подпись медианы.
        axes[-1].set_xlim(-0.6, len(seasons) + 0.2)
        axes[-1].set_xticks(range(len(seasons)))
        axes[-1].set_xticklabels([s.replace("-", "/")[2:] for s in seasons], fontsize=9)

        handles = [
            plt.Line2D([], [], color=color, lw=0, marker="o", ms=7, mec=SURFACE, mew=1.4,
                       label=label)
            for _, color, label in highlights
        ] + [
            plt.Rectangle((0, 0), 1, 1, facecolor="#eceae5", edgecolor=GRID,
                          label="все защитники лиги: квартили, усы 1,5·IQR, точками — выбросы"),
            plt.Line2D([], [], color=INK_MUTED, lw=1.6, label="медиана когорты"),
        ]
        legend = fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
                            fontsize=9, bbox_to_anchor=(0.5, 0.005))
        for text in legend.get_texts():
            text.set_color(INK)

        fig.suptitle("График 6. На фоне защитников лиги", x=0.075, ha="left", fontsize=14, color=INK)
        fig.text(
            0.075, 0.925,
            "Когорта — все чистые защитники (POSITION=G, без G-F/F-G) от 8 минут за игру"
            f" и от {min_gp} матчей за сезон, {sizes.min()}–{sizes.max()} человек за сезон.\n"
            "Только продукт, без цены: зарплат когорты в данных нет."
            " Шрёдер и Иш — сами внутри своей выборки.",
            ha="left", va="top", fontsize=8.2, color=INK_MUTED,
        )
        fig.tight_layout(rect=(0, 0.085, 1, 0.90))
        return fig

    return COHORT_PANELS, make_cohort_figure


@app.cell
def cohort_figure(
    COHORT_MIN_GP,
    PALETTE,
    cohort_chart,
    cohort_seasons,
    ish_shares,
    make_cohort_figure,
    schroder_shares,
):
    make_cohort_figure(
        cohort_chart,
        cohort_seasons,
        min_gp=COHORT_MIN_GP,
        highlights=[
            (schroder_shares, PALETTE[0], "Шрёдер"),
            (ish_shares, PALETTE[1], "Иш Смит"),
        ],
    )
    return


@app.cell
def pub_figure6(
    COHORT_MIN_GP,
    COHORT_PANELS,
    GRID,
    INK,
    INK_MUTED,
    PALETTE,
    alt,
    cohort_chart,
    ish_shares,
    pd,
    pub_config,
    schroder_shares,
):
    def _pub_cohort(cohort, highlights, min_gp):
        """Публикационная версия графика 6: боксплоты когорты и траектории игроков, две панели."""
        box_fill = "#eceae5"
        seasons = sorted(cohort["season"].unique())
        names = [name for _, _, name in highlights]
        players = pd.concat([
            table.reset_index()[["season", "minutes_share", "points_share"]].assign(player=name)
            for table, _, name in highlights
        ])
        box_legend = "защитники лиги: квартили, усы — 1,5 межквартильного размаха, точки — выбросы"

        panels = []
        for i, (col, panel_title) in enumerate(COHORT_PANELS):
            x = alt.X("season:O", title=None, scale=alt.Scale(domain=seasons),
                      axis=alt.Axis(labelExpr="slice(datum.value, 2, 4) + '/' + slice(datum.value, 5, 7)",
                                    labelAngle=0, labels=i == len(COHORT_PANELS) - 1))
            y = alt.Y(f"{col}:Q", title=None, axis=alt.Axis(format=".0%", tickCount=4))
            box = alt.Chart(cohort).mark_boxplot(
                extent=1.5,
                size=20,
                box={"fill": box_fill, "stroke": GRID},
                median={"stroke": INK_MUTED, "strokeWidth": 1.6},
                rule={"stroke": INK_MUTED, "opacity": 0.7},
                ticks={"stroke": INK_MUTED, "opacity": 0.7, "size": 8},
                outliers={"size": 5, "fill": INK_MUTED, "filled": True, "strokeWidth": 0, "opacity": 0.35},
            ).encode(x, y)
            # У составной марки boxplot своей легенды нет — её даёт невидимый квадрат.
            box_key = alt.Chart(pd.DataFrame({"k": [box_legend]})).mark_square(opacity=0).encode(
                fill=alt.Fill("k:N", scale=alt.Scale(range=[box_fill]),
                              legend=alt.Legend(symbolType="square", symbolOpacity=1,
                                                symbolStrokeColor=GRID, symbolStrokeWidth=1)))
            trajectory = alt.Chart(players).encode(
                x, y,
                alt.Color("player:N", scale=alt.Scale(domain=names, range=[c for _, c, _ in highlights]),
                          legend=alt.Legend(symbolType="circle", symbolSize=80, symbolOpacity=1)),
            )
            # Медиана подписана отдельно, у последнего боксплота.
            median = cohort.loc[cohort["season"] == seasons[-1], col].median()
            median_label = alt.Chart(
                pd.DataFrame({"season": [seasons[-1]], col: [median], "t": ["медиана"]})
            ).mark_text(align="left", dx=13, fontSize=11, color=INK_MUTED).encode(x, y, text="t:N")
            panels.append(
                alt.layer(
                    box,
                    box_key,
                    trajectory.mark_line(strokeWidth=1.3, opacity=0.55),
                    trajectory.mark_circle(size=50, opacity=1, stroke="white", strokeWidth=1.4),
                    median_label,
                ).properties(
                    width=720, height=108,
                    title=alt.TitleParams(panel_title, fontSize=13, fontWeight="normal", color=INK),
                )
            )

        chart = (
            alt.vconcat(*panels, spacing=8)
            .resolve_scale(y="independent")
            .properties(title=alt.TitleParams(
                "Польза в сравнении с другими защитниками",
                subtitle=f"Все защитники лиги от 8 минут за игру и от {min_gp} матчей за сезон",
            ))
        )
        return pub_config(chart)


    pub_chart6 = _pub_cohort(
        cohort_chart,
        [(schroder_shares, PALETTE[0], "Шрёдер"), (ish_shares, PALETTE[1], "Иш Смит")],
        min_gp=COHORT_MIN_GP,
    )
    pub_chart6
    return (pub_chart6,)


@app.cell
def cohort_minutes_2122(COHORT_MIN_GP, cohort_chart, cohort_shares, mo):
    def _minutes_leaders():
        """Кто держал верх доли минут в 2021/22 и что с ним сделал порог по матчам.

        Таблица — по когорте целиком, без порога: иначе самой находки не видно.
        """

        def _pct(value):
            return f"{value * 100:.1f}%".replace(".", ",")

        def _games(n):
            return f"{n} " + ("матч" if n == 1 else "матча" if n < 5 else "матчей")

        def _row(r):
            minutes = f"{r.min:.1f}".replace(".", ",")
            return f"| {r.player} | {r.team_abbr} | {r.gp} | {minutes} | {_pct(r.minutes_share)} |"

        season = cohort_shares[cohort_shares["season"] == "2021-22"]
        top = season.nlargest(6, "minutes_share")
        after = cohort_chart[cohort_chart["season"] == "2021-22"].nlargest(1, "minutes_share").iloc[0]
        leaders = cohort_shares.loc[cohort_shares.groupby("season")["minutes_share"].idxmax()]
        artifacts = "; ".join(
            f"{r.season.replace('-', '/')} — {r.player} ({_games(r.gp)}, {_pct(r.minutes_share)})"
            for r in leaders[leaders["gp"] < COHORT_MIN_GP].itertuples()
        )

        return mo.md(
            "### Кто набрал такую долю минут в 2021/22\n\n"
            "Верх уса 2021/22 на панели минут был не звездой, а игроком с горсткой матчей"
            " (когорта целиком, без порога по матчам):\n\n"
            "| игрок | клуб | матчей | минут за игру | доля минут |\n|---|---|---|---|---|\n"
            + "\n".join(_row(r) for r in top.itertuples())
            + "\n\n"
            "В CSV порог когорты — только 8 минут за игру, порога по матчам нет. Поэтому верх"
            " распределения в отдельные сезоны держали игроки с парой матчей и большими"
            f" минутами: {artifacts}.\n\n"
            f"**На графике 6 они убраны:** там когорта — от 8 минут за игру и от"
            f" {COHORT_MIN_GP} матчей за сезон; на графике {len(cohort_chart)} из {len(cohort_shares)} строк CSV."
            f" Верх 2021/22 после порога — {after['player']} ({after['team_abbr']},"
            f" {_games(after['gp'])}, {_pct(after['minutes_share'])})."
        )


    _minutes_leaders()
    return


@app.cell
def pub_export(
    DATA,
    pd,
    pub_chart1,
    pub_chart2,
    pub_chart5,
    pub_chart6,
    save_png,
):
    # Экспорт публикационных графиков для sports.ru: PNG ×2 в writing/charts/.
    _charts = DATA.parent / "charts"
    _charts.mkdir(exist_ok=True)
    pd.DataFrame(
        [
            (name, *save_png(chart, _charts / name))
            for name, chart in [
                ("chart1_schroder_contracts.png", pub_chart1),
                ("chart2_ish_smith_contracts.png", pub_chart2),
                ("chart5_value_vs_contract.png", pub_chart5),
                ("chart6_guards_cohort.png", pub_chart6),
            ]
        ],
        columns=["файл", "ширина, px", "высота, px"],
    )
    return


if __name__ == "__main__":
    app.run()
