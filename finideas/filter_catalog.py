"""Finviz screener filter fields for the custom scanner builder.

Covers the main fields from Finviz All filters (Descriptive / Fundamental /
Technical / News). Each option maps to an Elite ``f=`` code. ``Any`` = no code.
"""

from __future__ import annotations

from dataclasses import dataclass

from finideas.custom_range import CUSTOM_SENTINEL, CustomRangeSpec


@dataclass(frozen=True)
class FilterOption:
    label: str
    code: str  # "" means Any / not applied


@dataclass(frozen=True)
class FilterField:
    id: str
    label: str
    category: str  # Descriptive | Fundamental | Technical | News
    options: tuple[FilterOption, ...]
    custom: CustomRangeSpec | None = None


def _any() -> FilterOption:
    return FilterOption("Any", "")


def _opts(*pairs: tuple[str, str]) -> tuple[FilterOption, ...]:
    return (_any(),) + tuple(FilterOption(label, code) for label, code in pairs)


def _ou(
    prefix: str,
    *,
    unders: tuple[str | float, ...] = (),
    overs: tuple[str | float, ...] = (),
    extras: tuple[tuple[str, str], ...] = (),
) -> tuple[FilterOption, ...]:
    """Build Under/Over style options for a Finviz prefix."""
    items: list[tuple[str, str]] = list(extras)
    for u in unders:
        items.append((f"Under {u}", f"{prefix}u{u}"))
    for o in overs:
        items.append((f"Over {o}", f"{prefix}o{o}"))
    return _opts(*items)


def _cr(prefix: str, unit: str = "", **kwargs) -> CustomRangeSpec:
    return CustomRangeSpec(kind="range", prefix=prefix, unit=unit, **kwargs)


def _hl(prefix: str) -> CustomRangeSpec:
    return CustomRangeSpec(
        kind="highlow",
        prefix=prefix,
        unit="%",
        modes=(("Below High", "bhx"), ("Above Low", "alx")),
    )


def _attach_customs(
    fields: tuple[FilterField, ...],
    specs: dict[str, CustomRangeSpec],
) -> tuple[FilterField, ...]:
    """Append Custom… and attach CustomRangeSpec for Elite custom ranges."""
    out: list[FilterField] = []
    for f in fields:
        spec = specs.get(f.id)
        if spec is None:
            out.append(f)
            continue
        opts = []
        saw_custom = False
        for o in f.options:
            if o.code in (CUSTOM_SENTINEL, "__custom_perf__", "__custom_perf2__"):
                if not saw_custom:
                    opts.append(FilterOption("Custom…", CUSTOM_SENTINEL))
                    saw_custom = True
                continue
            opts.append(o)
        if not saw_custom:
            opts.append(FilterOption("Custom…", CUSTOM_SENTINEL))
        out.append(FilterField(f.id, f.label, f.category, tuple(opts), spec))
    return tuple(out)


# ---------------------------------------------------------------------------
# Signal (uses screener ``s=`` param, not ``f=``)
# ---------------------------------------------------------------------------

# Elite intraday / session suffixes for Top Gainers & Top Losers (s=ta_topgainers_5m).
SIGNAL_TIMEFRAMES: tuple[tuple[str, str], ...] = (
    ("1M", "1m"),
    ("2M", "2m"),
    ("3M", "3m"),
    ("5M", "5m"),
    ("10M", "10m"),
    ("15M", "15m"),
    ("30M", "30m"),
    ("1H", "1h"),
    ("2H", "2h"),
    ("4H", "4h"),
    ("AH", "ah"),
)


def _mover_signals(label: str, base_code: str) -> tuple[tuple[str, str], ...]:
    """Base mover signal plus Elite timeframe variants (1M … AH)."""
    items: list[tuple[str, str]] = [(label, base_code)]
    for tf_label, tf_code in SIGNAL_TIMEFRAMES:
        items.append((f"{label} {tf_label}", f"{base_code}_{tf_code}"))
    return tuple(items)


SIGNAL_OPTIONS: tuple[FilterOption, ...] = _opts(
    # Market movers (Top Gainers / Losers include Elite 1M…AH variants)
    *_mover_signals("Top Gainers", "ta_topgainers"),
    *_mover_signals("Top Losers", "ta_toplosers"),
    ("New High", "ta_newhigh"),
    ("New Low", "ta_newlow"),
    ("Most Volatile", "ta_mostvolatile"),
    ("Most Active", "ta_mostactive"),
    ("Most Active AH", "ta_mostactive_ah"),
    ("Unusual Volume", "ta_unusualvolume"),
    ("Unusual Volume AH", "ta_unusualvolume_ah"),
    ("Overbought", "ta_overbought"),
    ("Oversold", "ta_oversold"),
    # News / analysts / insiders
    ("Downgrades", "ta_downgrades"),
    ("Upgrades", "ta_upgrades"),
    ("Earnings Before", "ta_earnbefore"),
    ("Earnings After", "ta_earnafter"),
    ("Recent Insider Buying", "it_latestbuys"),
    ("Recent Insider Selling", "it_latestsales"),
    ("Major News", "n_majornews"),
    # Chart patterns
    ("Horizontal S/R", "ta_p_horizontal"),
    ("TL Resistance", "ta_p_tlresistance"),
    ("TL Support", "ta_p_tlsupport"),
    ("Wedge Up", "ta_p_wedgeup"),
    ("Wedge Down", "ta_p_wedgedown"),
    ("Triangle Ascending", "ta_p_wedgeresistance"),
    ("Triangle Descending", "ta_p_wedgesupport"),
    ("Wedge", "ta_p_wedge"),
    ("Channel Up", "ta_p_channelup"),
    ("Channel Down", "ta_p_channeldown"),
    ("Channel", "ta_p_channel"),
    ("Double Top", "ta_p_doubletop"),
    ("Double Bottom", "ta_p_doublebottom"),
    ("Multiple Top", "ta_p_multipletop"),
    ("Multiple Bottom", "ta_p_multiplebottom"),
    ("Head & Shoulders", "ta_p_headandshoulders"),
    ("Head & Shoulders Inverse", "ta_p_headandshouldersinv"),
)

# ---------------------------------------------------------------------------
# Field catalog (base options; Custom… attached via _attach_customs below)
# ---------------------------------------------------------------------------

