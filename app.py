import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PH LGU Fiscal Dashboard", layout="wide")

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
ECON_COLORS = px.colors.qualitative.Pastel


@st.cache_data
def load_data():
    df = pd.read_csv("lgu_fiscal_panel.csv", low_memory=False)

    # Build one column per sector for the row's observation year
    for key in SECTORS:
        vals = pd.Series(float("nan"), index=df.index)
        for yr in range(2015, 2024):
            col = f"aa_s_{key}_{yr}"
            if col in df.columns:
                mask = df["year"] == yr
                vals.loc[mask] = df.loc[mask, col]
        df[f"sec_{key}"] = vals.fillna(0)

    # Fill econ columns with 0 where missing
    for col in ECON:
        df[col] = df[col].fillna(0)

    return df


df = load_data()

# ── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")

regions = sorted(df["region"].dropna().unique())
sel_region = st.sidebar.selectbox("Region", ["— All Regions —"] + regions)

if sel_region != "— All Regions —":
    in_region = df[df["region"] == sel_region]
else:
    in_region = df

provinces = sorted(in_region["province"].dropna().unique())
sel_province = st.sidebar.selectbox("Province", ["— All Provinces —"] + provinces)

if sel_province != "— All Provinces —":
    in_province = in_region[in_region["province"] == sel_province]
else:
    in_province = in_region

lgus = sorted(in_province["lgu"].dropna().unique())
sel_lgu = st.sidebar.selectbox("LGU", ["— All in selection —"] + lgus)

st.sidebar.divider()

all_types = sorted(in_province["lgutype_n"].dropna().unique())
sel_types = st.sidebar.multiselect("LGU Type", all_types, default=all_types)

all_years = sorted(df["year"].dropna().unique())
year_range = st.sidebar.select_slider(
    "Year range",
    options=all_years,
    value=(min(all_years), max(all_years)),
)

st.sidebar.divider()

view = st.sidebar.radio("View", ["By Sector", "By Economic Classification"])
show_pct = st.sidebar.toggle("Show as % of total")

# ── Filter ───────────────────────────────────────────────────────────────────
if sel_lgu != "— All in selection —":
    filtered = in_province[in_province["lgu"] == sel_lgu]
else:
    filtered = in_province

if sel_types:
    filtered = filtered[filtered["lgutype_n"].isin(sel_types)]

filtered = filtered[
    (filtered["year"] >= year_range[0]) & (filtered["year"] <= year_range[1])
]

# ── Scope label ──────────────────────────────────────────────────────────────
if sel_lgu != "— All in selection —":
    scope = sel_lgu
elif sel_province != "— All Provinces —":
    scope = f"All LGUs — {sel_province}"
elif sel_region != "— All Regions —":
    scope = f"All LGUs — {sel_region}"
else:
    scope = "All LGUs — National"

# ── Header metrics ───────────────────────────────────────────────────────────
st.title("PH LGU Fiscal Dashboard")
st.subheader(scope)

total_approp = filtered["aa_total"].sum()
n_lgus = filtered["lgu"].nunique()
years_present = sorted(filtered["year"].unique())

c1, c2, c3 = st.columns(3)
c1.metric("Total Appropriations (all years)", f"₱{total_approp:,.0f}")
c2.metric("LGUs in selection", n_lgus)
c3.metric("Years covered", f"{min(years_present)}–{max(years_present)}" if years_present else "—")

# ── Aggregate by year ─────────────────────────────────────────────────────────
if view == "By Sector":
    raw_cols = {f"sec_{k}": v for k, v in SECTORS.items()}
    chart_title = "Appropriations by Sector"
    color_seq = SECTOR_COLORS
else:
    raw_cols = ECON
    chart_title = "Appropriations by Economic Classification"
    color_seq = ECON_COLORS

agg = (
    filtered
    .groupby("year")[list(raw_cols.keys())]
    .sum()
    .reset_index()
    .rename(columns=raw_cols)
)

cat_cols = list(raw_cols.values())

if show_pct:
    row_totals = agg[cat_cols].sum(axis=1).replace(0, float("nan"))
    agg[cat_cols] = agg[cat_cols].div(row_totals, axis=0).mul(100)

# ── Chart ────────────────────────────────────────────────────────────────────
melted = agg.melt(id_vars="year", value_vars=cat_cols, var_name="Category", value_name="Value")
melted["Value"] = melted["Value"].fillna(0)

y_label = "Share of total (%)" if show_pct else "Appropriations (PHP)"

fig = px.bar(
    melted,
    x="year",
    y="Value",
    color="Category",
    barmode="stack",
    title=chart_title,
    labels={"Value": y_label, "year": "Year"},
    color_discrete_sequence=color_seq,
)
fig.update_layout(
    xaxis=dict(tickmode="linear", dtick=1),
    yaxis_tickformat=",.0f" if not show_pct else ".1f",
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01),
    height=480,
)
if show_pct:
    fig.update_yaxes(ticksuffix="%", range=[0, 100])

st.plotly_chart(fig, use_container_width=True)

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("Annual Breakdown")

display = agg.copy()
display["year"] = display["year"].astype(str)
for col in cat_cols:
    if show_pct:
        display[col] = display[col].map(lambda x: f"{x:.1f}%")
    else:
        display[col] = display[col].map(lambda x: f"₱{x:,.0f}")

st.dataframe(display.set_index("year").T, use_container_width=True)

# ── LGU ranking table (only when multiple LGUs in scope) ─────────────────────
if sel_lgu == "— All in selection —" and n_lgus > 1:
    st.subheader(f"LGU Rankings — {year_range[0]}–{year_range[1]}")

    rank_cols = ["lgu", "province", "region", "lgutype_n", "year", "aa_total"]
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
