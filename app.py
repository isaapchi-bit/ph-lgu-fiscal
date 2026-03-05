import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PH LGU Fiscal Dashboard", layout="wide")

st.markdown("""
<style>
/* ── Metric cards ─────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: #ffffff;
    border: none;
    border-radius: 14px;
    padding: 1.4rem 1.6rem !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: #718096 !important;
    font-size: 0.72rem !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #1a202c !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    line-height: 1.2;
}

/* ── Section headings ─────────────────────────────────────────────── */
h2, h3 {
    color: #1a202c !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
}

/* ── Chart card ───────────────────────────────────────────────────── */
.stPlotlyChart {
    background: #ffffff;
    border-radius: 14px;
    padding: 0.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}

/* ── Dataframe card ───────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}

/* ── Sidebar labels ───────────────────────────────────────────────── */
[data-testid="stSidebar"] label p {
    font-size: 0.72rem !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #a0aec0 !important;
}
</style>
""", unsafe_allow_html=True)

SECTORS = {
    "gen_serv":   "General Services",
    "educ":       "Education",
    "health":     "Health",
    "labor":      "Labor & Employment",
    "house":      "Housing & Community Dev.",
    "social":     "Social Services",
    "econ_serv":  "Economic Services",
    "other_purp": "Other Purposes",
    "ldrrmf":     "LDRRMF",
    "devfund":    "Development Fund",
    "others":     "Others",
}

ECON = {
    "aa_ps":               "Personal Services (PS)",
    "aa_capital_outlays":  "Capital Outlays (CO)",
    "aa_mooe":             "MOOE",
    "aa_unc":              "Unclassified",
    "aa_amort":            "Amortization",
    "aa_fin":              "Financial Expenses",
}

SECTOR_COLORS = px.colors.qualitative.Safe
ECON_COLORS   = px.colors.qualitative.Pastel

