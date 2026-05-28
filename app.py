```python
import streamlit as st
import pandas as pd
import os
import plotly.express as px

# ======================================================
# CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="Staff Appraisal System",
    layout="wide"
)

# ======================================================
# CUSTOM CSS
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
st.title(
    "Staff Performance Appraisal Dashboard"
)

# ======================================================
# PATH TO REPORTS
# ======================================================
BASE_DIR = "reports"

# ======================================================
# LOAD EMPLOYEE MASTER LIST
# employee.csv format:
# Name
# John Doe
# Mary James
# ======================================================
employee_file = "employee.csv"

if os.path.exists(employee_file):

    employee_df = pd.read_csv(
        employee_file
    )

    employee_df.columns = (
        employee_df.columns
        .str.strip()
    )

else:
    st.error(
        "employee.csv file not found"
    )
    st.stop()

# ======================================================
# GET MONTH FOLDERS
# ======================================================
month_folders = sorted([
    f for f in os.listdir(BASE_DIR)
    if os.path.isdir(
        os.path.join(
            BASE_DIR,
            f
        )
    )
])

selected_month = st.selectbox(
    "Select Month",
    month_folders
)

month_path = os.path.join(
    BASE_DIR,
    selected_month
)

# ======================================================
# LOAD ALL CSV FILES
# ======================================================
all_month_data = []

files = [
    f for f in os.listdir(
        month_path
    )
    if f.endswith(".csv")
]

selected_file = st.selectbox(
    "Select Daily Report File",
    files
)

for file in files:

    file_path = os.path.join(
        month_path,
        file
    )

    try:
        temp_df = pd.read_csv(
            file_path
        )

        temp_df["Source_File"] = (
            file
        )

        all_month_data.append(
            temp_df
        )

    except Exception as e:
        st.warning(
            f"Could not load {file}: {e}"
        )

# ======================================================
# MONTHLY DATA
# ======================================================
monthly_df = pd.concat(
    all_month_data,
    ignore_index=True
)

monthly_df.columns = (
    monthly_df.columns
    .str.strip()
)

# ======================================================
# LOAD DAILY FILE
# ======================================================
file_path = os.path.join(
    month_path,
    selected_file
)

df = pd.read_csv(file_path)

df.columns = (
    df.columns
    .str.strip()
)

# ======================================================
# TASK SCORE FUNCTION
# ======================================================
def task_score(x):

    x = str(x).strip().lower()

    if x == "yes":
        return 1

    elif x == "partially":
        return 0.5

    return 0

# ======================================================
# DAILY PERFORMANCE
# ======================================================
df["Task1_Score"] = df[
    "Was Task 1 completed?"
].apply(task_score)

df["Task2_Score"] = df[
    "Was Task 2 completed?"
].apply(task_score)

df["Daily_Score"] = (
    (
        df["Task1_Score"] +
        df["Task2_Score"]
    ) / 2
) * 100

# ======================================================
# MONTHLY PERFORMANCE
# ======================================================
monthly_df["Task1_Score"] = (
    monthly_df[
        "Was Task 1 completed?"
    ].apply(task_score)
)

monthly_df["Task2_Score"] = (
    monthly_df[
        "Was Task 2 completed?"
    ].apply(task_score)
)

monthly_df["Daily_Score"] = (
    (
        monthly_df[
            "Task1_Score"
        ] +
        monthly_df[
            "Task2_Score"
        ]
    ) / 2
) * 100

# ======================================================
# GROUP BY STAFF
# ======================================================
performance = monthly_df.groupby(
    [
        "Name",
        "Department",
        "Designation"
    ]
).agg({
    "Task1_Score": "mean",
    "Task2_Score": "mean",
    "Daily_Score": "mean"
}).reset_index()

performance["Performance %"] = (
    performance["Daily_Score"]
)

# ======================================================
# ADD NON-SUBMITTERS
# ======================================================
submitted_staff = set(
    monthly_df["Name"]
    .astype(str)
    .str.strip()
)

all_staff = set(
    employee_df["Name"]
    .astype(str)
    .str.strip()
)

missing_staff = (
    all_staff -
    submitted_staff
)

missing_records = []

for staff in missing_staff:

    missing_records.append({
        "Name": staff,
        "Department":
        "Not Submitted",
        "Designation":
        "Not Submitted",
        "Task1_Score": 0,
        "Task2_Score": 0,
        "Daily_Score": 0,
        "Performance %": 0
    })

if missing_records:

    missing_df = pd.DataFrame(
        missing_records
    )

    performance = pd.concat(
        [
            performance,
            missing_df
        ],
        ignore_index=True
    )

# ======================================================
# TRACK STAFF WHO MISSED 3+ TIMES
# ======================================================
missed_tracking = []

for staff in all_staff:

    missed_count = 0

    for file in files:

        try:

            temp_df = pd.read_csv(
                os.path.join(
                    month_path,
                    file
                )
            )

            temp_df.columns = (
                temp_df.columns
                .str.strip()
            )

            submitted_names = set(
                temp_df["Name"]
                .astype(str)
                .str.strip()
            )

            if staff not in submitted_names:
                missed_count += 1

        except:
            pass

    if missed_count >= 3:

        missed_tracking.append({
            "Name": staff,
            "Missed Submission":
            missed_count
        })

missed_df = pd.DataFrame(
    missed_tracking
)

# ======================================================
# RANKING
# ======================================================
performance = performance.sort_values(
    by="Performance %",
    ascending=False
).reset_index(drop=True)

performance["Rank"] = (
    performance.index + 1
)

top_performers = (
    performance.head(5)
)

low_performers = (
    performance.tail(5)
)

# ======================================================
# DASHBOARD METRICS
# ======================================================
col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Staff",
    len(performance)
)

col2.metric(
    "Top Performer Score",
    round(
        performance[
            "Performance %"
        ].max(),
        2
    )
)

col3.metric(
    "Lowest Score",
    round(
        performance[
            "Performance %"
        ].min(),
        2
    )
)

# ======================================================
# PIE CHART
# ======================================================
st.subheader(
    "Performance Distribution"
)

performance[
    "Performance Band"
] = pd.cut(
    performance[
        "Performance %"
    ],
    bins=[0, 50, 75, 100],
    labels=[
        "Low",
        "Average",
        "High"
    ],
    include_lowest=True
)

pie_data = performance[
    "Performance Band"
].value_counts().reset_index()

pie_data.columns = [
    "Band",
    "Count"
]

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
# BAR CHART
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

    st.subheader(
        "🏆 Top Performers"
    )

    top_performers_display = (
        top_performers
        .reset_index(drop=True)
    )

    top_performers_display.index = (
        top_performers_display.index + 1
    )

    st.dataframe(
        top_performers_display,
        use_container_width=True
    )

with col2:

    st.subheader(
        "⚠️ Low Performers"
    )

    low_performers_display = (
        low_performers
        .reset_index(drop=True)
    )

    low_performers_display.index = (
        low_performers_display.index + 1
    )

    st.dataframe(
        low_performers_display,
        use_container_width=True
    )

# ======================================================
# MISSED 3+ SUBMISSIONS ONLY
# ======================================================
st.subheader(
    "Staff That Failed To Submit 3+ Times"
)

if not missed_df.empty:

    missed_df.index = (
        range(
            1,
            len(missed_df) + 1
        )
    )

    st.dataframe(
        missed_df,
        use_container_width=True
    )

else:
    st.success(
        "No staff missed submission 3 times."
    )

# ======================================================
# FULL TABLE
# ======================================================
st.subheader(
    "Monthly Appraisal Table"
)

performance_display = (
    performance
    .reset_index(drop=True)
)

performance_display.index = (
    performance_display.index + 1
)

st.dataframe(
    performance_display,
    use_container_width=True
)

# ======================================================
# DAILY CHALLENGES
# ======================================================
st.subheader(
    "Daily Challenges Report"
)

if (
    "Challenges faced during the day"
    in df.columns
):

    challenge_df = df[[
        "Name",
        "Challenges faced during the day"
    ]].reset_index(
        drop=True
    )

    challenge_df.index = (
        challenge_df.index + 1
    )

    st.dataframe(
        challenge_df,
        use_container_width=True
    )
```
        
