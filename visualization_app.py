import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
# Helper functions (for donut plots, etc.)
# ─────────────────────────────────────────────────────────────────────────────

def custom_autopct(pct: float) -> str:
    """Only show the percentage label if it's > 1%."""
    return f"{pct:.1f}%" if pct > 1 else ""

def plot_donut_chart(percent_series: pd.Series, title: str, color_list: list):
    """
    Draws a donut‐style pie chart. 
    - percent_series: pd.Series whose index are labels and whose values are percentages
    - color_list: a list of hex‐colors; length must be ≥ len(percent_series)
    """
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

def get_talk_percentages(df_subset: pd.DataFrame, talk_column: str, label_map_talk: dict) -> pd.Series:
    """
    For a given subset DataFrame, count occurrences in talk_column,
    remap each raw label via label_map_talk, then convert to percentage
    and sort descending.
    """
    counts = df_subset[talk_column].value_counts()
    counts.index = [label_map_talk.get(lbl, lbl) for lbl in counts.index]
    percent = 100 * counts / counts.sum() if counts.sum() > 0 else pd.Series(dtype=float)
    return percent.sort_values(ascending=False)

# ─────────────────────────────────────────────────────────────────────────────
# Streamlit layout begins
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Walkthrough Perspectives Dashboard", layout="wide")
st.title("Walkthrough Perspectives Dashboard")

