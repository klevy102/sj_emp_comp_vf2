import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import psycopg2

# ── page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="San Jose Employee Compensation",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── global styles ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: black;
    background: #c1e7ff;
}

.stApp, .main, .block-container {
    background: #c1e7ff !important;
}

.block-container {
    padding-top: 3.5rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

h1, h2, h3, h4, h5, h6, p, label, span, div {
    color: black;
}

h1 {
    margin-bottom: 0.25rem;
}

.kpi-card {
    margin-bottom: 1rem;
}

[data-testid="stHorizontalBlock"] > div {
    gap: 1rem !important;
}

.stButton>button {
    margin-top: 0.5rem !important;
}

.kpi-card {
    background: white;
    border-radius: 10px;
    padding: 18px 22px;
    border: 1px solid #e8eaf0;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
}

.kpi-label {
    font-size: 11px;
    font-weight: 600;
    color: black;
    letter-spacing: .8px;
    text-transform: uppercase;
}

.kpi-value {
    font-size: 30px;
    font-weight: 700;
    color: black;
    margin: 4px 0 2px;
}

.kpi-sub {
    font-size: 12px;
    color: black;
}

.section-header {
    font-size: 18px;
    font-weight: 700;
    color: black;
    margin-top: 20px;
    margin-bottom: 8px;
}

[data-testid="stSidebar"] {
    background: #f5f7fa;
}

[data-testid="stSidebar"] * {
    color: black !important;
}
</style>
""", unsafe_allow_html=True)


# ── plotly formatting helper ───────────────────────────────────────────────────
def format_chart(fig, title, x_title, y_title, legend_title=None):
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, color="black"),
            x=0.01
        ),
        font=dict(color="black"),
        plot_bgcolor="#e6f7ff",
        paper_bgcolor="#e6f7ff",
        xaxis=dict(
            title=dict(text=x_title, font=dict(color="black")),
            tickfont=dict(color="black"),
            showline=True,
            linecolor="black",
            gridcolor="#e5e5e5"
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(color="black")),
            tickfont=dict(color="black"),
            showline=True,
            linecolor="black",
            gridcolor="#e5e5e5"
        ),
        legend=dict(
            title=dict(text=legend_title if legend_title else "", font=dict(color="black")),
            font=dict(color="black"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),
        margin=dict(l=40, r=30, t=70, b=50),
    )
    return fig


# ── database ────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "sj_emp_comp"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    conn = get_conn()
    return pd.read_sql("""
        SELECT
            e.name,
            d.name AS department,
            j.title AS job_title,
            c.fiscal_year,
            COALESCE(c.base_pay, 0) AS base_pay,
            COALESCE(c.overtime, 0) AS overtime,
            COALESCE(c.sick_and_vacation_payouts, 0) AS sick_vacation,
            COALESCE(c.other_cash_compensation, 0) AS other_cash,
            COALESCE(c.total_cash_compensation, 0) AS total_cash,
            COALESCE(c.defined_contribution_plan_contributions, 0)
                + COALESCE(c.medical_dental_vision, 0)
                + COALESCE(c.retirement_contributions_normal_cost, 0)
                + COALESCE(c.long_term_disability_life_medicare, 0)
                + COALESCE(c.misc_employment_related_costs, 0) AS total_benefits,
            COALESCE(c.total_cash_compensation, 0)
                + COALESCE(c.defined_contribution_plan_contributions, 0)
                + COALESCE(c.medical_dental_vision, 0)
                + COALESCE(c.retirement_contributions_normal_cost, 0)
                + COALESCE(c.long_term_disability_life_medicare, 0)
                + COALESCE(c.misc_employment_related_costs, 0) AS total_comp
        FROM compensation c
        JOIN employees e ON e.id = c.employee_id
        JOIN departments d ON d.id = e.department_id
        JOIN job_titles j ON j.id = e.job_title_id
    """, conn)


# ── load data ───────────────────────────────────────────────────────────────────
df_raw = load_data()

# ── sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Fiscal Dashboard")
    st.caption("San Jose Employee Compensation Analysis: 2020–2024")
    st.markdown("---")

    page = st.radio(
        "Dashboard Page",
        ["Overview", "Trends", "Departments", "Outliers"]
    )

    st.markdown("---")
    st.markdown("### Filters")

    years = sorted(df_raw["fiscal_year"].unique())
    depts = sorted(df_raw["department"].unique())

    sel_year = st.selectbox("Fiscal Year", ["All Years"] + [str(y) for y in years])
    sel_depts = st.multiselect("Department", depts, default=depts[:4])
    comp_range = st.slider(
        "Total Compensation Range",
        0,
        500_000,
        (0, 500_000),
        step=10_000,
        format="$%d"
    )

    export_btn = st.button("Export Filtered Dataset", use_container_width=True)


# ── filter data ─────────────────────────────────────────────────────────────────
df = df_raw.copy()

if sel_year != "All Years":
    df = df[df["fiscal_year"] == int(sel_year)]

if sel_depts:
    df = df[df["department"].isin(sel_depts)]

df = df[
    (df["total_comp"] >= comp_range[0]) &
    (df["total_comp"] <= comp_range[1])
]

if export_btn:
    st.sidebar.download_button(
        "Download CSV",
        df.to_csv(index=False),
        "sj_comp_export.csv",
        "text/csv"
    )


# ── main header ─────────────────────────────────────────────────────────────────
st.title("San Jose Employee Compensation Dashboard")
st.caption("Interactive dashboard analyzing employee compensation by year, department, and compensation category.")

if df.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# ────────────────────────────────────────────────────────────────────────────────
# OVERVIEW PAGE
# ────────────────────────────────────────────────────────────────────────────────
if page == "Overview":

    total_comp = df["total_comp"].sum()
    avg_comp = df["total_comp"].mean()
    top_dept = df.groupby("department")["total_comp"].sum().idxmax()
    top_dept_pct = (
        df.groupby("department")["total_comp"].sum().max()
        / df["total_comp"].sum()
        * 100
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Total Compensation</div>
            <div class='kpi-value'>${total_comp / 1e9:.2f} Billion</div>
            <div class='kpi-sub'>Total employee compensation in selected data</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Average Compensation per Employee</div>
            <div class='kpi-value'>${avg_comp / 1e3:.1f}K</div>
            <div class='kpi-sub'>Average total compensation per employee</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Highest Spending Department</div>
            <div class='kpi-value' style='font-size:22px'>{top_dept}</div>
            <div class='kpi-sub'>{top_dept_pct:.1f}% of total selected compensation</div>
        </div>
        """, unsafe_allow_html=True)

    top5 = df_raw.groupby("department")["total_comp"].sum().nlargest(5).index.tolist()
    trend_df = (
        df_raw[df_raw["department"].isin(top5)]
        .groupby(["fiscal_year", "department"])["total_comp"]
        .sum()
        .reset_index()
    )

    fig_trend = px.line(
        trend_df,
        x="fiscal_year",
        y="total_comp",
        color="department",
        markers=True
    )

    fig_trend.update_yaxes(tickprefix="$", tickformat=".2s")
    fig_trend = format_chart(
        fig_trend,
        title="",
        x_title="Fiscal Year",
        y_title="Total Compensation (USD)",
        legend_title="Department"
    )

    st.plotly_chart(fig_trend, use_container_width=True)

    comp_df = (
        df.groupby("department")
        .agg(
            Base_Pay=("base_pay", "sum"),
            Benefits=("total_benefits", "sum"),
            Overtime=("overtime", "sum")
        )
        .nlargest(5, "Base_Pay")
        .reset_index()
    )

    fig_comp = go.Figure()

    fig_comp.add_trace(go.Bar(
        name="Base Pay",
        y=comp_df["department"],
        x=comp_df["Base_Pay"],
        orientation="h"
    ))

    fig_comp.add_trace(go.Bar(
        name="Benefits",
        y=comp_df["department"],
        x=comp_df["Benefits"],
        orientation="h"
    ))

    fig_comp.add_trace(go.Bar(
        name="Overtime",
        y=comp_df["department"],
        x=comp_df["Overtime"],
        orientation="h"
    ))

    fig_comp.update_layout(barmode="stack")
    fig_comp.update_xaxes(tickprefix="$", tickformat=".2s")

    fig_comp = format_chart(
        fig_comp,
        title="",
        x_title="Total Compensation Amount (USD)",
        y_title="Department",
        legend_title="Compensation Category"
    )

    st.plotly_chart(fig_comp, use_container_width=True)

    top10 = (
        df.groupby("department")["total_comp"]
        .sum()
        .nlargest(10)
        .reset_index()
        .sort_values("total_comp")
    )

    fig_top10 = px.bar(
        top10,
        x="total_comp",
        y="department",
        orientation="h"
    )

    fig_top10.update_xaxes(tickprefix="$", tickformat=".2s")

    fig_top10 = format_chart(
        fig_top10,
        title="",
        x_title="Total Compensation (USD)",
        y_title="Department",
        legend_title=None
    )

    fig_top10.update_layout(showlegend=False)

    st.plotly_chart(fig_top10, use_container_width=True)

    box_depts = df.groupby("department")["total_comp"].sum().nlargest(4).index.tolist()
    box_df = df[df["department"].isin(box_depts)]

    fig_box = px.box(
        box_df,
        x="total_comp",
        y="department",
        orientation="h",
        points="outliers"
    )

    fig_box.update_xaxes(tickprefix="$", tickformat=".2s")

    fig_box = format_chart(
        fig_box,
        title="",
        x_title="Employee Total Compensation (USD)",
        y_title="Department",
        legend_title=None
    )

    fig_box.update_layout(showlegend=False)

    st.plotly_chart(fig_box, use_container_width=True)

    table_df = df[[
        "name",
        "department",
        "job_title",
        "base_pay",
        "overtime",
        "total_comp"
    ]].copy()

    table_df = table_df.sort_values("total_comp", ascending=False).reset_index(drop=True)

    table_df.columns = [
        "Name",
        "Department",
        "Job Title",
        "Base Pay",
        "Overtime",
        "Total Compensation"
    ]

    st.dataframe(
        table_df.style.format({
            "Base Pay": "${:,.0f}",
            "Overtime": "${:,.0f}",
            "Total Compensation": "${:,.0f}"
        }),
        use_container_width=True,
        height=320
    )

    st.caption(f"Showing {len(table_df):,} employee records.")


