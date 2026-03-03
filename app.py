import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PH LGU Fiscal Explorer", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("lgu_fiscal_panel.csv", low_memory=False)
    return df

df = load_data()

st.title("Philippine LGU Fiscal Data Explorer")
st.markdown("Explore local government unit appropriations data across regions, provinces, and years.")

# Sidebar filters
st.sidebar.header("Filters")

regions = sorted(df["region"].dropna().unique())
selected_region = st.sidebar.selectbox("Region", ["All"] + list(regions))

if selected_region != "All":
    filtered = df[df["region"] == selected_region]
else:
    filtered = df.copy()

provinces = sorted(filtered["province"].dropna().unique())
selected_province = st.sidebar.selectbox("Province", ["All"] + list(provinces))

if selected_province != "All":
    filtered = filtered[filtered["province"] == selected_province]

lgu_types = sorted(filtered["lgutype_n"].dropna().unique())
selected_type = st.sidebar.multiselect("LGU Type", lgu_types, default=lgu_types)
if selected_type:
    filtered = filtered[filtered["lgutype_n"].isin(selected_type)]

years = sorted(filtered["year"].dropna().unique())
year_range = st.sidebar.select_slider("Year Range", options=years, value=(min(years), max(years)))
filtered = filtered[(filtered["year"] >= year_range[0]) & (filtered["year"] <= year_range[1])]

# Summary metrics
st.subheader("Summary")
col1, col2, col3 = st.columns(3)
col1.metric("LGUs", filtered["lgu"].nunique())
col2.metric("Years", filtered["year"].nunique())
col3.metric("Records", len(filtered))

# Spending by sector over time
st.subheader("Average Annual Appropriations by Sector")

sector_cols = {
    "Education": "aa_educ",
    "Health": "aa_health",
    "Social Services": "aa_social",
    "General Services": "aa_gen_serv",
    "Economic Services": "aa_sh_econ_serv",
}

available = {k: v for k, v in sector_cols.items() if v in filtered.columns}

if available:
    trend = (
        filtered.groupby("year")[list(available.values())]
        .mean()
        .reset_index()
        .rename(columns={v: k for k, v in available.items()})
    )
    trend_melted = trend.melt(id_vars="year", var_name="Sector", value_name="Average Appropriation")
    fig = px.line(
        trend_melted,
        x="year",
        y="Average Appropriation",
        color="Sector",
        markers=True,
        title="Average Appropriations by Sector (Selected LGUs)",
    )
    st.plotly_chart(fig, use_container_width=True)

# Total appropriations per capita
st.subheader("Per Capita Total Appropriations")

if "aa_pc_total_all" in filtered.columns:
    pc_data = filtered.dropna(subset=["aa_pc_total_all"])
    if not pc_data.empty:
        fig2 = px.box(
            pc_data,
            x="year",
            y="aa_pc_total_all",
            color="lgutype_n",
            title="Per Capita Appropriations by Year and LGU Type",
            labels={"aa_pc_total_all": "Per Capita Appropriation (PHP)", "year": "Year", "lgutype_n": "LGU Type"},
        )
        st.plotly_chart(fig2, use_container_width=True)

# LGU ranking table
st.subheader("LGU Appropriation Summary (Latest Year)")

latest_year = filtered["year"].max()
latest = filtered[filtered["year"] == latest_year][["lgu", "province", "region", "lgutype_n", "aa_total"]].dropna(subset=["aa_total"])
latest = latest.sort_values("aa_total", ascending=False).reset_index(drop=True)
latest["aa_total"] = latest["aa_total"].apply(lambda x: f"₱{x:,.0f}")
latest.columns = ["LGU", "Province", "Region", "Type", f"Total Appropriation ({latest_year})"]
st.dataframe(latest, use_container_width=True)
