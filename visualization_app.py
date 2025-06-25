import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Walkthrough Survey Data Analysis Dashboard", layout="centered")

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

# Rename specific school names for display:
school_name_map = {
    "Cane Ridge":  "School B",
    "Hillsboro":   "School E",
    "Maplewood":   "School F"
}
df["School Name"] = df["School Name"].replace(school_name_map)

# Clean “Your affiliation:” and map to ILT vs SH
df["Your affiliation:"] = df["Your affiliation:"].astype(str).str.strip()

# Standardize affiliation and talk response labels
talk_col = "Who talked the most during the debrief conversation?"

# Corrected talk_label_map: keys should be the raw values from the column
# and values are the standardized labels you want to use.
talk_label_map = {
    "No one person spoke significantly more than others": "No one person spoke significantly more",
    "Other ILT members (not the executive principal)": "Other ILT members",
    "Other support hub members (not EDs)": "Other Support Hub members",
    "The executive director(s)": "The executive director"
}

df["Affiliation"] = df["Your affiliation:"].map({
    "MNPS Support Hub": "SH",
    "This school's ILT": "ILT"
})

# ✅ CORRECT mapping from actual talk column
# Apply the mapping to create the 'TalkLabel' column
df["TalkLabel"] = df[talk_col].map(talk_label_map)


# ─────────────────────────────────────────────────────────────────────────────
# PURPOSE OF WALKTHROUGHS – identify & clean those columns
# ─────────────────────────────────────────────────────────────────────────────

label_mapping = {
    "Identify areas for instructional improvement for the math or ELA team at this school":
        "Identify areas for instructional improvement",
    "Identify needed professional learning supports regarding math or ELA teaching":
        "Identify needed professional learning supports",
    "Sharpen our eye for quality math or ELA instruction":
        "Sharpen our eye for quality instruction",
    "Monitor progress on this schools theory of action":  # Note: no apostrophe in "schools"
        "Monitor progress on this school's theory of action",
    "Identify additional supports to enhance curriculum implementation":
        "Identify additional curricular implementation supports",
    "Provide feedback to individual teachers on their instructional quality":
        "Provide feedback to individual teachers",
    "Evaluate individual teacher competence":
        "Evaluate individual teacher competence"
}


def clean_column_name(colname: str) -> str:
    for long_text, short_text in label_mapping.items():
        if long_text in colname:
            return short_text
    return colname


purpose_columns = [
    col for col in df.columns
    if col.startswith("The purpose of this walkthrough was to:")
]
cleaned_purpose_cols = [clean_column_name(c) for c in purpose_columns]


purpose_color_map = {
    "Identify areas for instructional improvement":              "#4E79A7",  # blue
    "Identify needed professional learning supports":             "#F28E2B",  # orange
    "Sharpen our eye for quality instruction":                    "#E15759",  # red
    "Monitor progress on this school's theory of action":         "#76B7B2",  # teal
    "Identify additional curricular implementation supports":     "#59A14F",  # green
    "Provide feedback to individual teachers":                     "#EDC948",  # yellow
    "Evaluate individual teacher competence":                      "#B07AA1"   # purple
}

def custom_autopct(pct: float) -> str:
    return f"{pct:.1f}%" if pct > 1 else ""

def plot_donut_fixed_colors(
    percent_series: pd.Series,
    title: str,
    color_map: dict
):
    # Sort values descending so the largest slice starts at top (clockwise)
    percent_series = percent_series.sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(5, 5))
    labels = percent_series.index.tolist()
    values = percent_series.values
    colors = [color_map.get(label, "#cccccc") for label in labels]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        autopct=custom_autopct,
        startangle=90,
        counterclock=False,
        colors=colors,
        wedgeprops=dict(width=0.3)
    )
    for autotext in autotexts:
        autotext.set_fontsize(8)

    ax.axis("equal")
    ax.set_title(title, pad=20)
    ax.legend(
        wedges,
        labels,
        title="Legend",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=8
    )
    st.pyplot(fig)


support_hub_df = df[df["Affiliation"] == "SH"]
ilt_df        = df[df["Affiliation"] == "ILT"]

support_counts = (support_hub_df[purpose_columns] == "Checked").sum()
ilt_counts     = (ilt_df[purpose_columns] == "Checked").sum()

support_counts.index = cleaned_purpose_cols
ilt_counts.index     = cleaned_purpose_cols