# Approximate province centroids (lat, lon)
PROVINCE_COORDS = {
    "Abra":                 (17.60, 120.73),
    "Agusan del Norte":     (8.95,  125.53),
    "Agusan del Sur":       (8.16,  126.00),
    "Aklan":                (11.58, 122.37),
    "Albay":                (13.18, 123.53),
    "Antique":              (11.37, 122.00),
    "Apayao":               (18.01, 121.17),
    "Aurora":               (15.97, 121.65),
    "Basilan":              (6.42,  121.97),
    "Bataan":               (14.64, 120.48),
    "Batanes":              (20.45, 121.97),
    "Batangas":             (13.76, 121.06),
    "Benguet":              (16.40, 120.60),
    "Biliran":              (11.58, 124.47),
    "Bohol":                (9.85,  124.17),
    "Bukidnon":             (8.05,  125.10),
    "Bulacan":              (14.80, 120.88),
    "Cagayan":              (17.99, 121.81),
    "Camarines Norte":      (14.14, 122.76),
    "Camarines Sur":        (13.52, 123.35),
    "Camiguin":             (9.18,  124.72),
    "Capiz":                (11.55, 122.74),
    "Catanduanes":          (13.71, 124.24),
    "Cavite":               (14.24, 120.87),
    "Cebu":                 (10.31, 123.89),
    "Cotabato":             (7.21,  124.25),
    "Davao Occidental":     (6.10,  125.61),
    "Davao Oriental":       (7.31,  126.54),
    "Davao de Oro":         (7.31,  126.17),
    "Davao del Norte":      (7.57,  125.65),
    "Davao del Sur":        (6.77,  125.36),
    "Dinagat Islands":      (10.13, 125.60),
    "Eastern Samar":        (11.50, 125.47),
    "Guimaras":             (10.59, 122.63),
    "Ifugao":               (16.83, 121.17),
    "Ilocos Norte":         (18.17, 120.57),
    "Ilocos Sur":           (17.57, 120.39),
    "Iloilo":               (10.75, 122.56),
    "Isabela":              (16.97, 121.81),
    "Kalinga":              (17.47, 121.35),
    "La Union":             (16.61, 120.32),
    "Laguna":               (14.17, 121.42),
    "Lanao del Norte":      (8.07,  124.23),
    "Lanao del Sur":        (7.82,  124.43),
    "Leyte":                (10.86, 124.88),
    "Maguindanao":          (6.94,  124.42),
    "Maguindanao del Norte":(7.19,  124.23),
    "Maguindanao del Sur":  (6.65,  124.45),
    "Marinduque":           (13.48, 121.91),
    "Masbate":              (12.17, 123.62),
    "Misamis Occidental":   (8.34,  123.71),
    "Misamis Oriental":     (8.50,  124.62),
    "Mountain Province":    (17.00, 121.00),
    "Negros Occidental":    (10.67, 123.03),
    "Negros Oriental":      (9.65,  123.01),
    "Northern Samar":       (12.47, 124.67),
    "Nueva Ecija":          (15.57, 121.02),
    "Nueva Vizcaya":        (16.33, 121.17),
    "Occidental Mindoro":   (13.10, 120.77),
    "Oriental Mindoro":     (13.05, 121.44),
    "Palawan":              (9.84,  118.74),
    "Pampanga":             (15.08, 120.67),
    "Pangasinan":           (15.89, 120.29),
    "Quezon":               (14.03, 122.11),
    "Quirino":              (16.27, 121.53),
    "Rizal":                (14.60, 121.31),
    "Romblon":              (12.57, 122.27),
    "Samar":                (11.79, 124.99),
    "Sarangani":            (5.92,  125.17),
    "Siquijor":             (9.20,  123.59),
    "Sorsogon":             (12.97, 124.01),
    "South Cotabato":       (6.27,  124.85),
    "Southern Leyte":       (10.34, 125.17),
    "Sultan Kudarat":       (6.51,  124.42),
    "Sulu":                 (5.97,  121.03),
    "Surigao del Norte":    (9.75,  125.51),
    "Surigao del Sur":      (8.51,  126.12),
    "Tarlac":               (15.48, 120.59),
    "Tawi-Tawi":            (5.13,  119.95),
    "Zambales":             (15.51, 119.97),
    "Zamboanga Sibugay":    (7.52,  122.31),
    "Zamboanga del Norte":  (8.39,  123.16),
    "Zamboanga del Sur":    (7.83,  123.30),
}


@st.cache_data
def load_data():
    df = pd.read_csv("lgu_fiscal_panel.csv", low_memory=False)

    for key in SECTORS:
        vals = pd.Series(float("nan"), index=df.index)
        for yr in range(2015, 2024):
            col = f"aa_s_{key}_{yr}"
            if col in df.columns:
                mask = df["year"] == yr
                vals.loc[mask] = df.loc[mask, col]
        df[f"sec_{key}"] = vals.fillna(0)

    for col in ECON:
        df[col] = df[col].fillna(0)

    return df


df = load_data()

# ── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")

all_regions = sorted(df["region"].dropna().unique())
sel_regions = st.sidebar.multiselect("Region", all_regions)

in_region = df[df["region"].isin(sel_regions)] if sel_regions else df

all_provinces = sorted(in_region["province"].dropna().unique())
sel_provinces = st.sidebar.multiselect("Province", all_provinces)

in_province = in_region[in_region["province"].isin(sel_provinces)] if sel_provinces else in_region

all_lgus = sorted(in_province["lgu"].dropna().unique())
sel_lgus = st.sidebar.multiselect("LGU", all_lgus)

st.sidebar.divider()

all_types = sorted(in_province["lgutype_n"].dropna().unique())
sel_types = st.sidebar.multiselect("LGU Type", all_types)

all_years = sorted(df["year"].dropna().unique())
year_range = st.sidebar.select_slider(
    "Year range",
    options=all_years,
    value=(min(all_years), max(all_years)),
)