_FILTER_FIELDS_BASE: tuple[FilterField, ...] = (
    # ----- Descriptive -----
    FilterField(
        "exchange",
        "Exchange",
        "Descriptive",
        _opts(
            ("AMEX", "exch_amex"),
            ("NASDAQ", "exch_nasd"),
            ("NYSE", "exch_nyse"),
            ("CBOE", "exch_cboe"),
        ),
    ),
    FilterField(
        "index",
        "Index",
        "Descriptive",
        _opts(
            ("S&P 500", "idx_sp500"),
            ("DJIA", "idx_dji"),
            ("NASDAQ 100", "idx_ndx"),
            ("RUSSELL 2000", "idx_rut"),
        ),
    ),
    FilterField(
        "sector",
        "Sector",
        "Descriptive",
        _opts(
            ("Basic Materials", "sec_basicmaterials"),
            ("Communication Services", "sec_communicationservices"),
            ("Consumer Cyclical", "sec_consumercyclical"),
            ("Consumer Defensive", "sec_consumerdefensive"),
            ("Energy", "sec_energy"),
            ("Financial", "sec_financial"),
            ("Healthcare", "sec_healthcare"),
            ("Industrials", "sec_industrials"),
            ("Real Estate", "sec_realestate"),
            ("Technology", "sec_technology"),
            ("Utilities", "sec_utilities"),
        ),
    ),
    FilterField(
        "country",
        "Country",
        "Descriptive",
        _opts(
            ("USA", "geo_usa"),
            ("Foreign (ex-USA)", "geo_notusa"),
            ("Canada", "geo_canada"),
            ("China", "geo_china"),
            ("China & Hong Kong", "geo_chinahongkong"),
            ("Europe", "geo_europe"),
            ("Asia", "geo_asia"),
            ("United Kingdom", "geo_unitedkingdom"),
            ("Japan", "geo_japan"),
            ("India", "geo_india"),
            ("Israel", "geo_israel"),
            ("Australia", "geo_australia"),
            ("South Korea", "geo_southkorea"),
            ("Taiwan", "geo_taiwan"),
            ("Brazil", "geo_brazil"),
            ("Germany", "geo_germany"),
            ("France", "geo_france"),
        ),
    ),
    FilterField(
        "market_cap",
        "Market Cap.",
        "Descriptive",
        _opts(
            ("Mega ($200B+)", "cap_mega"),
            ("Large ($10B to $200B)", "cap_large"),
            ("Mid ($2B to $10B)", "cap_mid"),
            ("Small ($300M to $2B)", "cap_small"),
            ("Micro ($50M to $300M)", "cap_micro"),
            ("Nano (under $50M)", "cap_nano"),
            ("+Large (over $10B)", "cap_largeover"),
            ("+Mid (over $2B)", "cap_midover"),
            ("+Small (over $300M)", "cap_smallover"),
            ("+Micro (over $50M)", "cap_microover"),
            ("-Large (under $200B)", "cap_largeunder"),
            ("-Mid (under $10B)", "cap_midunder"),
            ("-Small (under $2B)", "cap_smallunder"),
            ("-Micro (under $300M)", "cap_microunder"),
        ),
    ),
    FilterField(
        "price",
        "Price $",
        "Descriptive",
        _ou(
            "sh_price_",
            unders=(1, 2, 5, 10, 15, 20, 40, 50, 100),
            overs=(1, 2, 5, 10, 15, 20, 40, 50, 100),
            extras=(
                ("$1 to $5", "sh_price_1to5"),
                ("$5 to $10", "sh_price_5to10"),
                ("$10 to $20", "sh_price_10to20"),
                ("$20 to $50", "sh_price_20to50"),
                ("$50 to $100", "sh_price_50to100"),
            ),
        ),
    ),
    FilterField(
        "avg_volume",
        "Average Volume",
        "Descriptive",
        _opts(
            ("Under 50K", "sh_avgvol_u50"),
            ("Under 100K", "sh_avgvol_u100"),
            ("Under 500K", "sh_avgvol_u500"),
            ("Under 1M", "sh_avgvol_u1000"),
            ("Over 50K", "sh_avgvol_o50"),
            ("Over 100K", "sh_avgvol_o100"),
            ("Over 200K", "sh_avgvol_o200"),
            ("Over 300K", "sh_avgvol_o300"),
            ("Over 400K", "sh_avgvol_o400"),
            ("Over 500K", "sh_avgvol_o500"),
            ("Over 750K", "sh_avgvol_o750"),
            ("Over 1M", "sh_avgvol_o1000"),
            ("Over 2M", "sh_avgvol_o2000"),
            ("100K to 500K", "sh_avgvol_100to500"),
            ("500K to 1M", "sh_avgvol_500to1000"),
        ),
    ),
    FilterField(
        "rel_volume",
        "Relative Volume",
        "Descriptive",
        _ou(
            "sh_relvol_",
            unders=(0.5, 1, 1.5, 2),
            overs=(0.5, 1, 1.5, 2, 3, 4, 5, 10),
        ),
    ),
    FilterField(
        "cur_volume",
        "Current Volume",
        "Descriptive",
        _opts(
            ("Over 50K", "sh_curvol_o50"),
            ("Over 100K", "sh_curvol_o100"),
            ("Over 200K", "sh_curvol_o200"),
            ("Over 500K", "sh_curvol_o500"),
            ("Over 1M", "sh_curvol_o1000"),
            ("Over 2M", "sh_curvol_o2000"),
            ("Over 5M", "sh_curvol_o5000"),
            ("Over 10M", "sh_curvol_o10000"),
        ),
    ),
    FilterField(
        "float",
        "Float",
        "Descriptive",
        _opts(
            ("Under 1M", "sh_float_u1"),
            ("Under 5M", "sh_float_u5"),
            ("Under 10M", "sh_float_u10"),
            ("Under 20M", "sh_float_u20"),
            ("Under 50M", "sh_float_u50"),
            ("Under 100M", "sh_float_u100"),
            ("Over 1M", "sh_float_o1"),
            ("Over 5M", "sh_float_o5"),
            ("Over 10M", "sh_float_o10"),
            ("Over 20M", "sh_float_o20"),
            ("Over 50M", "sh_float_o50"),
            ("Over 100M", "sh_float_o100"),
        ),
    ),
    FilterField(
        "shares_outstanding",
        "Shares Outstanding",
        "Descriptive",
        _opts(
            ("Under 1M", "sh_outstanding_u1"),
            ("Under 5M", "sh_outstanding_u5"),
            ("Under 10M", "sh_outstanding_u10"),
            ("Under 20M", "sh_outstanding_u20"),
            ("Under 50M", "sh_outstanding_u50"),
            ("Under 100M", "sh_outstanding_u100"),
            ("Over 1M", "sh_outstanding_o1"),
            ("Over 5M", "sh_outstanding_o5"),
            ("Over 10M", "sh_outstanding_o10"),
            ("Over 20M", "sh_outstanding_o20"),
            ("Over 50M", "sh_outstanding_o50"),
            ("Over 100M", "sh_outstanding_o100"),
        ),
    ),
    FilterField(
        "short_float",
        "Short Float",
        "Descriptive",
        _ou(
            "sh_short_",
            unders=(5, 10, 15, 20, 25, 30),
            overs=(5, 10, 15, 20, 25, 30),
            extras=(("High (>20%)", "sh_short_high"), ("Low (<5%)", "sh_short_low")),
        ),
    ),
    FilterField(
        "ipo_date",
        "IPO Date",
        "Descriptive",
        _opts(
            ("Today", "ipodate_today"),
            ("Yesterday", "ipodate_yesterday"),
            ("In the last week", "ipodate_prevweek"),
            ("In the last month", "ipodate_prevmonth"),
            ("In the last quarter", "ipodate_prevquarter"),
            ("In the last year", "ipodate_prevyear"),
            ("In the last 2 years", "ipodate_prev2yrs"),
            ("In the last 3 years", "ipodate_prev3yrs"),
            ("In the last 5 years", "ipodate_prev5yrs"),
            ("More than a year ago", "ipodate_more1"),
            ("More than 5 years ago", "ipodate_more5"),
            ("More than 10 years ago", "ipodate_more10"),
            ("More than 15 years ago", "ipodate_more15"),
            ("More than 20 years ago", "ipodate_more20"),
            ("More than 25 years ago", "ipodate_more25"),
        ),
    ),
    FilterField(
        "earnings_date",
        "Earnings Date",
        "Descriptive",
        _opts(
            ("Today", "earningsdate_today"),
            ("Today Before Market Open", "earningsdate_todaybefore"),
            ("Today After Market Close", "earningsdate_todayafter"),
            ("Tomorrow", "earningsdate_tomorrow"),
            ("Tomorrow Before Market Open", "earningsdate_tomorrowbefore"),
            ("Tomorrow After Market Close", "earningsdate_tomorrowafter"),
            ("Yesterday", "earningsdate_yesterday"),
            ("Yesterday Before Market Open", "earningsdate_yesterdaybefore"),
            ("Yesterday After Market Close", "earningsdate_yesterdayafter"),
            ("Next 5 Days", "earningsdate_nextdays5"),
            ("Previous 5 Days", "earningsdate_prevdays5"),
            ("This Week", "earningsdate_thisweek"),
            ("Next Week", "earningsdate_nextweek"),
            ("Previous Week", "earningsdate_prevweek"),
            ("This Month", "earningsdate_thismonth"),
        ),
    ),
    # ----- Fundamental (high-use subset) -----
    FilterField(
        "pe",
        "P/E",
        "Fundamental",
        _ou(
            "fa_pe_",
            unders=(5, 10, 15, 20, 25, 30, 40, 50),
            overs=(5, 10, 15, 20, 25, 30, 40, 50),
            extras=(
                ("Low (<15)", "fa_pe_low"),
                ("Profitable (>0)", "fa_pe_profitable"),
                ("High (>50)", "fa_pe_high"),
            ),
        ),
    ),
    FilterField(
        "forward_pe",
        "Forward P/E",
        "Fundamental",
        _ou(
            "fa_fpe_",
            unders=(5, 10, 15, 20, 25, 30, 40, 50),
            overs=(5, 10, 15, 20, 25, 30, 40, 50),
            extras=(
                ("Low (<15)", "fa_fpe_low"),
                ("Profitable (>0)", "fa_fpe_profitable"),
                ("High (>50)", "fa_fpe_high"),
            ),
        ),
    ),
    FilterField(
        "peg",
        "PEG",
        "Fundamental",
        _ou(
            "fa_peg_",
            unders=(1, 2, 3),
            overs=(1, 2, 3),
            extras=(("Low (<1)", "fa_peg_low"), ("High (>2)", "fa_peg_high")),
        ),
    ),
    FilterField(
        "ps",
        "P/S",
        "Fundamental",
        _ou(
            "fa_ps_",
            unders=(1, 2, 3, 4, 5, 10),
            overs=(1, 2, 3, 4, 5, 10),
            extras=(("Low (<1)", "fa_ps_low"), ("High (>10)", "fa_ps_high")),
        ),
    ),
    FilterField(
        "pb",
        "P/B",
        "Fundamental",
        _ou(
            "fa_pb_",
            unders=(1, 2, 3, 4, 5, 10),
            overs=(1, 2, 3, 4, 5, 10),
            extras=(("Low (<1)", "fa_pb_low"), ("High (>5)", "fa_pb_high")),
        ),
    ),
    FilterField(
        "pc",
        "Price/Cash",
        "Fundamental",
        _ou(
            "fa_pc_",
            unders=(1, 2, 3, 5, 10),
            overs=(1, 2, 3, 5, 10),
            extras=(("Low (<3)", "fa_pc_low"), ("High (>50)", "fa_pc_high")),
        ),
    ),
    FilterField(
        "pfcf",
        "Price/Free Cash Flow",
        "Fundamental",
        _ou(
            "fa_pfcf_",
            unders=(5, 10, 15, 20, 25, 30, 40, 50),
            overs=(5, 10, 15, 20, 25, 30, 40, 50),
            extras=(("Low (<15)", "fa_pfcf_low"), ("High (>50)", "fa_pfcf_high")),
        ),
    ),
    FilterField(
        "evebitda",
        "EV/EBITDA",
        "Fundamental",
        _ou(
            "fa_evebitda_",
            unders=(5, 10, 15, 20, 25, 30, 40, 50),
            overs=(5, 10, 15, 20, 25, 30, 40, 50),
            extras=(
                ("Negative (<0)", "fa_evebitda_negative"),
                ("Low (<15)", "fa_evebitda_low"),
                ("High (>50)", "fa_evebitda_high"),
            ),
        ),
    ),
    FilterField(
        "div_yield",
        "Dividend Yield",
        "Fundamental",
        _ou(
            "fa_div_",
            unders=(1, 2, 3, 4, 5, 6, 8, 10),
            overs=(1, 2, 3, 4, 5, 6, 8, 10),
            extras=(
                ("None (0%)", "fa_div_none"),
                ("Positive (>0%)", "fa_div_pos"),
                ("High (>5%)", "fa_div_high"),
                ("Very High (>10%)", "fa_div_veryhigh"),
            ),
        ),
    ),
    FilterField(
        "eps_q_oq",
        "EPS Growth Qtr Over Qtr",
        "Fundamental",
        _ou(
            "fa_epsqoq_",
            unders=(5, 10, 15, 20, 25, 30),
            overs=(5, 10, 15, 20, 25, 30),
            extras=(
                ("Negative (<0%)", "fa_epsqoq_neg"),
                ("Positive (>0%)", "fa_epsqoq_pos"),
                ("High (>25%)", "fa_epsqoq_high"),
            ),
        ),
    ),
    FilterField(
        "sales_q_oq",
        "Sales Growth Qtr Over Qtr",
        "Fundamental",
        _ou(
            "fa_salesqoq_",
            unders=(5, 10, 15, 20, 25, 30),
            overs=(5, 10, 15, 20, 25, 30),
            extras=(
                ("Negative (<0%)", "fa_salesqoq_neg"),
                ("Positive (>0%)", "fa_salesqoq_pos"),
                ("High (>25%)", "fa_salesqoq_high"),
            ),
        ),
    ),
    FilterField(
        "eps_this_y",
        "EPS Growth This Year",
        "Fundamental",
        _ou(
            "fa_epsyoy_",
            unders=(5, 10, 15, 20, 25, 30),
            overs=(5, 10, 15, 20, 25, 30),
            extras=(
                ("Negative (<0%)", "fa_epsyoy_neg"),
                ("Positive (>0%)", "fa_epsyoy_pos"),
                ("High (>25%)", "fa_epsyoy_high"),
            ),
        ),
    ),
    FilterField(
        "roe",
        "Return on Equity",
        "Fundamental",
        _ou(
            "fa_roe_",
            unders=(5, 10, 15, 20, 25, 30),
            overs=(5, 10, 15, 20, 25, 30),
            extras=(
                ("Positive (>0%)", "fa_roe_pos"),
                ("Negative (<0%)", "fa_roe_neg"),
                ("Very Positive (>30%)", "fa_roe_verypos"),
                ("Very Negative (<-15%)", "fa_roe_veryneg"),
            ),
        ),
    ),
    FilterField(
        "roa",
        "Return on Assets",
        "Fundamental",
        _ou(
            "fa_roa_",
            unders=(5, 10, 15, 20, 25),
            overs=(5, 10, 15, 20, 25),
            extras=(
                ("Positive (>0%)", "fa_roa_pos"),
                ("Negative (<0%)", "fa_roa_neg"),
                ("Very Positive (>15%)", "fa_roa_verypos"),
            ),
        ),
    ),
    FilterField(
        "debt_eq",
        "Debt/Equity",
        "Fundamental",
        _ou(
            "fa_debteq_",
            unders=(0.1, 0.2, 0.3, 0.4, 0.5, 1),
            overs=(0.1, 0.2, 0.3, 0.4, 0.5, 1),
            extras=(("High (>0.5)", "fa_debteq_high"), ("Low (<0.1)", "fa_debteq_low")),
        ),
    ),
    FilterField(
        "gross_margin",
        "Gross Margin",
        "Fundamental",
        _ou(
            "fa_grossmargin_",
            unders=(10, 20, 30, 40, 50, 60),
            overs=(10, 20, 30, 40, 50, 60),
            extras=(
                ("Positive (>0%)", "fa_grossmargin_pos"),
                ("Negative (<0%)", "fa_grossmargin_neg"),
                ("High (>50%)", "fa_grossmargin_high"),
            ),
        ),
    ),
    FilterField(
        "oper_margin",
        "Operating Margin",
        "Fundamental",
        _ou(
            "fa_opermargin_",
            unders=(5, 10, 15, 20, 25, 30),
            overs=(5, 10, 15, 20, 25, 30),
            extras=(
                ("Positive (>0%)", "fa_opermargin_pos"),
                ("Negative (<0%)", "fa_opermargin_neg"),
                ("High (>25%)", "fa_opermargin_high"),
            ),
        ),
    ),
    FilterField(
        "net_margin",
        "Net Profit Margin",
        "Fundamental",
        _ou(
            "fa_netmargin_",
            unders=(5, 10, 15, 20, 25),
            overs=(5, 10, 15, 20, 25),
            extras=(
                ("Positive (>0%)", "fa_netmargin_pos"),
                ("Negative (<0%)", "fa_netmargin_neg"),
                ("High (>20%)", "fa_netmargin_high"),
            ),
        ),
    ),
    FilterField(
        "inst_own",
        "Institutional Ownership",
        "Fundamental",
        _ou(
            "sh_instown_",
            unders=(10, 20, 30, 40, 50, 60, 70, 80, 90),
            overs=(10, 20, 30, 40, 50, 60, 70, 80, 90),
        ),
    ),
    FilterField(
        "insider_own",
        "Insider Ownership",
        "Fundamental",
        _ou(
            "sh_insiderown_",
            unders=(5, 10, 15, 20, 25, 30, 40, 50),
            overs=(5, 10, 15, 20, 25, 30, 40, 50),
            extras=(("Very High (>30%)", "sh_insiderown_veryhigh"),),
        ),
    ),
    FilterField(
        "analyst_recom",
        "Analyst Recom.",
        "Fundamental",
        _opts(
            ("Strong Buy", "an_recom_strongbuy"),
            ("Buy or better", "an_recom_buybetter"),
            ("Buy", "an_recom_buy"),
            ("Hold or better", "an_recom_holdbetter"),
            ("Hold", "an_recom_hold"),
            ("Hold or worse", "an_recom_holdworse"),
            ("Sell", "an_recom_sell"),
            ("Sell or worse", "an_recom_sellworse"),
            ("Strong Sell", "an_recom_strongsell"),
        ),
    ),
    # ----- Technical -----
    FilterField(
        "performance",
        "Performance",
        "Technical",
        _opts(
            ("Today Up", "ta_perf_dup"),
            ("Today Down", "ta_perf_ddown"),
            ("Today -15% or more", "ta_perf_d15u"),
            ("Today -10% or more", "ta_perf_d10u"),
            ("Today -5% or more", "ta_perf_d5u"),
            ("Today +5% or more", "ta_perf_d5o"),
            ("Today +10% or more", "ta_perf_d10o"),
            ("Today +15% or more", "ta_perf_d15o"),
            ("Week Up", "ta_perf_1wup"),
            ("Week Down", "ta_perf_1wdown"),
            ("Week -30% or more", "ta_perf_1w30u"),
            ("Week -20% or more", "ta_perf_1w20u"),
            ("Week -10% or more", "ta_perf_1w10u"),
            ("Week +10% or more", "ta_perf_1w10o"),
            ("Week +20% or more", "ta_perf_1w20o"),
            ("Week +30% or more", "ta_perf_1w30o"),
            ("Month Up", "ta_perf_4wup"),
            ("Month Down", "ta_perf_4wdown"),
            ("Month -50% or more", "ta_perf_4w50u"),
            ("Month -30% or more", "ta_perf_4w30u"),
            ("Month -20% or more", "ta_perf_4w20u"),
            ("Month -10% or more", "ta_perf_4w10u"),
            ("Month +10% or more", "ta_perf_4w10o"),
            ("Month +20% or more", "ta_perf_4w20o"),
            ("Month +30% or more", "ta_perf_4w30o"),
            ("Month +50% or more", "ta_perf_4w50o"),
            ("Quarter Up", "ta_perf_13wup"),
            ("Quarter Down", "ta_perf_13wdown"),
            ("Quarter +50% or more", "ta_perf_13w50o"),
            ("Half Up", "ta_perf_26wup"),
            ("Half Down", "ta_perf_26wdown"),
            ("Half +100% or more", "ta_perf_26w100o"),
            ("Year Up", "ta_perf_52wup"),
            ("Year Down", "ta_perf_52wdown"),
            ("Year +100% or more", "ta_perf_52w100o"),
            ("YTD Up", "ta_perf_ytdup"),
            ("YTD Down", "ta_perf_ytddown"),
            ("Custom…", "__custom_perf__"),
        ),
    ),
    FilterField(
        "performance2",
        "Performance 2",
        "Technical",
        _opts(
            ("Today Up", "ta_perf2_dup"),
            ("Today Down", "ta_perf2_ddown"),
            ("Week Up", "ta_perf2_1wup"),
            ("Week Down", "ta_perf2_1wdown"),
            ("Month Up", "ta_perf2_4wup"),
            ("Month Down", "ta_perf2_4wdown"),
            ("Quarter Up", "ta_perf2_13wup"),
            ("Quarter Down", "ta_perf2_13wdown"),
            ("Half Up", "ta_perf2_26wup"),
            ("Half Down", "ta_perf2_26wdown"),
            ("Year Up", "ta_perf2_52wup"),
            ("Year Down", "ta_perf2_52wdown"),
            ("YTD Up", "ta_perf2_ytdup"),
            ("YTD Down", "ta_perf2_ytddown"),
            ("Custom…", "__custom_perf2__"),
        ),
    ),
    FilterField(
        "volatility",
        "Volatility",
        "Technical",
        _opts(
            ("Week - Over 3%", "ta_volatility_wo3"),
            ("Week - Over 4%", "ta_volatility_wo4"),
            ("Week - Over 5%", "ta_volatility_wo5"),
            ("Week - Over 7%", "ta_volatility_wo7"),
            ("Week - Over 10%", "ta_volatility_wo10"),
            ("Week - Over 15%", "ta_volatility_wo15"),
            ("Month - Over 2%", "ta_volatility_mo2"),
            ("Month - Over 3%", "ta_volatility_mo3"),
            ("Month - Over 4%", "ta_volatility_mo4"),
            ("Month - Over 5%", "ta_volatility_mo5"),
            ("Month - Over 7%", "ta_volatility_mo7"),
            ("Month - Over 10%", "ta_volatility_mo10"),
            ("Month - Over 15%", "ta_volatility_mo15"),
        ),
    ),
    FilterField(
        "rsi",
        "RSI (14)",
        "Technical",
        _ou(
            "ta_rsi_",
            unders=(10, 20, 30, 40, 50, 60, 70, 80, 90),
            overs=(10, 20, 30, 40, 50, 60, 70, 80, 90),
            extras=(
                ("Overbought (90)", "ta_rsi_ob90"),
                ("Overbought (80)", "ta_rsi_ob80"),
                ("Overbought (70)", "ta_rsi_ob70"),
                ("Overbought (60)", "ta_rsi_ob60"),
                ("Oversold (40)", "ta_rsi_os40"),
                ("Oversold (30)", "ta_rsi_os30"),
                ("Oversold (20)", "ta_rsi_os20"),
                ("Oversold (10)", "ta_rsi_os10"),
                ("Not Overbought (<60)", "ta_rsi_nob60"),
                ("Not Oversold (>40)", "ta_rsi_nos40"),
            ),
        ),
    ),
    FilterField(
        "gap",
        "Gap",
        "Technical",
        _opts(
            ("Up", "ta_gap_u"),
            ("Up 0%", "ta_gap_u0"),
            ("Up 1%", "ta_gap_u1"),
            ("Up 2%", "ta_gap_u2"),
            ("Up 3%", "ta_gap_u3"),
            ("Up 4%", "ta_gap_u4"),
            ("Up 5%", "ta_gap_u5"),
            ("Up 6%", "ta_gap_u6"),
            ("Up 7%", "ta_gap_u7"),
            ("Up 8%", "ta_gap_u8"),
            ("Up 9%", "ta_gap_u9"),
            ("Up 10%", "ta_gap_u10"),
            ("Up 15%", "ta_gap_u15"),
            ("Up 20%", "ta_gap_u20"),
            ("Down", "ta_gap_d"),
            ("Down 0%", "ta_gap_d0"),
            ("Down 1%", "ta_gap_d1"),
            ("Down 2%", "ta_gap_d2"),
            ("Down 3%", "ta_gap_d3"),
            ("Down 4%", "ta_gap_d4"),
            ("Down 5%", "ta_gap_d5"),
            ("Down 10%", "ta_gap_d10"),
            ("Down 15%", "ta_gap_d15"),
            ("Down 20%", "ta_gap_d20"),
        ),
    ),
    FilterField(
        "sma20",
        "20-Day Simple Moving Average",
        "Technical",
        _opts(
            ("Price below SMA20", "ta_sma20_pb"),
            ("Price 10% below SMA20", "ta_sma20_pb10"),
            ("Price 20% below SMA20", "ta_sma20_pb20"),
            ("Price 30% below SMA20", "ta_sma20_pb30"),
            ("Price 40% below SMA20", "ta_sma20_pb40"),
            ("Price 50% below SMA20", "ta_sma20_pb50"),
            ("Price above SMA20", "ta_sma20_pa"),
            ("Price 10% above SMA20", "ta_sma20_pa10"),
            ("Price 20% above SMA20", "ta_sma20_pa20"),
            ("Price 30% above SMA20", "ta_sma20_pa30"),
            ("Price 40% above SMA20", "ta_sma20_pa40"),
            ("Price 50% above SMA20", "ta_sma20_pa50"),
            ("SMA20 crossed SMA50", "ta_sma20_cross50"),
            ("SMA20 crossed SMA200", "ta_sma20_cross200"),
            ("SMA20 crossed SMA50 above", "ta_sma20_cross50a"),
            ("SMA20 crossed SMA50 below", "ta_sma20_cross50b"),
            ("SMA20 crossed SMA200 above", "ta_sma20_cross200a"),
            ("SMA20 crossed SMA200 below", "ta_sma20_cross200b"),
        ),
    ),
    FilterField(
        "sma50",
        "50-Day Simple Moving Average",
        "Technical",
        _opts(
            ("Price below SMA50", "ta_sma50_pb"),
            ("Price 10% below SMA50", "ta_sma50_pb10"),
            ("Price 20% below SMA50", "ta_sma50_pb20"),
            ("Price 30% below SMA50", "ta_sma50_pb30"),
            ("Price 40% below SMA50", "ta_sma50_pb40"),
            ("Price 50% below SMA50", "ta_sma50_pb50"),
            ("Price above SMA50", "ta_sma50_pa"),
            ("Price 10% above SMA50", "ta_sma50_pa10"),
            ("Price 20% above SMA50", "ta_sma50_pa20"),
            ("Price 30% above SMA50", "ta_sma50_pa30"),
            ("Price 40% above SMA50", "ta_sma50_pa40"),
            ("Price 50% above SMA50", "ta_sma50_pa50"),
            ("SMA50 crossed SMA20", "ta_sma50_cross20"),
            ("SMA50 crossed SMA200", "ta_sma50_cross200"),
            ("SMA50 crossed SMA20 above", "ta_sma50_cross20a"),
            ("SMA50 crossed SMA20 below", "ta_sma50_cross20b"),
            ("SMA50 crossed SMA200 above", "ta_sma50_cross200a"),
            ("SMA50 crossed SMA200 below", "ta_sma50_cross200b"),
        ),
    ),
    FilterField(
        "sma200",
        "200-Day Simple Moving Average",
        "Technical",
        _opts(
            ("Price below SMA200", "ta_sma200_pb"),
            ("Price 10% below SMA200", "ta_sma200_pb10"),
            ("Price 20% below SMA200", "ta_sma200_pb20"),
            ("Price 30% below SMA200", "ta_sma200_pb30"),
            ("Price 40% below SMA200", "ta_sma200_pb40"),
            ("Price 50% below SMA200", "ta_sma200_pb50"),
            ("Price above SMA200", "ta_sma200_pa"),
            ("Price 10% above SMA200", "ta_sma200_pa10"),
            ("Price 20% above SMA200", "ta_sma200_pa20"),
            ("Price 30% above SMA200", "ta_sma200_pa30"),
            ("Price 40% above SMA200", "ta_sma200_pa40"),
            ("Price 50% above SMA200", "ta_sma200_pa50"),
            ("SMA200 crossed SMA20", "ta_sma200_cross20"),
            ("SMA200 crossed SMA50", "ta_sma200_cross50"),
            ("SMA200 crossed SMA20 above", "ta_sma200_cross20a"),
            ("SMA200 crossed SMA20 below", "ta_sma200_cross20b"),
            ("SMA200 crossed SMA50 above", "ta_sma200_cross50a"),
            ("SMA200 crossed SMA50 below", "ta_sma200_cross50b"),
        ),
    ),
    FilterField(
        "highlow52w",
        "52-Week High/Low",
        "Technical",
        _opts(
            ("New High", "ta_highlow52w_nh"),
            ("New Low", "ta_highlow52w_nl"),
            ("0-3% below High", "ta_highlow52w_b0to3h"),
            ("0-5% below High", "ta_highlow52w_b0to5h"),
            ("0-10% below High", "ta_highlow52w_b0to10h"),
            ("5% or more below High", "ta_highlow52w_b5h"),
            ("10% or more below High", "ta_highlow52w_b10h"),
            ("15% or more below High", "ta_highlow52w_b15h"),
            ("20% or more below High", "ta_highlow52w_b20h"),
            ("30% or more below High", "ta_highlow52w_b30h"),
            ("40% or more below High", "ta_highlow52w_b40h"),
            ("50% or more below High", "ta_highlow52w_b50h"),
            ("0-3% above Low", "ta_highlow52w_a0to3h"),
            ("0-5% above Low", "ta_highlow52w_a0to5h"),
            ("0-10% above Low", "ta_highlow52w_a0to10h"),
            ("5% or more above Low", "ta_highlow52w_a5h"),
            ("10% or more above Low", "ta_highlow52w_a10h"),
            ("15% or more above Low", "ta_highlow52w_a15h"),
            ("20% or more above Low", "ta_highlow52w_a20h"),
            ("30% or more above Low", "ta_highlow52w_a30h"),
            ("40% or more above Low", "ta_highlow52w_a40h"),
            ("50% or more above Low", "ta_highlow52w_a50h"),
        ),
    ),
    FilterField(
        "highlow20d",
        "20-Day High/Low",
        "Technical",
        _opts(
            ("New High", "ta_highlow20d_nh"),
            ("New Low", "ta_highlow20d_nl"),
            ("0-3% below High", "ta_highlow20d_b0to3h"),
            ("0-5% below High", "ta_highlow20d_b0to5h"),
            ("0-10% below High", "ta_highlow20d_b0to10h"),
            ("5% or more below High", "ta_highlow20d_b5h"),
            ("10% or more below High", "ta_highlow20d_b10h"),
            ("0-3% above Low", "ta_highlow20d_a0to3h"),
            ("0-5% above Low", "ta_highlow20d_a0to5h"),
            ("0-10% above Low", "ta_highlow20d_a0to10h"),
            ("5% or more above Low", "ta_highlow20d_a5h"),
            ("10% or more above Low", "ta_highlow20d_a10h"),
        ),
    ),
    FilterField(
        "highlow50d",
        "50-Day High/Low",
        "Technical",
        _opts(
            ("New High", "ta_highlow50d_nh"),
            ("New Low", "ta_highlow50d_nl"),
            ("0-3% below High", "ta_highlow50d_b0to3h"),
            ("0-5% below High", "ta_highlow50d_b0to5h"),
            ("0-10% below High", "ta_highlow50d_b0to10h"),
            ("5% or more below High", "ta_highlow50d_b5h"),
            ("10% or more below High", "ta_highlow50d_b10h"),
            ("0-3% above Low", "ta_highlow50d_a0to3h"),
            ("0-5% above Low", "ta_highlow50d_a0to5h"),
            ("0-10% above Low", "ta_highlow50d_a0to10h"),
            ("5% or more above Low", "ta_highlow50d_a5h"),
            ("10% or more above Low", "ta_highlow50d_a10h"),
        ),
    ),
    FilterField(
        "alltime",
        "All-Time High/Low",
        "Technical",
        _opts(
            ("New High", "ta_alltime_nh"),
            ("New Low", "ta_alltime_nl"),
            ("0-3% below High", "ta_alltime_b0to3h"),
            ("0-5% below High", "ta_alltime_b0to5h"),
            ("0-10% below High", "ta_alltime_b0to10h"),
            ("5% or more below High", "ta_alltime_b5h"),
            ("10% or more below High", "ta_alltime_b10h"),
            ("20% or more below High", "ta_alltime_b20h"),
            ("30% or more below High", "ta_alltime_b30h"),
            ("50% or more below High", "ta_alltime_b50h"),
            ("0-3% above Low", "ta_alltime_a0to3h"),
            ("0-5% above Low", "ta_alltime_a0to5h"),
            ("0-10% above Low", "ta_alltime_a0to10h"),
            ("5% or more above Low", "ta_alltime_a5h"),
            ("10% or more above Low", "ta_alltime_a10h"),
            ("20% or more above Low", "ta_alltime_a20h"),
            ("50% or more above Low", "ta_alltime_a50h"),
        ),
    ),
    FilterField(
        "atr",
        "Average True Range",
        "Technical",
        _ou(
            "ta_averagetruerange_",
            unders=(0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5),
            overs=(0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5),
        ),
    ),
    FilterField(
        "change",
        "Change",
        "Technical",
        _opts(
            ("Up", "ta_change_u"),
            ("Up 1%", "ta_change_u1"),
            ("Up 2%", "ta_change_u2"),
            ("Up 3%", "ta_change_u3"),
            ("Up 4%", "ta_change_u4"),
            ("Up 5%", "ta_change_u5"),
            ("Up 6%", "ta_change_u6"),
            ("Up 7%", "ta_change_u7"),
            ("Up 8%", "ta_change_u8"),
            ("Up 9%", "ta_change_u9"),
            ("Up 10%", "ta_change_u10"),
            ("Up 15%", "ta_change_u15"),
            ("Up 20%", "ta_change_u20"),
            ("Down", "ta_change_d"),
            ("Down 1%", "ta_change_d1"),
            ("Down 2%", "ta_change_d2"),
            ("Down 3%", "ta_change_d3"),
            ("Down 4%", "ta_change_d4"),
            ("Down 5%", "ta_change_d5"),
            ("Down 10%", "ta_change_d10"),
            ("Down 15%", "ta_change_d15"),
            ("Down 20%", "ta_change_d20"),
        ),
    ),
    FilterField(
        "change_open",
        "Change from Open",
        "Technical",
        _opts(
            ("Up", "ta_changeopen_u"),
            ("Up 1%", "ta_changeopen_u1"),
            ("Up 2%", "ta_changeopen_u2"),
            ("Up 3%", "ta_changeopen_u3"),
            ("Up 4%", "ta_changeopen_u4"),
            ("Up 5%", "ta_changeopen_u5"),
            ("Up 10%", "ta_changeopen_u10"),
            ("Down", "ta_changeopen_d"),
            ("Down 1%", "ta_changeopen_d1"),
            ("Down 2%", "ta_changeopen_d2"),
            ("Down 3%", "ta_changeopen_d3"),
            ("Down 4%", "ta_changeopen_d4"),
            ("Down 5%", "ta_changeopen_d5"),
            ("Down 10%", "ta_changeopen_d10"),
        ),
    ),
    FilterField(
        "beta",
        "Beta",
        "Technical",
        _ou(
            "ta_beta_",
            unders=(0, 0.5, 1, 1.5, 2),
            overs=(0, 0.5, 1, 1.5, 2, 2.5, 3),
            extras=(("0 < Beta < 1", "ta_beta_0to1"), ("1 < Beta < 1.5", "ta_beta_1to1.5"), ("1.5 < Beta < 2", "ta_beta_1.5to2")),
        ),
    ),
    FilterField(
        "pattern",
        "Pattern",
        "Technical",
        _opts(
            ("Horizontal S/R", "ta_pattern_horizontal"),
            ("Horizontal S/R (Strong)", "ta_pattern_horizontal2"),
            ("TL Resistance", "ta_pattern_tlresistance"),
            ("TL Resistance (Strong)", "ta_pattern_tlresistance2"),
            ("TL Support", "ta_pattern_tlsupport"),
            ("TL Support (Strong)", "ta_pattern_tlsupport2"),
            ("Wedge Up", "ta_pattern_wedgeup"),
            ("Wedge Up (Strong)", "ta_pattern_wedgeup2"),
            ("Wedge Down", "ta_pattern_wedgedown"),
            ("Wedge Down (Strong)", "ta_pattern_wedgedown2"),
            ("Triangle Ascending", "ta_pattern_wedgeresistance"),
            ("Triangle Descending", "ta_pattern_wedgesupport"),
            ("Channel Up", "ta_pattern_channelup"),
            ("Channel Up (Strong)", "ta_pattern_channelup2"),
            ("Channel Down", "ta_pattern_channeldown"),
            ("Channel Down (Strong)", "ta_pattern_channeldown2"),
            ("Channel", "ta_pattern_channel"),
            ("Channel (Strong)", "ta_pattern_channel2"),
            ("Double Top", "ta_pattern_doubletop"),
            ("Double Bottom", "ta_pattern_doublebottom"),
            ("Multiple Top", "ta_pattern_multipletop"),
            ("Multiple Bottom", "ta_pattern_multiplebottom"),
            ("Head & Shoulders", "ta_pattern_headandshoulders"),
            ("Head & Shoulders Inverse", "ta_pattern_headandshouldersinv"),
        ),
    ),
    FilterField(
        "candlestick",
        "Candlestick",
        "Technical",
        _opts(
            ("Long Lower Shadow", "ta_candlestick_llshadow"),
            ("Long Upper Shadow", "ta_candlestick_lushadow"),
            ("Hammer", "ta_candlestick_hammer"),
            ("Inverted Hammer", "ta_candlestick_ihammer"),
            ("Hanging Man", "ta_candlestick_hangingman"),
            ("Shooting Star", "ta_candlestick_shootingstar"),
            ("Spinning Top / Doji", "ta_candlestick_spinningtop"),
            ("Doji", "ta_candlestick_doji"),
            ("Dragonfly Doji", "ta_candlestick_dragonflydoji"),
            ("Gravestone Doji", "ta_candlestick_gravestonedoji"),
            ("Marubozu White", "ta_candlestick_marubozuwhite"),
            ("Marubozu Black", "ta_candlestick_marubozublack"),
        ),
    ),
    # ----- News -----
    FilterField(
        "latest_news",
        "Latest News",
        "News",
        _opts(
            ("Today", "news_time_t"),
            ("Today or Yesterday", "news_time_r"),
            ("Last Week", "news_time_w"),
            ("Last Month", "news_time_m"),
        ),
    ),
)

