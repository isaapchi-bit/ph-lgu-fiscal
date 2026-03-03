"""
Philippine LGU Fiscal Spending Dashboard  (2016–2023)
=====================================================
Expected CSV columns
--------------------
lgu_name       : str  – name of the LGU
lgu_type       : str  – province | city | municipality
region         : str  – region name / code
year           : int  – 2016–2023
population     : int  – resident population
spend_general_public_services : float  (PHP, total)
spend_education               : float
spend_health                  : float
spend_labor                   : float
spend_housing                 : float
spend_social_welfare          : float
spend_economic_services       : float
spend_debt_service            : float

If lgu_spending.csv is absent, the app generates synthetic sample data
so you can explore the UI immediately.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PH LGU Fiscal Spending Dashboard",
    page_icon="🇵🇭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sector definitions ────────────────────────────────────────────────────────
SECTORS: dict[str, str] = {
    "General Public Services": "spend_general_public_services",
    "Education":               "spend_education",
    "Health":                  "spend_health",
    "Labor & Employment":      "spend_labor",
    "Housing & Community Dev.":"spend_housing",
    "Social Welfare":          "spend_social_welfare",
    "Economic Services":       "spend_economic_services",
    "Debt Service":            "spend_debt_service",
}
PC_COL   = {label: f"pc_{col}" for label, col in SECTORS.items()}
ALL_PCOLS = list(PC_COL.values())

SECTOR_PALETTE = px.colors.qualitative.Plotly   # 10-colour cycle

LGU_COLORS = {
    "province":    "#1f77b4",
    "city":        "#ff7f0e",
    "municipality":"#2ca02c",
}

CSV_PATH = "lgu_spending.csv"


# ── Sample data generator ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Generating sample data …")
def _make_sample() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    regions = [
        "NCR", "CAR", "Ilocos (I)", "Cagayan Valley (II)",
        "Central Luzon (III)", "CALABARZON (IV-A)", "MIMAROPA (IV-B)",
        "Bicol (V)", "W. Visayas (VI)", "C. Visayas (VII)",
        "E. Visayas (VIII)", "Zamboanga (IX)", "N. Mindanao (X)",
        "Davao (XI)", "SOCCSKSARGEN (XII)", "CARAGA", "BARMM",
    ]
    configs = [
        # (lgu_type,      n,    pop_range,               base_pc_range)
        ("province",      81,   (300_000, 2_500_000),    (2_500, 9_000)),
        ("city",         146,   (60_000,   600_000),     (2_000, 7_000)),
        ("municipality", 200,   (5_000,    120_000),     (400,   3_500)),
    ]
    rows = []
    for lgu_type, n, pop_range, pc_range in configs:
        for i in range(n):
            region   = rng.choice(regions)
            base_pop = int(rng.integers(*pop_range))
            base_pc  = float(rng.uniform(*pc_range))           # PHP per capita
            weights  = rng.dirichlet([3.0, 1.5, 1.2, 0.3, 0.5, 1.0, 1.8, 0.7])

            for year in range(2016, 2024):
                pop    = int(base_pop * (1 + 0.015 * (year - 2016)))
                growth = 1 + 0.045 * (year - 2016) + float(rng.uniform(-0.04, 0.04))
                pc_tot = base_pc * growth

                row: dict = {
                    "lgu_name":   f"{lgu_type.capitalize()}-{i+1:03d}",
                    "lgu_type":   lgu_type,
                    "region":     region,
                    "year":       year,
                    "population": pop,
                }
                for (label, col), w in zip(SECTORS.items(), weights):
                    row[col]           = round(pc_tot * w * pop, 2)
                    row[f"pc_{col}"]   = round(pc_tot * w, 4)
                rows.append(row)
    return pd.DataFrame(rows)


# ── Data loader ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading data …")
def load_data() -> tuple[pd.DataFrame, bool]:
    """Return (dataframe, is_sample)."""
    if Path(CSV_PATH).exists():
        df = pd.read_csv(CSV_PATH)
        df["year"] = df["year"].astype(int)
        # Derive per-capita columns if missing
        for label, col in SECTORS.items():
            pc = f"pc_{col}"
            if col in df.columns and pc not in df.columns:
                df[pc] = df[col] / df["population"]
        return df, False
    else:
        return _make_sample(), True


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_php(value: float, decimals: int = 0) -> str:
    """Format a peso value with ₱ prefix and thousands separator."""
    return f"₱{value:,.{decimals}f}"


def build_long(df: pd.DataFrame) -> pd.DataFrame:
    """Melt per-capita columns into long format for multi-sector charts."""
    pc_map = {v: k for k, v in PC_COL.items()}
    long = df.melt(
        id_vars=["lgu_name", "lgu_type", "region", "year", "population"],
        value_vars=ALL_PCOLS,
        var_name="pc_col",
        value_name="per_capita_spend",
    )
    long["sector"] = long["pc_col"].map(pc_map)
    return long.drop(columns="pc_col")


# ─────────────────────────────────────────────────────────────────────────────
#  Main app
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    df_full, is_sample = load_data()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🇵🇭 PH LGU Spending")
        st.caption("Fiscal data 2016–2023")

        if is_sample:
            st.info(
                "Using **synthetic sample data**.\n\n"
                f"Place `{CSV_PATH}` in the working directory to load real data.",
                icon="ℹ️",
            )

        st.divider()

        # LGU type
        all_types = sorted(df_full["lgu_type"].unique())
        sel_types = st.multiselect(
            "LGU Type",
            options=all_types,
            default=all_types,
            help="Filter by administrative classification.",
        )

        # Region
        all_regions = sorted(df_full["region"].unique())
        sel_regions = st.multiselect(
            "Region",
            options=all_regions,
            default=all_regions,
        )

        # Year range
        min_yr, max_yr = int(df_full["year"].min()), int(df_full["year"].max())
        sel_years = st.slider(
            "Year range",
            min_value=min_yr,
            max_value=max_yr,
            value=(min_yr, max_yr),
            step=1,
        )

        # Sector picker (for drill-down charts)
        st.divider()
        sel_sector = st.selectbox(
            "Focus sector (detail charts)",
            options=list(SECTORS.keys()),
            index=1,
        )

        # Aggregation
        agg_fn = st.radio(
            "Aggregation",
            ["Mean", "Median"],
            horizontal=True,
            help="Statistic used when averaging across LGUs.",
        )
        agg = "mean" if agg_fn == "Mean" else "median"

    # ── Apply filters ─────────────────────────────────────────────────────────
    mask = (
        df_full["lgu_type"].isin(sel_types)
        & df_full["region"].isin(sel_regions)
        & df_full["year"].between(*sel_years)
    )
    df = df_full[mask].copy()

    if df.empty:
        st.error("No data matches the current filters. Adjust the sidebar selections.")
        return

    # ── KPI row ───────────────────────────────────────────────────────────────
    st.header("Philippine LGU Fiscal Spending Dashboard", divider="gray")

    n_lgus     = df["lgu_name"].nunique()
    total_php  = df[list(SECTORS.values())].sum().sum()
    avg_pc     = df[ALL_PCOLS].sum(axis=1).agg(agg)
    yoy_df     = (
        df.groupby("year")[ALL_PCOLS]
        .mean()
        .sum(axis=1)
    )
    if len(yoy_df) >= 2:
        yoy = (yoy_df.iloc[-1] - yoy_df.iloc[-2]) / yoy_df.iloc[-2] * 100
        yoy_str = f"{yoy:+.1f}% vs prev yr"
    else:
        yoy_str = "—"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("LGUs in selection", f"{n_lgus:,}")
    k2.metric("Total spending (all sectors)", fmt_php(total_php / 1e9, 1) + " B")
    k3.metric(f"{agg_fn} per capita (all sectors)", fmt_php(avg_pc))
    k4.metric("YoY per capita change", yoy_str)

    st.divider()

    # ── Chart row 1: sector bar + sector trend ────────────────────────────────
    col_a, col_b = st.columns([3, 2], gap="large")

    with col_a:
        st.subheader(f"{agg_fn} per capita spending by sector")

        # One bar per sector, coloured by type (grouped)
        bar_rows = []
        for lgu_type in sel_types:
            sub = df[df["lgu_type"] == lgu_type]
            if sub.empty:
                continue
            for label, pc_col in PC_COL.items():
                v = sub[pc_col].agg(agg) if pc_col in sub.columns else 0.0
                bar_rows.append({"LGU Type": lgu_type, "Sector": label, "Per Capita (₱)": v})

        bar_df = pd.DataFrame(bar_rows)
        # Sort sectors by overall mean descending
        sector_order = (
            bar_df.groupby("Sector")["Per Capita (₱)"].mean()
            .sort_values(ascending=False)
            .index.tolist()
        )

        fig_bar = px.bar(
            bar_df,
            x="Sector",
            y="Per Capita (₱)",
            color="LGU Type",
            barmode="group",
            color_discrete_map=LGU_COLORS,
            category_orders={"Sector": sector_order},
            labels={"Per Capita (₱)": "₱ per capita"},
            height=380,
        )
        fig_bar.update_layout(
            legend_title_text="",
            xaxis_tickangle=-35,
            margin=dict(t=20, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_bar.update_yaxes(tickprefix="₱", tickformat=",.0f", gridcolor="#eee")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        st.subheader("Yearly trend — all sectors")

        trend_df = (
            df.groupby("year")[ALL_PCOLS]
            .agg(agg)
            .reset_index()
        )
        trend_long = trend_df.melt(
            id_vars="year",
            value_vars=ALL_PCOLS,
            var_name="pc_col",
            value_name="per_capita",
        )
        pc_to_label = {v: k for k, v in PC_COL.items()}
        trend_long["sector"] = trend_long["pc_col"].map(pc_to_label)

        fig_trend = px.line(
            trend_long,
            x="year",
            y="per_capita",
            color="sector",
            markers=True,
            labels={"per_capita": "₱ per capita", "year": "Year", "sector": "Sector"},
            color_discrete_sequence=SECTOR_PALETTE,
            height=380,
        )
        fig_trend.update_layout(
            legend_title_text="",
            margin=dict(t=20, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(dtick=1),
        )
        fig_trend.update_yaxes(tickprefix="₱", tickformat=",.0f", gridcolor="#eee")
        st.plotly_chart(fig_trend, use_container_width=True)

    # ── Chart row 2: distribution + stacked area ──────────────────────────────
    col_c, col_d = st.columns([2, 3], gap="large")

    with col_c:
        st.subheader(f"Distribution — {sel_sector}")
        pc_focus = PC_COL[sel_sector]

        if pc_focus in df.columns:
            fig_box = px.box(
                df,
                x="lgu_type",
                y=pc_focus,
                color="lgu_type",
                color_discrete_map=LGU_COLORS,
                points="outliers",
                labels={pc_focus: "₱ per capita", "lgu_type": "LGU Type"},
                category_orders={"lgu_type": ["province", "city", "municipality"]},
                height=370,
            )
            fig_box.update_layout(
                showlegend=False,
                margin=dict(t=20, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig_box.update_yaxes(tickprefix="₱", tickformat=",.0f", gridcolor="#eee")
            st.plotly_chart(fig_box, use_container_width=True)

    with col_d:
        st.subheader("Spending composition over time (stacked area)")

        stack_df = (
            df.groupby("year")[ALL_PCOLS]
            .mean()
            .reset_index()
        )
        stack_long = stack_df.melt(
            id_vars="year",
            value_vars=ALL_PCOLS,
            var_name="pc_col",
            value_name="per_capita",
        )
        stack_long["sector"] = stack_long["pc_col"].map(pc_to_label)

        fig_area = px.area(
            stack_long,
            x="year",
            y="per_capita",
            color="sector",
            labels={"per_capita": "₱ per capita", "year": "Year", "sector": "Sector"},
            color_discrete_sequence=SECTOR_PALETTE,
            height=370,
        )
        fig_area.update_layout(
            legend_title_text="",
            margin=dict(t=20, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(dtick=1),
        )
        fig_area.update_yaxes(tickprefix="₱", tickformat=",.0f", gridcolor="#eee")
        st.plotly_chart(fig_area, use_container_width=True)

    # ── Chart row 3: regional heatmap ─────────────────────────────────────────
    st.subheader(f"Regional heat map — {sel_sector} per capita ({agg_fn})")

    heat_df = (
        df.groupby(["region", "year"])[PC_COL[sel_sector]]
        .agg(agg)
        .reset_index()
        .rename(columns={PC_COL[sel_sector]: "per_capita"})
    )
    heat_pivot = heat_df.pivot(index="region", columns="year", values="per_capita")

    fig_heat = go.Figure(
        go.Heatmap(
            z=heat_pivot.values,
            x=[str(c) for c in heat_pivot.columns],
            y=heat_pivot.index.tolist(),
            colorscale="Blues",
            colorbar=dict(title="₱ / capita"),
            hoverongaps=False,
            hovertemplate="Region: %{y}<br>Year: %{x}<br>₱ %{z:,.0f}<extra></extra>",
        )
    )
    fig_heat.update_layout(
        height=max(320, len(heat_pivot) * 26 + 80),
        margin=dict(t=20, b=20, l=200),
        xaxis_title="Year",
        yaxis_title="",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # ── Chart row 4: top/bottom LGUs ─────────────────────────────────────────
    st.subheader(f"Top & bottom 15 LGUs — {sel_sector} per capita (period {agg_fn})")

    lgu_avg = (
        df.groupby(["lgu_name", "lgu_type"])[PC_COL[sel_sector]]
        .agg(agg)
        .reset_index()
        .rename(columns={PC_COL[sel_sector]: "per_capita"})
        .sort_values("per_capita", ascending=False)
    )

    top15    = lgu_avg.head(15).copy()
    bottom15 = lgu_avg.tail(15).copy()

    tc, bc = st.columns(2, gap="large")

    with tc:
        top15["rank"] = range(1, 16)
        top15["₱ per capita"] = top15["per_capita"].map(lambda v: fmt_php(v, 0))
        st.dataframe(
            top15[["rank", "lgu_name", "lgu_type", "₱ per capita"]]
            .rename(columns={"lgu_name": "LGU", "lgu_type": "Type", "rank": "#"}),
            hide_index=True,
            use_container_width=True,
        )

    with bc:
        bottom15 = bottom15.iloc[::-1].reset_index(drop=True)
        bottom15["rank"] = range(len(lgu_avg), len(lgu_avg) - 15, -1)
        bottom15["₱ per capita"] = bottom15["per_capita"].map(lambda v: fmt_php(v, 0))
        st.dataframe(
            bottom15[["rank", "lgu_name", "lgu_type", "₱ per capita"]]
            .rename(columns={"lgu_name": "LGU", "lgu_type": "Type", "rank": "#"}),
            hide_index=True,
            use_container_width=True,
        )

    # ── Raw data explorer ─────────────────────────────────────────────────────
    with st.expander("Raw data explorer", expanded=False):
        show_cols = (
            ["lgu_name", "lgu_type", "region", "year", "population"]
            + list(SECTORS.values())
            + ALL_PCOLS
        )
        show_cols = [c for c in show_cols if c in df.columns]
        st.dataframe(
            df[show_cols].sort_values(["lgu_name", "year"]),
            use_container_width=True,
            height=400,
        )
        csv_bytes = df[show_cols].to_csv(index=False).encode()
        st.download_button(
            "⬇ Download filtered data as CSV",
            data=csv_bytes,
            file_name="lgu_spending_filtered.csv",
            mime="text/csv",
        )

    st.caption(
        "Data: Philippine Commission on Audit / BLGF Statement of Income and Expenditures "
        "| Dashboard built with Streamlit & Plotly"
    )


if __name__ == "__main__":
    main()