support_percent = (
    100 * support_counts / support_counts.sum()
    if support_counts.sum() > 0
    else pd.Series(dtype=float)
)
ilt_percent = (
    100 * ilt_counts / ilt_counts.sum()
    if ilt_counts.sum() > 0
    else pd.Series(dtype=float)
)

support_percent = support_percent.sort_index()
ilt_percent     = ilt_percent.sort_index()

# ─────────────────────────────────────────────────────────────────────────────
# 2) OVERALL “Purpose of Walkthroughs” – Donuts (fixed colors)
# ─────────────────────────────────────────────────────────────────────────────

st.header("Overall: Purpose of Walkthroughs (SH vs ILT)")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Support Hub (SH)")
    if not support_percent.empty:
        plot_donut_fixed_colors(
            support_percent,
            "Support Hub: Purpose of Walkthroughs",
            purpose_color_map
        )
    else:
        st.info("No Support Hub data to show.")
with col2:
    st.subheader("ILT")
    if not ilt_percent.empty:
        plot_donut_fixed_colors(
            ilt_percent,
            "ILT: Purpose of Walkthroughs",
            purpose_color_map
        )
    else:
        st.info("No ILT data to show.")

# ─────────────────────────────────────────────────────────────────────────────
# WHO TALKED THE MOST – define fixed color map
# ─────────────────────────────────────────────────────────────────────────────

talk_column = "Who talked the most during the debrief conversation?"

# The `talk_label_map` is already defined correctly for mapping raw data to `TalkLabel`
# We need `talk_color_map` keys to match the *values* in `TalkLabel`

talk_color_map = {
    "No one person spoke significantly more": "#4E79A7",  # blue
    "Other Support Hub members":          "#F28E2B",  # orange
    "Other ILT members":         "#59A14F",  # green
    "The executive director":    "#E15759"   # red
}


def get_talk_percentages(df_subset: pd.DataFrame) -> pd.Series:
    # Use the already mapped 'TalkLabel' column
    filtered = df_subset[df_subset["TalkLabel"].notna()]
    counts = filtered["TalkLabel"].value_counts()
    percent = 100 * counts / counts.sum() if counts.sum() > 0 else pd.Series(dtype=float)
    return percent.sort_values(ascending=False)


support_talk_percent = get_talk_percentages(support_hub_df)
ilt_talk_percent     = get_talk_percentages(ilt_df)

# ─────────────────────────────────────────────────────────────────────────────
# 3) OVERALL “Who Talked the Most” – Donuts (fixed colors)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Overall: Who Talked the Most During Debrief Conversations")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Support Hub (SH)")
    if not support_talk_percent.empty:
        plot_donut_fixed_colors(
            support_talk_percent,
            "Support Hub: Who Talked the Most",
            talk_color_map
        )
    else:
        st.info("No SH “who talked” data.")
with col2:
    st.subheader("ILT")
    if not ilt_talk_percent.empty:
        plot_donut_fixed_colors(
            ilt_talk_percent,
            "ILT: Who Talked the Most",
            talk_color_map
        )
    else:
        st.info("No ILT “who talked” data.")

# ─────────────────────────────────────────────────────────────────────────────
# FOCUS AREAS – declare once for overall and school‐level
# ─────────────────────────────────────────────────────────────────────────────

focus_columns = {
    "Staying on pace in the curriculum":                        "Curriculum Pacing",
    "Using the curriculum with integrity":                       "Curricular Integrity",
    "Standards-aligned and/or grade-appropriate content":        "Standards-Aligned, Grade-Appropriate Content",
    "Addressing the specific needs of marginalized learners":     "Marginalized Learners"
}

response_order = [
    "A great deal of focus",
    "A minor focus", # Changed from 'A minor focus' to 'Some focus' as per current mapping in the `plot_donut_fixed_colors` function
    "Some focus",
    "Not a focus"
]

bar_colors = [
    "#2F6130",  # dark green
    "#59A14F",  # base green
    "#85BC74",  # medium-light green
    "#A8D09C"   # light green
]


# ─────────────────────────────────────────────────────────────────────────────
# 4) OVERALL “Focus Areas” – Grouped Stacked Bars (ILT vs SH)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Overall: Focus Areas of the Debrief Conversation (by Affiliation)")

