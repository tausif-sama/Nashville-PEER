import streamlit as st
import pandas as pd
import numpy as np          # ← Make sure numpy is imported before using np.zeros
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Walkthrough Perspectives Dashboard", layout="wide")
st.title("Walkthrough Perspectives Dashboard")
# ─────────────────────────────────────────────────────────────────────────────

uploaded_file = st.file_uploader("Upload the CSV file", type=["csv"])
if uploaded_file is None:
    st.info("📄 Please upload your CSV to proceed.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 1) LOAD & PREPARE THE DATA
# ─────────────────────────────────────────────────────────────────────────────

df = pd.read_csv(uploaded_file)

# Clean “Your affiliation:” and map to ILT vs SH
df["Your affiliation:"] = df["Your affiliation:"].astype(str).str.strip()
df["Affiliation"] = df["Your affiliation:"].map({
    "This school's ILT": "ILT",
    "MNPS Support Hub":   "SH"
})

# PURPOSE OF WALKTHROUGHS – we need to identify & clean those columns
label_mapping = {
    "Identify areas for instructional improvement for the math or ELA team at this school":
        "Identify areas for instructional improvement",
    "Identify needed professional learning supports regarding math or ELA teaching":
        "Identify needed professional learning supports",
    "Sharpen our eye for quality math or ELA instruction":
        "Sharpen our eye for quality instruction",
    "Monitor progress on this school's math or ELA theory of action":
        "Monitor progress on this school's theory of action",
    "Identify additional curricular implementation supports":
        "Identify additional curricular implementation supports",
    "Provide feedback to individual teachers":
        "Provide feedback to individual teachers",
    "Evaluate individual teacher competence":
        "Evaluate individual teacher competence"
}

def clean_column_name(colname: str) -> str:
    for long_text, short_text in label_mapping.items():
        if f"(choice={long_text})" in colname:
            return short_text
    return colname

purpose_columns = [
    col for col in df.columns
    if col.startswith("The purpose of this walkthrough was to:")
]
cleaned_purpose_cols = [clean_column_name(c) for c in purpose_columns]
df_purposes = df[purpose_columns].copy()
df_purposes.columns = cleaned_purpose_cols

# Split into SH vs ILT for “purpose” counts
support_hub_df = df[df["Affiliation"] == "SH"]
ilt_df        = df[df["Affiliation"] == "ILT"]

support_counts = (support_hub_df[purpose_columns] == "Checked").sum()
ilt_counts     = (ilt_df[purpose_columns] == "Checked").sum()
support_counts.index = cleaned_purpose_cols
ilt_counts.index     = cleaned_purpose_cols

support_percent = 100 * support_counts / support_counts.sum() if support_counts.sum() > 0 else pd.Series(dtype=float)
ilt_percent     = 100 * ilt_counts     / ilt_counts.sum()     if ilt_counts.sum()     > 0 else pd.Series(dtype=float)

support_percent = support_percent.sort_values(ascending=False)
ilt_percent     = ilt_percent.sort_values(ascending=False)

def custom_autopct(pct: float) -> str:
    return f"{pct:.1f}%" if pct > 1 else ""

def plot_donut_chart(percent_series: pd.Series, title: str, color_list: list):
    fig, ax = plt.subplots(figsize=(5, 5))
    wedges, texts, autotexts = ax.pie(
        percent_series.values,
        labels=None,
        autopct=custom_autopct,
        startangle=90,
        counterclock=False,
        colors=color_list[: len(percent_series)],
        wedgeprops=dict(width=0.3)
    )
    for autotext in autotexts:
        autotext.set_fontsize(8)
    ax.axis("equal")
    ax.set_title(title, pad=20)
    ax.legend(
        wedges,
        percent_series.index,
        title="",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=8
    )
    st.pyplot(fig)

# WHO TALKED THE MOST – helper
talk_column = "Who talked the most during the debrief conversation?"
label_map_talk = {
    "No one person spoke significantly more than others": "No single dominant voice",
    "Other SH Members":  "Other SH Members",
    "Other ILT Members": "Other ILT Members",
    "The executive director(s)": "The Executive Director"
}

def get_talk_percentages(df_subset: pd.DataFrame) -> pd.Series:
    counts = df_subset[talk_column].value_counts()
    counts.index = [label_map_talk.get(lbl, lbl) for lbl in counts.index]
    percent = 100 * counts / counts.sum() if counts.sum() > 0 else pd.Series(dtype=float)
    return percent.sort_values(ascending=False)

support_talk_percent = get_talk_percentages(support_hub_df)
ilt_talk_percent     = get_talk_percentages(ilt_df)

# FOCUS AREAS – declare once at top so all sections can use it
focus_columns = {
    "Staying on pace in the curriculum":                        "Curriculum Pacing",
    "Using the curriculum with integrity":                       "Curricular Integrity",
    "Standards-aligned and/or grade-appropriate content":        "Standards-Aligned, Grade-Appropriate Content",
    "Addressing the specific needs of marginalized learners":     "Marginalized Learners"
}

response_order = [
    "A great deal of focus",
    "A minor focus",
    "Some focus",
    "Not a focus"
]

bar_colors = [
    "#4E79A7",  # blue  → A great deal of focus
    "#F28E2B",  # orange → A minor focus
    "#59A14F",  # green → Some focus
    "#E15759"   # red   → Not a focus
]

# ─────────────────────────────────────────────────────────────────────────────
# 2) OVERALL “Purpose of Walkthroughs” – Donuts
# ─────────────────────────────────────────────────────────────────────────────

st.header("Overall: Purpose of Walkthroughs (SH vs ILT)")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Support Hub (SH)")
    plot_donut_chart(support_percent, "Support Hub: Purpose", [
        "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#EDC948", "#B07AA1"
    ])
with col2:
    st.subheader("ILT")
    plot_donut_chart(ilt_percent, "ILT: Purpose", [
        "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#EDC948", "#B07AA1"
    ])

# ─────────────────────────────────────────────────────────────────────────────
# 3) OVERALL “Who Talked the Most” – Donuts
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Overall: Who Talked the Most During Debrief Conversations")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Support Hub (SH)")
    plot_donut_chart(support_talk_percent, "Support Hub: Who Talked Most", [
        "#B07AA1", "#59A14F", "#F28E2B", "#4E79A7"
    ])