# ────────────────────────────────────────────────────────────────────────────────
# TRENDS PAGE
# ────────────────────────────────────────────────────────────────────────────────
elif page == "Trends":

    st.header("Compensation Trends Over Time")

    trend_all = (
        df_raw.groupby(["fiscal_year", "department"])["total_comp"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        trend_all,
        x="fiscal_year",
        y="total_comp",
        color="department",
        markers=True
    )

    fig.update_yaxes(tickprefix="$", tickformat=".2s")

    fig = format_chart(
        fig,
        title="Total Compensation Trends by Department Over Time",
        x_title="Fiscal Year",
        y_title="Total Compensation (USD)",
        legend_title="Department"
    )

    st.plotly_chart(fig, use_container_width=True)


# ────────────────────────────────────────────────────────────────────────────────
# DEPARTMENTS PAGE
# ────────────────────────────────────────────────────────────────────────────────
elif page == "Departments":

    st.header("Department Compensation Breakdown")

    dept_summary = (
        df.groupby("department")
        .agg(
            Employees=("name", "count"),
            Average_Compensation=("total_comp", "mean"),
            Total_Compensation=("total_comp", "sum")
        )
        .sort_values("Total_Compensation", ascending=False)
        .reset_index()
    )

    dept_summary.columns = [
        "Department",
        "Employee Count",
        "Average Compensation",
        "Total Compensation"
    ]

    st.dataframe(
        dept_summary.style.format({
            "Average Compensation": "${:,.0f}",
            "Total Compensation": "${:,.0f}"
        }),
        use_container_width=True
    )


# ────────────────────────────────────────────────────────────────────────────────
# OUTLIERS PAGE
# ────────────────────────────────────────────────────────────────────────────────
elif page == "Outliers":

    st.header("Compensation Outliers")

    q99 = df["total_comp"].quantile(0.99)

    outliers = (
        df[df["total_comp"] > q99]
        .sort_values("total_comp", ascending=False)
    )

    st.info(f"{len(outliers)} employees are above the 99th percentile compensation threshold of ${q99:,.0f}.")

    outlier_table = outliers[[
        "name",
        "department",
        "job_title",
        "base_pay",
        "overtime",
        "total_comp"
    ]].rename(columns={
        "name": "Name",
        "department": "Department",
        "job_title": "Job Title",
        "base_pay": "Base Pay",
        "overtime": "Overtime",
        "total_comp": "Total Compensation"
    })

    st.dataframe(
        outlier_table.style.format({
            "Base Pay": "${:,.0f}",
            "Overtime": "${:,.0f}",
            "Total Compensation": "${:,.0f}"
        }),
        use_container_width=True
    )