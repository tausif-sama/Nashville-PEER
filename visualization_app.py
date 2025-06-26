import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Apply a modern Matplotlib style for better aesthetics across all plots
# 'seaborn-v0_8-darkgrid' provides a clean look with a grid
plt.style.use('seaborn-v0_8-darkgrid')

# ─────────────────────────────────────────────────────────────────────────────
# Streamlit Page Configuration
# Set page title, icon, and layout for a better user experience
st.set_page_config(
    page_title="Walkthrough Survey Data Analysis Dashboard",
    layout="centered", # 'wide' or 'centered'
    initial_sidebar_state="auto"
)

# Main title of the dashboard
st.title("Walkthrough Perspectives Dashboard")

# ─────────────────────────────────────────────────────────────────────────────
# File Upload Section
# Provides a clear call to action for the user to upload the data
uploaded_file = st.file_uploader("Upload your CSV file here", type=["csv"])
if uploaded_file is None:
    st.info("📄 Please upload your CSV file to populate the dashboard. You can find example data formats in the documentation.")
    st.stop() # Stop execution until a file is uploaded

# ─────────────────────────────────────────────────────────────────────────────
# 1) DATA LOADING & PREPARATION
# This section loads the CSV, renames schools, and standardizes affiliation/talk labels.
# ─────────────────────────────────────────────────────────────────────────────

df = pd.read_csv(uploaded_file)

# Rename specific school names for display consistency
school_name_map = {
    "Cane Ridge":   "School B",
    "Hillsboro":    "School E",
    "Maplewood":    "School F"
}
df["School Name"] = df["School Name"].replace(school_name_map)

# Clean "Your affiliation:" column and map to ILT vs SH
df["Your affiliation:"] = df["Your affiliation:"].astype(str).str.strip()

# Standardize affiliation labels
df["Affiliation"] = df["Your affiliation:"].map({
    "MNPS Support Hub": "SH",
    "This school's ILT": "ILT"
})

# Define the column for 'Who talked the most'
talk_col = "Who talked the most during the debrief conversation?"

# Corrected talk_label_map: keys are raw values, values are standardized labels
talk_label_map = {
    "No one person spoke significantly more than others": "No one person spoke significantly more",
    "Other ILT members (not the executive principal)": "Other ILT members",
    "Other support hub members (not EDs)": "Other Support Hub members",
    "The executive director(s)": "The executive director"
}

# Apply the mapping to create the 'TalkLabel' column
df["TalkLabel"] = df[talk_col].map(talk_label_map)

# ─────────────────────────────────────────────────────────────────────────────
# PURPOSE OF WALKTHROUGHS – identify & clean those columns
# This section defines mappings for cleaning column names related to walkthrough purposes.
# ─────────────────────────────────────────────────────────────────────────────

label_mapping = {
    "Identify areas for instructional improvement for the math or ELA team at this school":
        "Identify areas for instructional improvement",
    "Identify needed professional learning supports regarding math or ELA teaching":
        "Identify needed professional learning supports",
    "Sharpen our eye for quality math or ELA instruction":
        "Sharpen our eye for quality instruction",
    "Monitor progress on this schools theory of action":  # Note: no apostrophe in "schools" in raw data
        "Monitor progress on this school's theory of action",
    "Identify additional supports to enhance curriculum implementation":
        "Identify additional curricular implementation supports",
    "Provide feedback to individual teachers":
        "Provide feedback to individual teachers",
    "Evaluate individual teacher competence":
        "Evaluate individual teacher competence"
}

# Helper function to clean column names based on the label_mapping
def clean_column_name(colname: str) -> str:
    for long_text, short_text in label_mapping.items():
        if long_text in colname:
            return short_text
    return colname

# Identify all columns related to the purpose of walkthroughs
purpose_columns = [
    col for col in df.columns
    if col.startswith("The purpose of this walkthrough was to:")
]
# Clean the identified column names for display
cleaned_purpose_cols = [clean_column_name(c) for c in purpose_columns]