with col2:
    st.subheader("ILT")
    plot_donut_chart(ilt_talk_percent, "ILT: Who Talked Most", [
        "#B07AA1", "#59A14F", "#F28E2B", "#4E79A7"
    ])

# ─────────────────────────────────────────────────────────────────────────────
# 4) OVERALL “Focus Areas” – Grouped Stacked Bars (ILT vs SH)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Overall: Focus Areas of the Debrief Conversation (by Affiliation)")

focus_keys   = list(focus_columns.keys())
focus_labels = list(focus_columns.values())
n_focus      = len(focus_keys)
n_resp       = len(response_order)

# Build ILT_data and SH_data (n_focus × n_resp)
df_focus_all = df.dropna(subset=["Affiliation"] + focus_keys)

ILT_data = np.zeros((n_focus, n_resp))
SH_data  = np.zeros((n_focus, n_resp))

for i, raw_col in enumerate(focus_keys):
    ilt_subset = df_focus_all[df_focus_all["Affiliation"] == "ILT"]
    ilt_dist   = (
        ilt_subset[raw_col]
        .value_counts(normalize=True)
        .reindex(response_order, fill_value=0)
        .values
        * 100
    )
    ILT_data[i, :] = ilt_dist

    sh_subset = df_focus_all[df_focus_all["Affiliation"] == "SH"]
    sh_dist   = (
        sh_subset[raw_col]
        .value_counts(normalize=True)
        .reindex(response_order, fill_value=0)
        .values
        * 100
    )
    SH_data[i, :] = sh_dist

fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(n_focus)
bar_width = 0.35
ax.set_ylim(-10, 100)

bottom_ilt = np.zeros(n_focus)
bottom_sh  = np.zeros(n_focus)

for j in range(n_resp):
    ax.bar(
        x - bar_width / 2,
        ILT_data[:, j],
        bar_width,
        bottom=bottom_ilt,
        color=bar_colors[j],
        edgecolor="white"
    )
    ax.bar(
        x + bar_width / 2,
        SH_data[:, j],
        bar_width,
        bottom=bottom_sh,
        color=bar_colors[j],
        edgecolor="white"
    )
    bottom_ilt += ILT_data[:, j]
    bottom_sh  += SH_data[:, j]

ax.set_ylabel("% of respondents", fontsize=11)
ax.set_title("By affiliation, focus of the debrief conversation", fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(focus_labels, rotation=20, ha="right", fontsize=10)

# Place ILT/SH labels below each bar
for i in range(n_focus):
    ax.text(
        x[i] - bar_width / 2,
        -5,
        "ILT",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold"
    )
    ax.text(
        x[i] + bar_width / 2,
        -5,
        "SH",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold"
    )

legend_handles = [plt.Rectangle((0, 0), 1, 1, color=bar_colors[k]) for k in range(n_resp)]
ax.legend(
    legend_handles,
    response_order,
    title="Level of Focus",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    fontsize=9
)
ax.yaxis.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
st.pyplot(fig)

# ─────────────────────────────────────────────────────────────────────────────
# 5) SCHOOL‐LEVEL BREAKDOWN (Support Hub vs ILT by School)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("School‐Level Breakdown: Support Hub vs ILT")

if "School Name" not in df.columns:
    st.error("❌ The CSV does not contain a “School Name” column.")
    st.stop()

school_list = sorted(df["School Name"].dropna().unique())
if len(school_list) == 0:
    st.warning("⚠️ No non‐null values found under “School Name”.")
    st.stop()

selected_school = st.selectbox("Select a school:", school_list)
school_df = df[df["School Name"] == selected_school]

st.subheader(f"Breakdown for: {selected_school}")

# --- 5a) Purpose of Walkthroughs at this School ---
st.markdown("**Purpose of Walkthroughs (SH vs ILT at this school)**")

school_sh  = school_df[school_df["Affiliation"] == "SH"]
school_ilt = school_df[school_df["Affiliation"] == "ILT"]

school_support_counts = (school_sh[purpose_columns] == "Checked").sum()
school_ilt_counts     = (school_ilt[purpose_columns] == "Checked").sum()

school_support_counts.index = cleaned_purpose_cols
school_ilt_counts.index     = cleaned_purpose_cols

school_support_percent = (
    100 * school_support_counts / school_support_counts.sum()
    if school_support_counts.sum() > 0
    else pd.Series(dtype=float)
)
school_ilt_percent = (
    100 * school_ilt_counts / school_ilt_counts.sum()
    if school_ilt_counts.sum() > 0
    else pd.Series(dtype=float)
)

school_support_percent = school_support_percent.sort_values(ascending=False)
school_ilt_percent     = school_ilt_percent.sort_values(ascending=False)

col1, col2 = st.columns(2)
with col1:
    st.write("**Support Hub (SH)**")
    if not school_support_percent.empty:
        plot_donut_chart(
            school_support_percent,
            f"{selected_school} – SH: Purpose",
            ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#EDC948", "#B07AA1"]
        )
    else:
        st.info("No SH responses for this school.")

with col2:
    st.write("**ILT**")
    if not school_ilt_percent.empty:
        plot_donut_chart(
            school_ilt_percent,
            f"{selected_school} – ILT: Purpose",
            ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#EDC948", "#B07AA1"]
        )
    else:
        st.info("No ILT responses for this school.")

# --- 5b) Who Talked the Most at this school ---
st.markdown("---")
st.subheader("Who Talked the Most During Debrief (SH vs ILT, by school)")

school_support_talk = get_talk_percentages(school_sh)
school_ilt_talk     = get_talk_percentages(school_ilt)

col1, col2 = st.columns(2)
with col1:
    st.write("**Support Hub (SH)**")
    if not school_support_talk.empty:
        plot_donut_chart(
            school_support_talk,
            f"{selected_school} – SH: Who Talked Most",
            ["#B07AA1", "#59A14F", "#F28E2B", "#4E79A7"]
        )
    else:
        st.info("No SH “who talked” data for this school.")

with col2:
    st.write("**ILT**")
    if not school_ilt_talk.empty:
        plot_donut_chart(
            school_ilt_talk,
            f"{selected_school} – ILT: Who Talked Most",
            ["#B07AA1", "#59A14F", "#F28E2B", "#4E79A7"]
        )
    else:
        st.info("No ILT “who talked” data for this school.")

# ─────────────────────────────────────────────────────────────────────────────
# 5c) Focus Areas at this school – Grouped Stacked Bars (ILT vs SH)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Focus Areas of Debrief (SH vs ILT, by school)")

df_focus_school = school_df.dropna(subset=["Affiliation"] + list(focus_columns.keys()))

focus_keys   = list(focus_columns.keys())
focus_labels = list(focus_columns.values())
n_focus      = len(focus_keys)
n_resp       = len(response_order)

ILT_school_data = np.zeros((n_focus, n_resp))
SH_school_data  = np.zeros((n_focus, n_resp))

for i, raw_col in enumerate(focus_keys):
    ilt_subset = df_focus_school[df_focus_school["Affiliation"] == "ILT"]
    ilt_dist   = (
        ilt_subset[raw_col]
        .value_counts(normalize=True)
        .reindex(response_order, fill_value=0)
        .values
        * 100
    )
    ILT_school_data[i, :] = ilt_dist

    sh_subset = df_focus_school[df_focus_school["Affiliation"] == "SH"]
    sh_dist   = (
        sh_subset[raw_col]
        .value_counts(normalize=True)
        .reindex(response_order, fill_value=0)
        .values
        * 100
    )
    SH_school_data[i, :] = sh_dist

fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(n_focus)
bar_width = 0.35
ax.set_ylim(-10, 100)

bottom_ilt = np.zeros(n_focus)
bottom_sh  = np.zeros(n_focus)

for j in range(n_resp):
    ax.bar(
        x - bar_width / 2,
        ILT_school_data[:, j],
        bar_width,
        bottom=bottom_ilt,
        color=bar_colors[j],
        edgecolor="white"
    )
    ax.bar(
        x + bar_width / 2,
        SH_school_data[:, j],
        bar_width,
        bottom=bottom_sh,
        color=bar_colors[j],
        edgecolor="white"
    )
    bottom_ilt += ILT_school_data[:, j]
    bottom_sh  += SH_school_data[:, j]

ax.set_ylabel("% of respondents", fontsize=11)
ax.set_title(f"{selected_school} – Focus Areas (SH vs ILT)", fontsize=13)

for i in range(n_focus):
    ax.text(
        x[i] - bar_width / 2,
        -5,
        "ILT",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold"
    )
    ax.text(
        x[i] + bar_width / 2,
        -5,
        "SH",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold"
    )

ax.set_xticks(x)
ax.set_xticklabels(focus_labels, rotation=20, ha="right", fontsize=9)

legend_handles = [plt.Rectangle((0, 0), 1, 1, color=bar_colors[k]) for k in range(n_resp)]
ax.legend(
    legend_handles,
    response_order,
    title="Level of Focus",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    fontsize=8
)

ax.yaxis.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
st.pyplot(fig)