focus_keys   = list(focus_columns.keys())
focus_labels = list(focus_columns.values())
n_focus      = len(focus_keys)
n_resp       = len(response_order)

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

for j in reversed(range(n_resp)):
    ilt_vals = ILT_data[:, j]
    sh_vals  = SH_data[:,  j]
    ax.bar(
        x - bar_width / 2,
        ilt_vals,
        bar_width,
        bottom=bottom_ilt,
        color=bar_colors[j],
        edgecolor="white"
    )
    ax.bar(
        x + bar_width / 2,
        sh_vals,
        bar_width,
        bottom=bottom_sh,
        color=bar_colors[j],
        edgecolor="white"
    )
    bottom_ilt += ilt_vals
    bottom_sh  += sh_vals


ax.set_ylabel("% of respondents", fontsize=11)
ax.set_title("By affiliation, perceptions that the debrief conversation included a focus on:", fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(focus_labels, rotation=20, ha="right", fontsize=10)

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

# ─────────────────────────────────────────────────────────────────────────────
# 5a) Purpose of Walkthroughs at this School (fixed colors)
# ─────────────────────────────────────────────────────────────────────────────

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

school_support_percent = school_support_percent.sort_index()
school_ilt_percent     = school_ilt_percent.sort_index()

col1, col2 = st.columns(2)
with col1:
    st.write("**Support Hub (SH)**")
    if not school_support_percent.empty:
        plot_donut_fixed_colors(
            school_support_percent,
            f"{selected_school} – SH: Purpose of Walkthroughs",
            purpose_color_map
        )
    else:
        st.info("No SH responses for this school.")
with col2:
    st.write("**ILT**")
    if not school_ilt_percent.empty:
        plot_donut_fixed_colors(
            school_ilt_percent,
            f"{selected_school} – ILT: Purpose of Walkthroughs",
            purpose_color_map
        )
    else:
        st.info("No ILT responses for this school.")

# ─────────────────────────────────────────────────────────────────────────────
# 5b) Who Talked the Most at this school (fixed colors)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Who Talked the Most During Debrief (SH vs ILT, by school)")

school_support_talk = get_talk_percentages(school_sh)
school_ilt_talk     = get_talk_percentages(school_ilt)

col1, col2 = st.columns(2)
with col1:
    st.write("**Support Hub (SH)**")
    if not school_support_talk.empty:
        plot_donut_fixed_colors(
            school_support_talk,
            f"{selected_school} – SH: Who Talked the Most",
            talk_color_map
        )
    else:
        st.info("No SH “who talked” data for this school.")
with col2:
    st.write("**ILT**")
    if not school_ilt_talk.empty:
        plot_donut_fixed_colors(
            school_ilt_talk,
            f"{selected_school} – ILT: Who Talked the Most",
            talk_color_map
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

for j in reversed(range(n_resp)):
    # Corrected: use ILT_school_data and SH_school_data for school-level plot
    ilt_vals = ILT_school_data[:, j]
    sh_vals  = SH_school_data[:,  j]
    ax.bar(
        x - bar_width / 2,
        ilt_vals,
        bar_width,
        bottom=bottom_ilt,
        color=bar_colors[j],
        edgecolor="white"
    )
    ax.bar(
        x + bar_width / 2,
        sh_vals,
        bar_width,
        bottom=bottom_sh,
        color=bar_colors[j],
        edgecolor="white"
    )
    bottom_ilt += ilt_vals
    bottom_sh  += sh_vals


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


# ─────────────────────────────────────────────────────────────────────────────
# 6) LINE CHART – All Schools: Theory-of-Action Perception Over Time
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
with st.container():
    st.header("Trend: Debrief Felt Connected to the School's Theory of Action (All Schools Combined)")

    theory_col = "Today's debrief discussion felt connected to this school's theory of action"

    if all(col in df.columns for col in ["Date", theory_col]):
        # Updated Likert mapping including all observed values
        likert_map = {
            "Strongly disagree": 1,
            "Disagree": 2,
            "Neutral": 3,
            "Somewhat agree": 3, # Map 'Somewhat agree' to 3, assuming it's between Neutral and Agree
            "Slightly agree": 3, # Map 'Slightly agree' to 3, assuming it's between Neutral and Agree
            "Agree": 4,
            "Strongly agree": 5
        }

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["TheoryScore"] = df[theory_col].map(likert_map)

        df_valid = df.dropna(subset=["Date", "TheoryScore"]).copy()
        df_valid["Date"] = df_valid["Date"].dt.date

        # Group and calculate average
        trend_all = (
            df_valid.groupby("Date")["TheoryScore"]
            .mean()
            .reset_index()
            .rename(columns={"TheoryScore": "AvgScore"})
        )

        if trend_all.empty:
            st.info("📉 No valid data found to plot the trend.")
        else:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(trend_all["Date"], trend_all["AvgScore"], marker="o", linewidth=3, color="#126782")

            ax.set_title("All Schools – Avg Agreement: Debrief Connected to School's Theory of Action", fontsize=12)
            ax.set_ylabel("Average Agreement (1–5)")
            ax.set_ylim(3, 5)
            ax.grid(True, linestyle="--", alpha=0.5)

            ax.set_xticks(trend_all["Date"])
            ax.set_xticklabels(
                 [d.strftime("%#m/%#d/%Y") for d in trend_all["Date"]],
                  rotation=45,
                 ha="right"
                )


            plt.tight_layout()
            st.pyplot(fig)
    else:
        st.info("❗ Required data not found to generate theory-of-action trend chart.")


# ─────────────────────────────────────────────────────────────────────────────
# 7) DONUT CHART – Purpose of Walkthrough (All Schools Combined)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Purpose of Walkthroughs (All Schools Combined)")

# Identify relevant columns
purpose_columns = [
    col for col in df.columns
    if col.startswith("The purpose of this walkthrough was to:")
]

# Clean labels for readability (using the already defined label_mapping)
# Re-using the clean_column_name function for consistency
# Make sure purpose_label_map is consistent with label_mapping if it's meant to be the same.
# For now, I'll use the existing `label_mapping` that was correctly applied for `cleaned_purpose_cols`.


# Prepare counts across all schools
purpose_counts_all = (df[purpose_columns] == "Checked").sum()
purpose_counts_all.index = [clean_column_name(c) for c in purpose_columns] # Use existing clean_column_name
purpose_counts_all = purpose_counts_all.sort_values(ascending=False)

# Filter out zero values (if any)
purpose_counts_all = purpose_counts_all[purpose_counts_all > 0]

# Define a consistent color map (using the already defined purpose_color_map)


# Plot donut
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 6))
labels = purpose_counts_all.index.tolist()
sizes = purpose_counts_all.values
colors = [purpose_color_map.get(label, "#cccccc") for label in labels] # Use purpose_color_map