# Define a consistent color map for the 'Purpose of Walkthroughs' donut charts
purpose_color_map = {
    "Identify areas for instructional improvement":          "#4E79A7",  # blue
    "Identify needed professional learning supports":        "#F28E2B",  # orange
    "Sharpen our eye for quality instruction":               "#E15759",  # red
    "Monitor progress on this school's theory of action":    "#76B7B2",  # teal
    "Identify additional curricular implementation supports": "#59A14F",  # green
    "Provide feedback to individual teachers":               "#EDC948",  # yellow
    "Evaluate individual teacher competence":                "#B07AA1"   # purple
}

# Custom autopct function for donut charts to show percentages only if significant
def custom_autopct(pct: float) -> str:
    return f"{pct:.1f}%" if pct > 1 else ""

# Function to plot fixed-color donut charts
def plot_donut_fixed_colors(
    percent_series: pd.Series,
    title: str,
    color_map: dict
):
    # Sort values descending so the largest slice starts at top (clockwise)
    # This also ensures consistent ordering for colors if labels match color_map
    percent_series = percent_series.sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(5, 5)) # Slightly increased size for better visual
    labels = percent_series.index.tolist()
    values = percent_series.values
    # Get colors from the map, default to grey for any unmapped labels
    colors = [color_map.get(label, "#cccccc") for label in labels]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=None, # Labels are shown in the legend, not directly on slices
        autopct=custom_autopct,
        startangle=90,
        counterclock=False,
        colors=colors,
        wedgeprops=dict(width=0.3, edgecolor='white') # Added white edge for separation
    )
    # Adjust font size for autotexts (percentages)
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_color('black') # Ensure percentage text is readable

    ax.axis("equal") # Ensures the pie chart is circular
    ax.set_title(title, pad=20, fontsize=12, fontweight='bold') # Title styling
    # Place legend outside the chart for clarity
    ax.legend(
        wedges,
        labels,
        title="Legend",
        loc="center left",
        bbox_to_anchor=(1, 0.5), # Position relative to axis
        fontsize=8,
        title_fontsize=9,
        frameon=True, # Add a frame around the legend
        fancybox=True # Rounded corners for the legend box
    )
    st.pyplot(fig) # Display the plot in Streamlit
    plt.close(fig) # Close the figure to free up memory

# Filter dataframes by affiliation (Support Hub vs ILT)
support_hub_df = df[df["Affiliation"] == "SH"]
ilt_df          = df[df["Affiliation"] == "ILT"]

# Calculate counts for each purpose for Support Hub and ILT
support_counts = (support_hub_df[purpose_columns] == "Checked").sum()
ilt_counts     = (ilt_df[purpose_columns] == "Checked").sum()

# Reindex counts with cleaned column names
support_counts.index = cleaned_purpose_cols
ilt_counts.index     = cleaned_purpose_cols

# Calculate percentages, handling cases with no data to avoid division by zero
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

# Sort percentages by index for consistent ordering in plots
support_percent = support_percent.sort_index()
ilt_percent     = ilt_percent.sort_index()

# ─────────────────────────────────────────────────────────────────────────────
# 2) OVERALL “Purpose of Walkthroughs” – Donuts (fixed colors)
# Displays donut charts comparing Support Hub and ILT perspectives on walkthrough purposes.
# ─────────────────────────────────────────────────────────────────────────────

st.header("Overall: Purpose of Walkthroughs (SH vs ILT)")
st.markdown("Below are the overall perceptions of the purpose of walkthroughs, broken down by affiliation.")

col1, col2 = st.columns(2) # Use columns for side-by-side display
with col1:
    st.subheader("Support Hub (SH)")
    if not support_percent.empty:
        plot_donut_fixed_colors(
            support_percent,
            "Support Hub: Purpose of Walkthroughs",
            purpose_color_map
        )
    else:
        st.info("No Support Hub data available for this section.")
with col2:
    st.subheader("ILT")
    if not ilt_percent.empty:
        plot_donut_fixed_colors(
            ilt_percent,
            "ILT: Purpose of Walkthroughs",
            purpose_color_map
        )
    else:
        st.info("No ILT data available for this section.")