uploaded_file = st.file_uploader("Upload the CSV file", type=["csv"])
if uploaded_file is None:
    st.info("📄 Please upload your CSV to proceed.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 1) LOAD & PREPARE
# ─────────────────────────────────────────────────────────────────────────────

df = pd.read_csv(uploaded_file)

# Clean up affiliation text & map to “ILT” or “SH”
df["Your affiliation:"] = df["Your affiliation:"].astype(str).str.strip()
df["Affiliation"] = df["Your affiliation:"].map({
    "This school's ILT": "ILT",
    "MNPS Support Hub":     "SH"
})

# Many of our “purpose” columns embed a long choice string inside parentheses.
# We replace each with a shorter label:
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
    """
    If colname contains “(choice=LONG TEXT)”, replace it with the short label.
    Otherwise just return colname unchanged.
    """
    for long_text, short_text in label_mapping.items():
        if f"(choice={long_text})" in colname:
            return short_text
    return colname

# Identify all “purpose” columns (they all start with the same prefix)
purpose_columns = [
    col for col in df.columns
    if col.startswith("The purpose of this walkthrough was to:")
]

# Create a copy with cleaned column names
cleaned_purpose_cols = [clean_column_name(c) for c in purpose_columns]
df_purposes = df[purpose_columns].copy()
df_purposes.columns = cleaned_purpose_cols

# Split into Support Hub vs. ILT
support_hub_df = df[df["Affiliation"] == "SH"]
ilt_df        = df[df["Affiliation"] == "ILT"]

# Count “Checked” in each purpose‐column
support_counts = (support_hub_df[purpose_columns] == "Checked").sum()
ilt_counts     = (ilt_df[ purpose_columns] == "Checked").sum()

# Remap their indexes to the cleaned column names
support_counts.index = cleaned_purpose_cols
ilt_counts.index     = cleaned_purpose_cols

# Convert to % of total “Checked” in that group
support_percent = 100 * support_counts / support_counts.sum() if support_counts.sum() > 0 else pd.Series(dtype=float)
ilt_percent     = 100 * ilt_counts     / ilt_counts.sum()     if ilt_counts.sum()     > 0 else pd.Series(dtype=float)

# Sort descending so largest slices appear first
support_percent = support_percent.sort_values(ascending=False)
ilt_percent     = ilt_percent.sort_values(ascending=False)

# ─────────────────────────────────────────────────────────────────────────────
# 2) OVERALL SH vs. ILT – DONUTS
# ─────────────────────────────────────────────────────────────────────────────

st.header("Overall: Purpose of Walkthroughs")
st.markdown("Support Hub vs ILT (all schools combined)")

# Pick 7 distinct hex‐colors (one for each possible “purpose” category)
purpose_colors = [
    "#4E79A7",  # blue
    "#F28E2B",  # orange
    "#E15759",  # red
    "#76B7B2",  # teal
    "#59A14F",  # green
    "#EDC948",  # yellow
    "#B07AA1"   # purple
]

col1, col2 = st.columns(2)
with col1:
    st.subheader("Support Hub (SH)")
    plot_donut_chart(
        support_percent,
        "Support Hub perspectives\non the purpose of walkthroughs",
        purpose_colors
    )

with col2:
    st.subheader("ILT")
    plot_donut_chart(
        ilt_percent,
        "ILT perspectives\non the purpose of walkthroughs",
        purpose_colors
    )

# ─────────────────────────────────────────────────────────────────────────────
# 3) OVERALL “Who Talked the Most” – DONUTS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Overall: Who Talked the Most During Debrief Conversations")

talk_column = "Who talked the most during the debrief conversation?"
label_map_talk = {
    "No one person spoke significantly more than others": "No single dominant voice",
    "Other SH Members":  "Other SH Members",
    "Other ILT Members": "Other ILT Members",
    "The executive director(s)": "The Executive Director"
}

support_talk_percent = get_talk_percentages(support_hub_df, talk_column, label_map_talk)
ilt_talk_percent     = get_talk_percentages(ilt_df,        talk_column, label_map_talk)

# Choose 4 contrasting hex colors for up to 4 slices
talk_colors = [
    "#B07AA1",  # purple
    "#59A14F",  # green
    "#F28E2B",  # orange
    "#4E79A7"   # blue
]

col1, col2 = st.columns(2)
with col1:
    st.subheader("Support Hub (SH)")
    plot_donut_chart(
        support_talk_percent,
        "Support Hub perspectives\non who talked the most",
        talk_colors
    )
with col2:
    st.subheader("ILT")
    plot_donut_chart(
        ilt_talk_percent,
        "ILT perspectives\non who talked the most",
        talk_colors
    )

# ─────────────────────────────────────────────────────────────────────────────
# 4) OVERALL “Focus Areas” – Grouped Stacked Bars (ILT vs SH)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Overall: Focus Areas of the Debrief Conversation (by Affiliation)")

# Define the raw focus‐column keys (those in the CSV) and their short labels:
focus_columns = {
    "Staying on pace in the curriculum":                        "Curriculum Pacing",
    "Using the curriculum with integrity":                       "Curricular Integrity",
    "Standards-aligned and/or grade-appropriate content":        "Standards-Aligned, Grade-Appropriate Content",
    "Addressing the specific needs of marginalized learners":     "Marginalized Learners"
}

# The exact order in which we want to stack the four response‐levels:
response_order = [
    "A great deal of focus",
    "A minor focus",
    "Some focus",
    "Not a focus"
]

# Choose four clearly distinct hex‐colors—one per response level.
bar_colors = [
    "#4E79A7",  # blue  → A great deal of focus
    "#F28E2B",  # orange → A minor focus
    "#59A14F",  # green → Some focus
    "#E15759"   # red   → Not a focus
]

# Drop any rows that are missing affiliation or any of the focus‐columns
df_focus = df.dropna(subset=["Affiliation"] + list(focus_columns.keys()))

# We will build two (n_focus × n_resp) arrays: one for ILT, one for SH.
focus_keys   = list(focus_columns.keys())
focus_labels = list(focus_columns.values())
n_focus      = len(focus_keys)
n_resp       = len(response_order)

# Initialize empty arrays
ILT_data = np.zeros((n_focus, n_resp))
SH_data  = np.zeros((n_focus, n_resp))

# Populate ILT_data and SH_data:
for i, raw_col in enumerate(focus_keys):
    # ILT subset for this raw_col
    ilt_subset = df_focus[df_focus["Affiliation"] == "ILT"]
    ilt_dist   = (
        ilt_subset[raw_col]
        .value_counts(normalize=True)
        .reindex(response_order, fill_value=0)
        .values
        * 100
    )  # multiply by 100 to get percentages
    ILT_data[i, :] = ilt_dist

    # SH subset for this raw_col
    sh_subset = df_focus[df_focus["Affiliation"] == "SH"]
    sh_dist   = (
        sh_subset[raw_col]
        .value_counts(normalize=True)
        .reindex(response_order, fill_value=0)
        .values
        * 100
    )
    SH_data[i, :] = sh_dist

# Now we have:
#   ILT_data[i, j] = % of ILT respondents who said response_order[j] for focus_keys[i]
#   SH_data[i, j]  = % of SH respondents who said response_order[j] for focus_keys[i]

# Create a grouped, side‐by‐side stacked bar plot:

fig, ax = plt.subplots(figsize=(12, 6))

# X‐axis positions for each focus area (we will offset ILT vs SH by half the bar‐width)
x = np.arange(n_focus)
bar_width = 0.35

# Keep track of “bottom” for stacking within each bar
bottom_ilt = np.zeros(n_focus)
bottom_sh  = np.zeros(n_focus)

# For each response level, draw the ILT bars (x - width/2) and SH bars (x + width/2)
for j, response_label in enumerate(response_order):
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

    # Update bottoms for next iteration
    bottom_ilt += ilt_vals
    bottom_sh  += sh_vals

# Final styling:
ax.set_ylabel("% of respondents", fontsize=11)
ax.set_ylim(0, 100)
ax.set_title("By affiliation, focus of the debrief conversation", fontsize=14)

# X‐axis: label each group (focus area) in the center
ax.set_xticks(x)
ax.set_xticklabels(focus_labels, rotation=20, ha="right", fontsize=10)

# Add a custom legend that maps colors → response_order
legend_handles = [
    plt.Rectangle((0, 0), 1, 1, color=bar_colors[k])
    for k in range(n_resp)
]
ax.legend(
    legend_handles,
    response_order,
    title="Level of Focus",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    fontsize=9
)

# Add subtle gridlines for readability
ax.yaxis.grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
st.pyplot(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 5) SCHOOL‐LEVEL BREAKDOWN
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("School‐Level Breakdown: Support Hub vs ILT")

# We'll use the “School Name” column as the site indicator:
if "School Name" not in df.columns:
    st.error("❌ The CSV does not contain a “School Name” column.")
    st.stop()

# Build a sorted list of unique schools (non‐null).
school_list = sorted(df["School Name"].dropna().unique())
if len(school_list) == 0:
    st.warning("⚠️ No non‐null values found under “School Name”.")
    st.stop()

# Let the user pick exactly one school to compare SH vs ILT
selected_school = st.selectbox("Select a school:", school_list)

# Filter to that school only
school_df = df[df["School Name"] == selected_school]

st.subheader(f"Breakdown for: {selected_school}")

# --- 5a) PURPOSE OF WALKTHROUGHS at this School ---
st.markdown("**Purpose of Walkthroughs (SH vs ILT at this school)**")

# Split again by affiliation, but only within this school
school_sh = school_df[school_df["Affiliation"] == "SH"]
school_ilt = school_df[school_df["Affiliation"] == "ILT"]

# Re‐compute “Checked” counts at school level
school_support_counts = (school_sh[purpose_columns] == "Checked").sum()
school_ilt_counts     = (school_ilt[purpose_columns] == "Checked").sum()

# Remap indices to cleaned column names
school_support_counts.index = cleaned_purpose_cols
school_ilt_counts.index     = cleaned_purpose_cols

# Convert to percentages (if group has any rows)
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

# Sort descending
school_support_percent = school_support_percent.sort_values(ascending=False)
school_ilt_percent     = school_ilt_percent.sort_values(ascending=False)

col1, col2 = st.columns(2)
with col1:
    st.write("**Support Hub (SH)**")
    if not school_support_percent.empty:
        plot_donut_chart(
            school_support_percent,
            f"{selected_school} – SH: Purpose",
            purpose_colors
        )
    else:
        st.info("No SH responses for this school.")

with col2:
    st.write("**ILT**")
    if not school_ilt_percent.empty:
        plot_donut_chart(
            school_ilt_percent,
            f"{selected_school} – ILT: Purpose",
            purpose_colors
        )
    else:
        st.info("No ILT responses for this school.")

# --- 5b) WHO TALKED THE MOST at this school ---
st.markdown("---")
st.subheader("Who Talked the Most During Debrief (SH vs ILT, by school)")

school_support_talk = get_talk_percentages(school_sh, talk_column, label_map_talk)
school_ilt_talk     = get_talk_percentages(school_ilt, talk_column, label_map_talk)

col1, col2 = st.columns(2)
with col1:
    st.write("**Support Hub (SH)**")
    if not school_support_talk.empty:
        plot_donut_chart(
            school_support_talk,
            f"{selected_school} – SH: Who Talked Most",
            talk_colors
        )
    else:
        st.info("No SH “who talked” data for this school.")

with col2:
    st.write("**ILT**")
    if not school_ilt_talk.empty:
        plot_donut_chart(
            school_ilt_talk,
            f"{selected_school} – ILT: Who Talked Most",
            talk_colors
        )
    else:
        st.info("No ILT “who talked” data for this school.")

# --- 5c) FOCUS AREAS at this school (stacked bar) ---
st.markdown("---")
st.subheader("Focus Areas of Debrief (SH vs ILT, by school)")

# We can re‐use the same focus_columns & response_order from above
df_focus_school = school_df.dropna(subset=["Affiliation"] + list(focus_columns.keys()))

# Build stacked data for this school
stacked_school = {}
for raw_col, label in focus_columns.items():
    # SH sub‐group
    sh_subset = df_focus_school[df_focus_school["Affiliation"] == "SH"]
    sh_dist = sh_subset[raw_col].value_counts(normalize=True).reindex(response_order, fill_value=0)
    stacked_school[f"SH: {label}"] = sh_dist

    # ILT sub‐group
    ilt_subset = df_focus_school[df_focus_school["Affiliation"] == "ILT"]
    ilt_dist = ilt_subset[raw_col].value_counts(normalize=True).reindex(response_order, fill_value=0)
    stacked_school[f"ILT: {label}"] = ilt_dist

stacked_school_df = pd.DataFrame(stacked_school).T[response_order]

fig, ax = plt.subplots(figsize=(10, 5))
bottom = [0] * len(stacked_school_df.index)
for i, resp in enumerate(response_order):
    heights = stacked_school_df[resp] * 100
    ax.bar(
        stacked_school_df.index,
        heights,
        bottom=bottom,
        label=resp,
        color=bar_colors[i]
    )
    bottom = [sum(pair) for pair in zip(bottom, heights)]

ax.set_ylabel("%", fontsize=11)
ax.set_ylim(0, 100)
ax.set_title(f"{selected_school} – Focus Areas (SH vs ILT)", fontsize=13)
plt.xticks(rotation=45, ha="right", fontsize=8)
ax.legend(
    title="Level of Focus",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    fontsize=8
)
plt.tight_layout()
st.pyplot(fig)