CATEGORIES = ("Descriptive", "Fundamental", "Technical", "News")

# Elite Custom… ranges — every Finviz numeric Under/Over-style filter that
# accepts From/To in the website UI.
_CUSTOM_SPECS: dict[str, CustomRangeSpec] = {
    # Descriptive
    "market_cap": _cr("cap_", "$B"),
    "price": _cr("sh_price_", "$"),
    "avg_volume": _cr("sh_avgvol_", "K"),
    "rel_volume": _cr("sh_relvol_", "x"),
    "cur_volume": _cr("sh_curvol_", "K"),
    "float": _cr("sh_float_", "M"),
    "shares_outstanding": _cr("sh_outstanding_", "M"),
    "short_float": _cr("sh_short_", "%"),
    # Fundamental
    "pe": _cr("fa_pe_"),
    "forward_pe": _cr("fa_fpe_"),
    "peg": _cr("fa_peg_"),
    "ps": _cr("fa_ps_"),
    "pb": _cr("fa_pb_"),
    "pc": _cr("fa_pc_"),
    "pfcf": _cr("fa_pfcf_"),
    "evebitda": _cr("fa_evebitda_"),
    "div_yield": _cr("fa_div_", "%"),
    "eps_q_oq": _cr("fa_epsqoq_", "%"),
    "sales_q_oq": _cr("fa_salesqoq_", "%"),
    "eps_this_y": _cr("fa_epsyoy_", "%"),
    "roe": _cr("fa_roe_", "%"),
    "roa": _cr("fa_roa_", "%"),
    "debt_eq": _cr("fa_debteq_"),
    "gross_margin": _cr("fa_grossmargin_", "%"),
    "oper_margin": _cr("fa_opermargin_", "%"),
    "net_margin": _cr("fa_netmargin_", "%"),
    "inst_own": _cr("sh_instown_", "%"),
    "insider_own": _cr("sh_insiderown_", "%"),
    # Technical
    "performance": CustomRangeSpec(kind="perf", prefix="ta_perf", unit="%"),
    "performance2": CustomRangeSpec(kind="perf2", prefix="ta_perf2", unit="%"),
    "rsi": _cr("ta_rsi_"),
    "atr": _cr("ta_averagetruerange_"),
    "beta": _cr("ta_beta_"),
    "highlow52w": _hl("ta_highlow52w_"),
    "highlow20d": _hl("ta_highlow20d_"),
    "highlow50d": _hl("ta_highlow50d_"),
    "alltime": _hl("ta_alltime_"),
    "gap": _cr("ta_gap_", "%"),
    "change": _cr("ta_change_", "%"),
    "change_open": _cr("ta_changeopen_", "%"),
}

FILTER_FIELDS: tuple[FilterField, ...] = _attach_customs(_FILTER_FIELDS_BASE, _CUSTOM_SPECS)

SORT_OPTIONS: tuple[FilterOption, ...] = (
    FilterOption("Change % (desc)", "-change"),
    FilterOption("Change % (asc)", "change"),
    FilterOption("Volume (desc)", "-volume"),
    FilterOption("Volume (asc)", "volume"),
    FilterOption("Price (desc)", "-price"),
    FilterOption("Price (asc)", "price"),
    FilterOption("Relative Volume (desc)", "-relativevolume"),
    FilterOption("Market Cap (desc)", "-marketcap"),
    FilterOption("Ticker", "ticker"),
)


def fields_by_category(category: str) -> tuple[FilterField, ...]:
    return tuple(f for f in FILTER_FIELDS if f.category == category)


def field_by_id(field_id: str) -> FilterField | None:
    for f in FILTER_FIELDS:
        if f.id == field_id:
            return f
    return None