# ─────────────────────────────────────────────────────────────────────────────
# WHO TALKED THE MOST – define fixed color map
# Defines the color map for the "Who talked the most" donut charts.
# ─────────────────────────────────────────────────────────────────────────────

# The `talk_label_map` is already defined correctly for mapping raw data to `TalkLabel`
# We need `talk_color_map` keys to match the *values* in `TalkLabel`
talk_color_map = {
    "No one person spoke significantly more": "#4E79A7",  # blue
    "Other Support Hub members":              "#F28E2B",  # orange
    "Other ILT members":                      "#59A14F",  # green
    "The executive director":                 "#E15759"   # red
}

# Helper function to get percentages for "Who talked the most"
def get_talk_percentages(df_subset: pd.DataFrame) -> pd.Series:
    # Use the already mapped 'TalkLabel' column
    filtered = df_subset[df_subset["TalkLabel"].notna()]
    counts = filtered["TalkLabel"].value_counts()
    percent = 100 * counts / counts.sum() if counts.sum() > 0 else pd.Series(dtype=float)
    return percent.sort_values(ascending=False) # Sort for consistent pie chart ordering

# Calculate percentages for Support Hub and ILT
support_talk_percent = get_talk_percentages(support_hub_df)
ilt_talk_percent     = get_talk_percentages(ilt_df)

# ─────────────────────────────────────────────────────────────────────────────
# 3) OVERALL “Who Talked the Most” – Donuts (fixed colors)
# Displays donut charts showing who talked the most during debrief conversations.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---") # Visual separator
st.header("Overall: Who Talked the Most During Debrief Conversations")
st.markdown("This section illustrates the perceived distribution of conversation during debriefs, by affiliation.")

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
        st.info("No Support Hub data for 'who talked the most'.")
with col2:
    st.subheader("ILT")
    if not ilt_talk_percent.empty:
        plot_donut_fixed_colors(
            ilt_talk_percent,
            "ILT: Who Talked the Most",
            talk_color_map
        )
    else:
        st.info("No ILT data for 'who talked the most'.")

# ─────────────────────────────────────────────────────────────────────────────
# FOCUS AREAS – declare once for overall and school-level
# Defines column mappings and response order for "Focus Areas" questions.
# ─────────────────────────────────────────────────────────────────────────────

focus_columns = {
    "Staying on pace in the curriculum":                 "Curriculum Pacing",
    "Using the curriculum with integrity":               "Curricular Integrity",
    "Standards-aligned and/or grade-appropriate content": "Standards-Aligned, Grade-Appropriate Content",
    "Addressing the specific needs of marginalized learners": "Marginalized Learners"
}

# Define the order of responses for stacked bar charts (Likert scale)
response_order = [
    "A great deal of focus",
    "Some focus",
    "A minor focus",
    "Not a focus"
]

# Define a color palette for the stacked bar charts (greens for focus levels)
bar_colors = [
    "#2F6130",  # dark green (A great deal of focus)
    "#59A14F",  # base green (Some focus)
    "#85BC74",  # medium-light green (A minor focus)
    "#A8D09C"   # light green (Not a focus)
]

# ─────────────────────────────────────────────────────────────────────────────
# 4) OVERALL “Focus Areas” – Grouped Stacked Bars (ILT vs SH)
# Displays stacked bar charts for focus areas, grouped by affiliation.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Overall: Focus Areas of the Debrief Conversation (by Affiliation)")
st.markdown("This chart shows the aggregated perception of what was focused on during debrief conversations, split by Support Hub and ILT members.")

focus_keys   = list(focus_columns.keys())
focus_labels = list(focus_columns.values())
n_focus      = len(focus_keys)
n_resp       = len(response_order)

# Drop rows where affiliation or any focus column data is missing
df_focus_all = df.dropna(subset=["Affiliation"] + focus_keys)

# Initialize arrays to hold percentage data for ILT and SH
ILT_data = np.zeros((n_focus, n_resp))
SH_data  = np.zeros((n_focus, n_resp))

