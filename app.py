import streamlit as st
import pandas as pd
import os
import plotly.express as px

# ======================================================
# CONFIGURATION
# ======================================================
st.set_page_config(page_title="Staff Appraisal System", layout="wide")

# ======================================================
# CUSTOM CSS (Orange, Black, White Theme)
# ======================================================
st.markdown("""
<style>
    .main {
        background-color: white;
    }
    h1, h2, h3 {
        color: black;
    }
    .stApp {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# ======================================================
# TITLE
# ======================================================
st.title("Staff Performance Appraisal Dashboard")

# ======================================================
# PATH TO REPORTS
# ======================================================
BASE_DIR = "reports"

# ======================================================
# GET MONTH FOLDERS
# ======================================================
month_folders = sorted([
    f for f in os.listdir(BASE_DIR)
    if os.path.isdir(os.path.join(BASE_DIR, f))
])

selected_month = st.selectbox("Select Month", month_folders)

month_path = os.path.join(BASE_DIR, selected_month)

# ======================================================
# LOAD ALL CSV FILES FOR MONTHLY DASHBOARD
# ======================================================
all_month_data = []

files = [
    f for f in os.listdir(month_path)
    if f.endswith(".csv")
]

selected_file = st.selectbox("Select Daily Report File", files)

for file in files:
    file_path = os.path.join(month_path, file)

    try:
        temp_df = pd.read_csv(file_path)
        temp_df["Source_File"] = file
        all_month_data.append(temp_df)
    except Exception as e:
        st.warning(f"Could not load {file}: {e}")

# Monthly Combined Data
monthly_df = pd.concat(all_month_data, ignore_index=True)

# Normalize column names
monthly_df.columns = monthly_df.columns.str.strip()

# ======================================================
# LOAD DAILY FILE
# ======================================================
file_path = os.path.join(month_path, selected_file)

df = pd.read_csv(file_path)
df.columns = df.columns.str.strip()

# ======================================================
# TASK SCORE FUNCTION
# ======================================================
def task_score(x):
    x = str(x).strip().lower()

    if x == "yes":
        return 1
    elif x == "partially":
        return 0.5
    else:
        return 0

# ======================================================
# DAILY PERFORMANCE CALCULATION
# ======================================================
df["Task1_Score"] = df["Was Task 1 completed?"].apply(task_score)
df["Task2_Score"] = df["Was Task 2 completed?"].apply(task_score)

df["Daily_Score"] = (
    (df["Task1_Score"] + df["Task2_Score"]) / 2
) * 100

# ======================================================
# MONTHLY PERFORMANCE CALCULATION
# ======================================================
monthly_df["Task1_Score"] = monthly_df[
    "Was Task 1 completed?"
].apply(task_score)

monthly_df["Task2_Score"] = monthly_df[
    "Was Task 2 completed?"
].apply(task_score)

monthly_df["Daily_Score"] = (
    (monthly_df["Task1_Score"] +
     monthly_df["Task2_Score"]) / 2
) * 100

# ======================================================
# GROUP BY STAFF (MONTHLY VIEW)
# ======================================================
performance = monthly_df.groupby(
    ["Name", "Department", "Designation"]
).agg({
    "Task1_Score": "mean",
    "Task2_Score": "mean",
    "Daily_Score": "mean"
}).reset_index()

performance["Performance %"] = performance[
    "Daily_Score"
]

# ======================================================
# RANKING
# ======================================================
performance = performance.sort_values(
    by="Performance %",
    ascending=False
)

performance["Rank"] = range(
    1,
    len(performance) + 1
)

top_performers = performance.head(5)
low_performers = performance.tail(5)

# ======================================================
# DASHBOARD METRICS
# ======================================================
col1, col2, col3 = st.columns(3)

col1.metric("Total Staff", len(performance))

col2.metric(
    "Top Performer Score",
    round(performance["Performance %"].max(), 2)
)

col3.metric(
    "Lowest Score",
    round(performance["Performance %"].min(), 2)
)

# ======================================================
# PIE CHART
# ======================================================
st.subheader("Performance Distribution")

performance["Performance Band"] = pd.cut(
    performance["Performance %"],
    bins=[0, 50, 75, 100],
    labels=["Low", "Average", "High"],
    include_lowest=True
)

pie_data = performance[
    "Performance Band"
].value_counts().reset_index()

pie_data.columns = ["Band", "Count"]

fig_pie = px.pie(
    pie_data,
    names="Band",
    values="Count",
    color_discrete_sequence=[
        "black",
        "orange",
        "#ffcc99"
    ]
)

st.plotly_chart(
    fig_pie,
    use_container_width=True
)

# ======================================================
# BAR CHART (MONTHLY RANKING)
# ======================================================
st.subheader(
    f"Monthly Staff Performance Ranking - {selected_month}"
)

fig_bar = px.bar(
    performance,
    x="Name",
    y="Performance %",
    color="Performance %",
    color_continuous_scale=[
        "black",
        "orange",
        "white"
    ],
    text="Performance %"
)

st.plotly_chart(
    fig_bar,
    use_container_width=True
)

# ======================================================
# TOP & LOW PERFORMERS
# ======================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top Performers")
    st.dataframe(
        top_performers,
        use_container_width=True
    )

with col2:
    st.subheader("⚠️ Low Performers")
    st.dataframe(
        low_performers,
        use_container_width=True
    )

# ======================================================
# FULL TABLE
# ======================================================
st.subheader("Monthly Appraisal Table")
st.dataframe(
    performance,
    use_container_width=True
)

# ======================================================
# QUARTERLY DASHBOARD
# ======================================================
st.subheader("Quarterly Dashboard")

quarter_mapping = {
    "January": "Q1",
    "February": "Q1",
    "March": "Q1",
    "April": "Q2",
    "May": "Q2",
    "June": "Q2",
    "July": "Q3",
    "August": "Q3",
    "September": "Q3",
    "October": "Q4",
    "November": "Q4",
    "December": "Q4",
}

selected_quarter = quarter_mapping.get(
    selected_month,
    "Q1"
)

quarter_months = [
    month for month, q in
    quarter_mapping.items()
    if q == selected_quarter
]

quarterly_data = []

for month in quarter_months:
    q_path = os.path.join(BASE_DIR, month)

    if os.path.exists(q_path):

        q_files = [
            f for f in os.listdir(q_path)
            if f.endswith(".csv")
        ]

        for file in q_files:
            try:
                temp = pd.read_csv(
                    os.path.join(q_path, file)
                )

                quarterly_data.append(temp)

            except:
                pass

if quarterly_data:

    quarterly_df = pd.concat(
        quarterly_data,
        ignore_index=True
    )

    quarterly_df.columns = (
        quarterly_df.columns.str.strip()
    )

    quarterly_df["Task1_Score"] = quarterly_df[
        "Was Task 1 completed?"
    ].apply(task_score)

    quarterly_df["Task2_Score"] = quarterly_df[
        "Was Task 2 completed?"
    ].apply(task_score)

    quarterly_df["Daily_Score"] = (
        quarterly_df["Task1_Score"] +
        quarterly_df["Task2_Score"]
    ) / 2 * 100

    quarterly_performance = quarterly_df.groupby(
        "Name"
    )["Daily_Score"].mean().reset_index()

    quarterly_performance.rename(
        columns={
            "Daily_Score":
            "Quarterly Performance %"
        },
        inplace=True
    )

    fig_quarter = px.bar(
        quarterly_performance,
        x="Name",
        y="Quarterly Performance %",
        text="Quarterly Performance %",
        color="Quarterly Performance %",
        color_continuous_scale=[
            "black",
            "orange",
            "white"
        ]
    )

    st.plotly_chart(
        fig_quarter,
        use_container_width=True
    )

    st.dataframe(
        quarterly_performance,
        use_container_width=True
    )

# ======================================================
# CHALLENGES SUMMARY
# ======================================================
st.subheader("Daily Challenges Report")

if "Challenges faced during the day" in df.columns:
    st.dataframe(
        df[[
            "Name",
            "Challenges faced during the day"
        ]],
        use_container_width=True
)