wedges, texts, autotexts = ax.pie(
    sizes,
    labels=None,
    colors=colors,
    autopct=lambda pct: f"{pct:.1f}%" if pct > 2 else "",
    startangle=90,
    counterclock=False,
    wedgeprops=dict(width=0.3)
)

ax.axis("equal")
ax.set_title("Proportions of respondents who said the purpose of the walkthrough was...", pad=20)

ax.legend(
    wedges,
    labels,
    title="Purpose",
    loc="center left",
    bbox_to_anchor=(1, 0.5),
    fontsize=8
)

st.pyplot(fig)

# ─────────────────────────────────────────────────────────────────────────────
# DONUT CHART – Who Talked the Most During Debrief (All Schools, Actual Data)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Who Spoke the Most During the Debrief Conversation? (All Schools)")

talk_col = "Who talked the most during the debrief conversation?"


# Color mapping for donut (using the already defined talk_color_map)
# The keys in talk_color_map must match the *mapped* values in 'TalkLabel'


# Clean and count responses
# 'df_valid_talk' is not needed; 'df["TalkLabel"]' is already mapped.
talk_counts = df["TalkLabel"].value_counts()
labels = talk_counts.index.tolist()
sizes = talk_counts.values
colors = [talk_color_map.get(label, "#cccccc") for label in labels] # Use talk_color_map

# Plotting
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 6))
wedges, texts, autotexts = ax.pie(
    sizes,
    labels=None,
    colors=colors,
    autopct=lambda pct: f"{pct:.1f}%" if pct > 2 else "",
    startangle=90,
    counterclock=False,
    wedgeprops=dict(width=0.3)
)

ax.axis("equal")
ax.set_title("Who spoke the most during the debrief conversation?", pad=20)

ax.legend(
    wedges,
    labels,
    title="Speaker",
    loc="center left",
    bbox_to_anchor=(1, 0.5),
    fontsize=9
)

st.pyplot(fig)