# Populate the data arrays by calculating normalized value counts for each focus area
for i, raw_col in enumerate(focus_keys):
    ilt_subset = df_focus_all[df_focus_all["Affiliation"] == "ILT"]
    ilt_dist   = (
        ilt_subset[raw_col]
        .value_counts(normalize=True) # Get proportions
        .reindex(response_order, fill_value=0) # Ensure all responses are present, fill missing with 0
        .values
        * 100 # Convert to percentage
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

fig, ax = plt.subplots(figsize=(12, 6)) # Adjust figure size for better readability
x = np.arange(n_focus) # X-axis positions for the groups of bars
bar_width = 0.35 # Width of each individual bar
ax.set_ylim(-10, 100) # Set Y-axis limits (with a small negative for labels)

bottom_ilt = np.zeros(n_focus) # Tracks the cumulative height for ILT stacked bars
bottom_sh  = np.zeros(n_focus) # Tracks the cumulative height for SH stacked bars

# Loop in reverse order of responses for correct stacking (e.g., 'A great deal of focus' at the bottom)
for j in reversed(range(n_resp)):
    ilt_vals = ILT_data[:, j]
    sh_vals  = SH_data[:,  j]
    ax.bar(
        x - bar_width / 2, # Position for ILT bars (shifted left)
        ilt_vals,
        bar_width,
        bottom=bottom_ilt,
        color=bar_colors[j],
        edgecolor="white" # White border for separation
        # Removed problematic label argument
    )
    ax.bar(
        x + bar_width / 2, # Position for SH bars (shifted right)
        sh_vals,
        bar_width,
        bottom=bottom_sh,
        color=bar_colors[j],
        edgecolor="white"
    )
    bottom_ilt += ilt_vals # Update bottom for next stack
    bottom_sh  += sh_vals

ax.set_ylabel("% of respondents", fontsize=11)
ax.set_title("By affiliation, perceptions that the debrief conversation included a focus on:", fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x) # Set x-axis ticks at the center of each group
ax.set_xticklabels(focus_labels, rotation=20, ha="right", fontsize=10) # Rotate labels for readability

# Add "ILT" and "SH" labels below each pair of bars
for i in range(n_focus):
    ax.text(
        x[i] - bar_width / 2,
        -5, # Position below the bars
        "ILT",
        ha="center", va="center",
        fontsize=9, fontweight="bold", color='gray' # Styled for clarity
    )
    ax.text(
        x[i] + bar_width / 2,
        -5,
        "SH",
        ha="center", va="center",
        fontsize=9, fontweight="bold", color='gray'
    )

# Create custom legend handles for the stacked bar colors
legend_handles = [plt.Rectangle((0, 0), 1, 1, color=bar_colors[k]) for k in reversed(range(n_resp))] # Reversed for legend order
ax.legend(
    legend_handles,
    reversed(response_order), # Match legend order to stacking order
    title="Level of Focus",
    bbox_to_anchor=(1.02, 1), loc="upper left", # Position outside the plot
    fontsize=9, title_fontsize=10, frameon=True, fancybox=True
)
ax.yaxis.grid(True, linestyle="--", alpha=0.4) # Make grid lines subtle
plt.tight_layout() # Adjust layout to prevent labels from overlapping
st.pyplot(fig) # Display the plot
plt.close(fig) # Close the figure


# ─────────────────────────────────────────────────────────────────────────────
# 5) LINE CHART – All Schools: Theory-of-Action Perception Over Time
# Displays a trend line for agreement on debriefs being connected to the school's theory of action.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Trend: Debrief Felt Connected to the School's Theory of Action (All Schools Combined)")
st.markdown("This chart illustrates the average agreement over time that debrief discussions were connected to the school's theory of action across all schools.")

theory_col = "Today's debrief discussion felt connected to this school's theory of action"

if all(col in df.columns for col in ["Date", theory_col]):
    # Updated Likert mapping including all observed values and standardizing
    likert_map = {
        "Strongly disagree": 1,
        "Disagree": 2,
        "Neutral": 3,
        "Somewhat agree": 3, # Mapped to Neutral for simplification in numerical scale
        "Slightly agree": 3, # Mapped to Neutral for simplification in numerical scale
        "Agree": 4,
        "Strongly agree": 5
    }

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce") # Convert 'Date' to datetime objects
    df["TheoryScore"] = df[theory_col].map(likert_map) # Map Likert responses to numerical scores

    df_valid = df.dropna(subset=["Date", "TheoryScore"]).copy() # Drop rows with missing date or score
    df_valid["Date"] = df_valid["Date"].dt.date # Extract just the date part

    # Group by date and calculate the mean TheoryScore
    trend_all = (
        df_valid.groupby("Date")["TheoryScore"]
        .mean()
        .reset_index()
        .rename(columns={"TheoryScore": "AvgScore"})
    )

    if trend_all.empty:
        st.info("📉 No valid data found to plot the trend for 'Theory of Action' agreement.")
    else:
        fig, ax = plt.subplots(figsize=(10, 4)) # Adjust figure size

        ax.plot(trend_all["Date"], trend_all["AvgScore"], marker="o", linewidth=2.5, color="#126782", markersize=6) # Styled line plot

        ax.set_title("All Schools – Avg Agreement: Debrief Connected to School's Theory of Action", fontsize=12, fontweight='bold', pad=15)
        ax.set_ylabel("Average Agreement (1–5)", fontsize=10)
        ax.set_ylim(1, 5) # Set Y-axis from 1 to 5 for Likert scale consistency
        ax.grid(True, linestyle="--", alpha=0.5) # Subtle grid

        ax.set_xticks(trend_all["Date"]) # Set ticks at each unique date
        ax.set_xticklabels(
            [d.strftime("%#m/%#d/%Y") for d in trend_all["Date"]], # Format dates nicely
            rotation=45,
            ha="right",
            fontsize=9
        )
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
else:
    st.info("❗ Required columns ('Date' or 'Today's debrief discussion felt connected to this school's theory of action') not found to generate the theory-of-action trend chart.")


# ─────────────────────────────────────────────────────────────────────────────
# 6) DONUT CHART – Purpose of Walkthrough (All Schools Combined)
# Displays an overall donut chart for the purpose of walkthroughs across all schools.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Purpose of Walkthroughs (All Schools Combined)")
st.markdown("This chart provides an overall view of the most frequently cited purposes for walkthroughs across all surveyed individuals.")

# Identify relevant columns (already done above, reusing `purpose_columns`)

# Prepare counts across all schools
purpose_counts_all = (df[purpose_columns] == "Checked").sum()
purpose_counts_all.index = [clean_column_name(c) for c in purpose_columns] # Use existing clean_column_name
purpose_counts_all = purpose_counts_all.sort_values(ascending=False) # Sort for consistent donut ordering

# Filter out zero values (if any)
purpose_counts_all = purpose_counts_all[purpose_counts_all > 0]

# Plot donut (reusing the plot_donut_fixed_colors function)
if not purpose_counts_all.empty:
    plot_donut_fixed_colors(
        purpose_counts_all,
        "All Schools – Proportions of respondents who said the purpose of the walkthrough was...",
        purpose_color_map # Reuse the defined color map
    )
else:
    st.info("No data available for the overall purpose of walkthroughs.")


# ─────────────────────────────────────────────────────────────────────────────
# 7) DONUT CHART – Who Talked the Most During Debrief (All Schools, Actual Data)
# Displays an overall donut chart for who talked the most during debriefs across all schools.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Who Spoke the Most During the Debrief Conversation? (All Schools Combined)")
st.markdown("This chart summarizes the perceived primary speaker during debrief conversations across all affiliations and schools.")

# talk_col is already defined
# talk_color_map is already defined

# Clean and count responses using the already mapped 'TalkLabel' column
talk_counts_all = df["TalkLabel"].value_counts()

# Plotting (reusing plot_donut_fixed_colors function)
if not talk_counts_all.empty:
    plot_donut_fixed_colors(
        talk_counts_all,
        "All Schools – Who spoke the most during the debrief conversation?",
        talk_color_map # Reuse the defined color map
    )
else:
    st.info("No data available for 'who spoke the most' across all schools.")


# ─────────────────────────────────────────────────────────────────────────────
# 8) NEW: Line Chart – Agreement that Support Hub Staff Focused on Accountability
# Displays a trend line showing agreement on Support Hub staff's focus on accountability.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("Trend: Agreement that Support Hub Staff Focused on Accountability for Results")
st.markdown("This chart tracks how perceived agreement regarding the Support Hub's focus on accountability has changed over time, by affiliation.")

accountability_col = "Support hub staff were primarily focused on holding this school accountable for results"

if all(col in df.columns for col in ["Date", "Affiliation", accountability_col]):

    likert_map = {
        "Strongly disagree": 1,
        "Disagree": 2,
        "Neutral": 3,
        "Somewhat agree": 3,
        "Slightly agree": 3,
        "Agree": 4,
        "Strongly agree": 5,
        1: 1, 2: 2, 3: 3, 4: 4, 5: 5 # Ensure already coded numerical values are also handled
    }

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["AccountabilityScore"] = df[accountability_col].map(likert_map)
    df["DateOnly"] = df["Date"].dt.date # Extract date only for grouping

    # Drop missing values in the relevant columns
    trend_df = df.dropna(subset=["AccountabilityScore", "DateOnly", "Affiliation"])

    # Group by date and affiliation, then unstack to get 'ILT' and 'SH' as columns
    avg_scores = (
        trend_df.groupby(["DateOnly", "Affiliation"])["AccountabilityScore"]
        .mean()
        .unstack()
        .reset_index()
    )

    if avg_scores.empty:
        st.info("📉 No valid data available to display the accountability trend.")
    else:
        fig, ax = plt.subplots(figsize=(10, 5)) # Set figure size

        # Plot lines for ILT and SH if data exists for them
        if "ILT" in avg_scores.columns:
            ax.plot(avg_scores["DateOnly"], avg_scores["ILT"], marker="o", label="ILT", color="#4E79A7", linewidth=2.5, markersize=6)
        if "SH" in avg_scores.columns:
            ax.plot(avg_scores["DateOnly"], avg_scores["SH"], marker="o", label="SH", color="#59A14F", linewidth=2.5, markersize=6)

        ax.set_title("By affiliation, agreement that support hub staff were primarily focused on holding this school accountable for results", fontsize=12, fontweight='bold', pad=15)
        ax.set_ylabel("Average Agreement (1–5)", fontsize=10)
        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylim(1, 5) # Consistent Y-axis for Likert scale
        ax.grid(True, linestyle="--", alpha=0.4) # Subtle grid lines
        ax.legend(title="Affiliation", fontsize=9, title_fontsize=10, frameon=True, fancybox=True)

        ax.set_xticks(avg_scores["DateOnly"]) # Set ticks at each unique date
        ax.set_xticklabels(
            [d.strftime("%#m/%#d/%Y") for d in avg_scores["DateOnly"]],
            rotation=45,
            ha="right",
            fontsize=9
        )

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
else:
    st.warning(f"❗ Required columns ('Date', 'Affiliation', or '{accountability_col}') not found to generate the accountability trend chart.")

# ─────────────────────────────────────────────────────────────────────────────
# 9) SCHOOL-LEVEL BREAKDOWN (Support Hub vs ILT by School) - MOVED TO END
# Allows users to select a school and view breakdowns for that specific school.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.header("School-Level Breakdown: Support Hub vs ILT")
st.markdown("Explore detailed insights for individual schools by selecting from the dropdown below.")

if "School Name" not in df.columns:
    st.error("❌ The uploaded CSV does not contain a 'School Name' column. Please check your data.")
    st.stop()

# Get unique school names and sort them for the selectbox
school_list = sorted(df["School Name"].dropna().unique())
if len(school_list) == 0:
    st.warning("⚠️ No non-null values found under 'School Name' to filter by.")
    st.stop()

selected_school = st.selectbox("Select a school to view its specific data:", school_list)
school_df = df[df["School Name"] == selected_school] # Filter dataframe for the selected school

st.subheader(f"Breakdown for: {selected_school}")

# ─────────────────────────────────────────────────────────────────────────────
# 9a) Purpose of Walkthroughs at this School (fixed colors)
# Donut charts for purpose of walkthroughs at the selected school.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### Purpose of Walkthroughs (SH vs ILT at this school)")
st.markdown(f"Comparison of perceived walkthrough purposes for {selected_school} by affiliation.")

school_sh    = school_df[school_df["Affiliation"] == "SH"]
school_ilt   = school_df[school_df["Affiliation"] == "ILT"]

# Calculate counts for purposes for the selected school
school_support_counts = (school_sh[purpose_columns] == "Checked").sum()
school_ilt_counts     = (school_ilt[purpose_columns] == "Checked").sum()

# Reindex with cleaned labels
school_support_counts.index = cleaned_purpose_cols
school_ilt_counts.index     = cleaned_purpose_cols

# Calculate percentages, handling empty data
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

# Sort for consistent plotting
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
# 9b) Who Talked the Most at this school (fixed colors)
# Donut charts for who talked the most at the selected school.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Who Talked the Most During Debrief (SH vs ILT, by school)")
st.markdown(f"Insights into conversation dynamics during debriefs for {selected_school}.")

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
        st.info("No SH 'who talked' data for this school.")
with col2:
    st.write("**ILT**")
    if not school_ilt_talk.empty:
        plot_donut_fixed_colors(
            school_ilt_talk,
            f"{selected_school} – ILT: Who Talked the Most",
            talk_color_map
        )
    else:
        st.info("No ILT 'who talked' data for this school.")

# ─────────────────────────────────────────────────────────────────────────────
# 9c) Focus Areas at this school – Grouped Stacked Bars (ILT vs SH)
# Stacked bar charts for focus areas at the selected school.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Focus Areas of Debrief (SH vs ILT, by school)")
st.markdown(f"Detailed view of debrief focus areas for {selected_school}, by affiliation.")

# Filter for the selected school and drop rows with missing data in relevant columns
df_focus_school = school_df.dropna(subset=["Affiliation"] + list(focus_columns.keys()))

focus_keys   = list(focus_columns.keys())
focus_labels = list(focus_columns.values())
n_focus      = len(focus_keys)
n_resp       = len(response_order)

# Initialize data arrays for the selected school
ILT_school_data = np.zeros((n_focus, n_resp))
SH_school_data  = np.zeros((n_focus, n_resp))

# Populate data arrays for the selected school
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

fig, ax = plt.subplots(figsize=(10, 5)) # Adjusted figure size for school-level chart
x = np.arange(n_focus)
bar_width = 0.35
ax.set_ylim(-10, 100) # Consistent Y-axis limits

bottom_ilt = np.zeros(n_focus)
bottom_sh  = np.zeros(n_focus)

for j in reversed(range(n_resp)):
    # Use the school-specific data arrays
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
ax.set_title(f"{selected_school} – Focus Areas (SH vs ILT)", fontsize=13, fontweight='bold', pad=20)

# Add ILT/SH labels below bars
for i in range(n_focus):
    ax.text(
        x[i] - bar_width / 2,
        -5,
        "ILT",
        ha="center", va="center",
        fontsize=9, fontweight="bold", color='gray'
    )
    ax.text(
        x[i] + bar_width / 2,
        -5,
        "SH",
        ha="center", va="center",
        fontsize=9, fontweight="bold", color='gray'
    )

ax.set_xticks(x)
ax.set_xticklabels(focus_labels, rotation=20, ha="right", fontsize=9)

# Create custom legend handles
legend_handles = [plt.Rectangle((0, 0), 1, 1, color=bar_colors[k]) for k in reversed(range(n_resp))]
ax.legend(
    legend_handles,
    reversed(response_order),
    title="Level of Focus",
    bbox_to_anchor=(1.02, 1), loc="upper left",
    fontsize=8, title_fontsize=9, frameon=True, fancybox=True
)
ax.yaxis.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)