st.sidebar.divider()

view     = st.sidebar.radio("View", ["By Sector", "By Economic Classification"])
show_pct = st.sidebar.toggle("Show as % of total")

# ── Filter ───────────────────────────────────────────────────────────────────
filtered = in_province.copy()

if sel_lgus:
    filtered = filtered[filtered["lgu"].isin(sel_lgus)]

if sel_types:
    filtered = filtered[filtered["lgutype_n"].isin(sel_types)]

filtered = filtered[
    (filtered["year"] >= year_range[0]) & (filtered["year"] <= year_range[1])
]

# ── Scope label ──────────────────────────────────────────────────────────────
if sel_lgus:
    scope = ", ".join(sel_lgus) if len(sel_lgus) <= 3 else f"{len(sel_lgus)} LGUs selected"
elif sel_provinces:
    scope = ", ".join(sel_provinces) if len(sel_provinces) <= 3 else f"{len(sel_provinces)} Provinces selected"
elif sel_regions:
    scope = ", ".join(sel_regions) if len(sel_regions) <= 3 else f"{len(sel_regions)} Regions selected"
else:
    scope = "All LGUs — National"

# ── Header ────────────────────────────────────────────────────────────────────
st.title("PH LGU Fiscal Dashboard")
st.subheader(scope)

total_approp  = filtered["aa_total"].sum()
n_lgus        = filtered["lgu"].nunique()
years_present = sorted(filtered["year"].unique())

c1, c2, c3 = st.columns(3)
c1.metric("Total Appropriations (all years)", f"₱{total_approp:,.0f}")
c2.metric("LGUs in selection", n_lgus)
c3.metric("Years covered", f"{min(years_present)}–{max(years_present)}" if years_present else "—")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_overview, tab_map = st.tabs(["Overview", "Map"])

# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ═══════════════════════════════════════════════════════════════════════════════
with tab_overview:

    # ── Aggregate by year ────────────────────────────────────────────────────
    if view == "By Sector":
        raw_cols   = {f"sec_{k}": v for k, v in SECTORS.items()}
        chart_title = "Appropriations by Sector"
        color_seq   = SECTOR_COLORS
    else:
        raw_cols   = ECON
        chart_title = "Appropriations by Economic Classification"
        color_seq   = ECON_COLORS

    agg = (
        filtered
        .groupby("year")[list(raw_cols.keys())]
        .sum()
        .reset_index()
        .rename(columns=raw_cols)
    )

    cat_cols = list(raw_cols.values())

    if show_pct:
        row_totals  = agg[cat_cols].sum(axis=1).replace(0, float("nan"))
        agg[cat_cols] = agg[cat_cols].div(row_totals, axis=0).mul(100)

    # ── Main chart ───────────────────────────────────────────────────────────
    melted          = agg.melt(id_vars="year", value_vars=cat_cols, var_name="Category", value_name="Value")
    melted["Value"] = melted["Value"].fillna(0)
    y_label         = "Share of total (%)" if show_pct else "Appropriations (PHP)"

    fig = px.bar(
        melted,
        x="year", y="Value", color="Category",
        barmode="stack", title=chart_title,
        labels={"Value": y_label, "year": "Year"},
        color_discrete_sequence=color_seq,
    )
    fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1, gridcolor="#edf2f7", color="#718096"),
        yaxis_tickformat=",.0f" if not show_pct else ".1f",
        yaxis=dict(gridcolor="#edf2f7", color="#718096"),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01,
                    bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1,
                    font=dict(color="#2d3748")),
        height=480,
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        font=dict(family="sans-serif", color="#2d3748"),
        title_font=dict(size=15, color="#1a202c"),
        margin=dict(t=50, r=20, b=40, l=60),
    )
    if show_pct:
        fig.update_yaxes(ticksuffix="%", range=[0, 100])

    st.plotly_chart(fig, use_container_width=True)

    # ── % Share Breakdown ────────────────────────────────────────────────────
    st.subheader("% Share Breakdown")

    pct_agg = agg.copy()
    if not show_pct:
        row_totals        = pct_agg[cat_cols].sum(axis=1).replace(0, float("nan"))
        pct_agg[cat_cols] = pct_agg[cat_cols].div(row_totals, axis=0).mul(100)

    pct_melted        = pct_agg.melt(id_vars="year", value_vars=cat_cols, var_name="Category", value_name="Pct")
    pct_melted["Pct"] = pct_melted["Pct"].fillna(0)

    col_bar, col_donut = st.columns([3, 2])

    with col_bar:
        fig_pct = px.bar(
            pct_melted,
            x="year", y="Pct", color="Category",
            barmode="stack", title="100% Stacked — Share per Year",
            labels={"Pct": "Share (%)", "year": "Year"},
            color_discrete_sequence=color_seq,
        )
        fig_pct.update_layout(
            xaxis=dict(tickmode="linear", dtick=1, gridcolor="#edf2f7", color="#718096"),
            yaxis=dict(gridcolor="#edf2f7", color="#718096", range=[0, 100]),
            yaxis_tickformat=".1f",
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01,
                        bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1,
                        font=dict(color="#2d3748")),
            height=380,
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(family="sans-serif", color="#2d3748"),
            title_font=dict(size=14, color="#1a202c"),
            margin=dict(t=50, r=20, b=40, l=60),
        )
        fig_pct.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig_pct, use_container_width=True)

    with col_donut:
        donut_vals = pct_agg[cat_cols].mean()
        fig_donut  = px.pie(
            names=donut_vals.index, values=donut_vals.values,
            hole=0.45, title=f"Avg Share — {year_range[0]}–{year_range[1]}",
            color_discrete_sequence=color_seq,
        )
        fig_donut.update_traces(
            textposition="inside", textinfo="percent",
            hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        )
        fig_donut.update_layout(
            height=380, paper_bgcolor="#ffffff",
            font=dict(family="sans-serif", color="#2d3748"),
            title_font=dict(size=14, color="#1a202c"),
            legend=dict(orientation="v", yanchor="middle", y=0.5,
                        font=dict(size=10, color="#2d3748")),
            margin=dict(t=50, r=10, b=10, l=10),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # ── Annual breakdown table ────────────────────────────────────────────────
    st.subheader("Annual Breakdown")

    display = agg.copy()
    display["year"] = display["year"].astype(str)
    for col in cat_cols:
        if show_pct:
            display[col] = display[col].map(lambda x: f"{x:.1f}%")
        else:
            display[col] = display[col].map(lambda x: f"₱{x:,.0f}")

    st.dataframe(display.set_index("year").T, use_container_width=True)

    # ── LGU ranking table ─────────────────────────────────────────────────────
    if n_lgus > 1:
        st.subheader(f"LGU Rankings — {year_range[0]}–{year_range[1]}")

        rank_cols = ["lgu", "province", "region", "lgutype_n", "aa_total"]
        rank = (
            filtered[rank_cols]
            .dropna(subset=["aa_total"])
            .groupby(["lgu", "province", "region", "lgutype_n"], as_index=False)["aa_total"]
            .sum()
            .sort_values("aa_total", ascending=False)
            .reset_index(drop=True)
        )
        rank.index += 1
        rank["aa_total"] = rank["aa_total"].map(lambda x: f"₱{x:,.0f}")
        rank.columns = ["LGU", "Province", "Region", "Type", "Total Appropriations"]
        st.dataframe(rank, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAP TAB
# ═══════════════════════════════════════════════════════════════════════════════
with tab_map:
    st.subheader("Provincial Map — Total Appropriations")

    map_col, ctrl_col = st.columns([4, 1])

    with ctrl_col:
        map_metric = st.radio(
            "Metric",
            ["Total Appropriations", "Per-LGU Average", "% Share of National"],
            key="map_metric",
        )
        map_year_all = st.checkbox("All years in range", value=True, key="map_year_all")
        if not map_year_all:
            map_year = st.selectbox("Year", sorted(filtered["year"].unique()), key="map_year")
        color_by = st.radio("Color by", ["Province", "Region"], key="map_color_by")

    # Build province-level aggregation
    map_data = filtered.copy()
    if not map_year_all and "map_year" in st.session_state:
        map_data = map_data[map_data["year"] == st.session_state["map_year"]]

    prov_agg = (
        map_data
        .groupby(["province", "region"], as_index=False)
        .agg(total=("aa_total", "sum"), lgu_count=("lgu", "nunique"))
    )
    prov_agg["avg_per_lgu"]  = prov_agg["total"] / prov_agg["lgu_count"]
    national_total           = prov_agg["total"].sum()
    prov_agg["pct_national"] = prov_agg["total"] / national_total * 100

    # Attach coordinates
    prov_agg["lat"] = prov_agg["province"].map(lambda p: PROVINCE_COORDS.get(p, (None, None))[0])
    prov_agg["lon"] = prov_agg["province"].map(lambda p: PROVINCE_COORDS.get(p, (None, None))[1])
    prov_agg = prov_agg.dropna(subset=["lat", "lon"])

    metric_col_map = {
        "Total Appropriations":  "total",
        "Per-LGU Average":       "avg_per_lgu",
        "% Share of National":   "pct_national",
    }
    size_col  = metric_col_map[map_metric]
    color_col = "province" if color_by == "Province" else "region"

    # Format hover labels
    prov_agg["label_total"]    = prov_agg["total"].map(lambda x: f"₱{x:,.0f}")
    prov_agg["label_avg"]      = prov_agg["avg_per_lgu"].map(lambda x: f"₱{x:,.0f}")
    prov_agg["label_pct"]      = prov_agg["pct_national"].map(lambda x: f"{x:.2f}%")
    prov_agg["label_lgus"]     = prov_agg["lgu_count"].map(lambda x: f"{x} LGUs")

    fig_map = px.scatter_mapbox(
        prov_agg,
        lat="lat", lon="lon",
        size=size_col,
        color=color_col,
        hover_name="province",
        hover_data={
            "label_total":  True,
            "label_avg":    True,
            "label_pct":    True,
            "label_lgus":   True,
            "lat":          False,
            "lon":          False,
            size_col:       False,
            color_col:      False,
        },
        labels={
            "label_total": "Total",
            "label_avg":   "Avg/LGU",
            "label_pct":   "% National",
            "label_lgus":  "LGUs",
        },
        size_max=50,
        zoom=5,
        center={"lat": 12.5, "lon": 122.5},
        mapbox_style="carto-positron",
        title="Appropriations by Province",
        color_discrete_sequence=SECTOR_COLORS,
    )
    fig_map.update_layout(
        height=680,
        paper_bgcolor="#ffffff",
        font=dict(family="sans-serif", color="#2d3748"),
        title_font=dict(size=15, color="#1a202c"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1,
            font=dict(color="#2d3748", size=10),
        ),
        margin=dict(t=50, r=10, b=10, l=10),
    )

    with map_col:
        st.plotly_chart(fig_map, use_container_width=True)

    # Province data table
    st.subheader("Province Summary")
    prov_display = prov_agg[["province", "region", "lgu_count", "label_total", "label_avg", "label_pct"]].copy()
    prov_display.columns = ["Province", "Region", "LGUs", "Total Appropriations", "Avg per LGU", "% of National"]
    prov_display = prov_display.sort_values("Total Appropriations", ascending=False).reset_index(drop=True)
    prov_display.index += 1
    st.dataframe(prov_display, use_container_width=True)
