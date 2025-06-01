import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Walkthrough Perspectives", layout="wide")
st.title("Walkthrough Purpose Perspectives Dashboard")

uploaded_file = st.file_uploader("Upload the CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["Your affiliation:"] = df["Your affiliation:"].astype(str).str.strip()

    # Define cleaned affiliations
    df["Affiliation"] = df["Your affiliation:"].map({
        "This school's ILT": "ILT",
        "MNPS Support Hub": "SH"
    })

    # ---------------------
    # Purpose of Walkthroughs
    # ---------------------
    purpose_columns = [col for col in df.columns if col.startswith("The purpose of this walkthrough was to:")]

    label_mapping = {
        "Identify areas for instructional improvement for the math or ELA team at this school": "Identify areas for instructional improvement",
        "Identify needed professional learning supports regarding math or ELA teaching": "Identify needed professional learning supports",
        "Sharpen our eye for quality math or ELA instruction": "Sharpen our eye for quality instruction",
        "Monitor progress on this school's math or ELA theory of action": "Monitor progress on this school's theory of action",
        "Identify additional curricular implementation supports": "Identify additional curricular implementation supports",
        "Provide feedback to individual teachers": "Provide feedback to individual teachers",
        "Evaluate individual teacher competence": "Evaluate individual teacher competence"
    }

    def clean_column(col):
        for long, short in label_mapping.items():
            if f"(choice={long})" in col:
                return short
        return col

    cleaned_columns = [clean_column(col) for col in purpose_columns]
    df_purposes = df[purpose_columns]
    df_purposes.columns = cleaned_columns

    support_hub = df[df["Affiliation"] == "SH"]
    ilt = df[df["Affiliation"] == "ILT"]

    support_counts = (support_hub[purpose_columns] == "Checked").sum()
    ilt_counts = (ilt[purpose_columns] == "Checked").sum()
    support_counts.index = cleaned_columns
    ilt_counts.index = cleaned_columns

    support_percent = 100 * support_counts / support_counts.sum()
    ilt_percent = 100 * ilt_counts / ilt_counts.sum()

    support_percent = support_percent.sort_values(ascending=False)
    ilt_percent = ilt_percent.sort_values(ascending=False)

    def custom_autopct(pct):
        return f'{pct:.1f}%' if pct > 1 else ''

    def plot_donut_chart(data, title, color_map):
        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(
            data,
            labels=None,
            autopct=custom_autopct,
            startangle=90,
            counterclock=False,
            colors=color_map,
            wedgeprops=dict(width=0.3)
        )
        for autotext in autotexts:
            autotext.set_fontsize(8)
        ax.axis('equal')
        ax.set_title(title)
        ax.legend(wedges, data.index, loc="center left", bbox_to_anchor=(1, 0.5))
        st.pyplot(fig)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Support Hub Perspectives")
        green_palette = plt.cm.Greens_r(range(100, 255, 20))
        plot_donut_chart(support_percent, "Support Hub perspectives on the purpose of walkthroughs", green_palette)
    with col2:
        st.subheader("ILT Perspectives")
        blue_palette = plt.cm.Blues_r(range(100, 255, 20))
        plot_donut_chart(ilt_percent, "ILT perspectives on the purpose of walkthroughs", blue_palette)

    # ---------------------
    # Who Talked the Most
    # ---------------------
    st.markdown("---")
    st.header("Who Talked the Most During Debrief Conversations")

    talk_column = "Who talked the most during the debrief conversation?"

    label_mapping_talk = {
        "No one person spoke significantly more than others": "No one person spoke significantly more than others",
        "Other SH Members": "Other SH Members",
        "Other ILT Members": "Other ILT Members",
        "The executive director(s)": "The Executive Director"
    }

    def get_talk_counts(group):
        counts = group[talk_column].value_counts()
        counts.index = [label_mapping_talk.get(label, label) for label in counts.index]
        return counts

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Support Hub Responses")
        green_palette = plt.cm.Greens_r(range(100, 255, 30))
        plot_donut_chart(get_talk_counts(support_hub), "Support Hub perspectives on who talked the most", green_palette)
    with col2:
        st.subheader("ILT Responses")
        blue_palette = plt.cm.Blues_r(range(100, 255, 30))
        plot_donut_chart(get_talk_counts(ilt), "ILT perspectives on who talked the most", blue_palette)

    # ---------------------
    # Focus Areas - Stacked Bar Chart
    # ---------------------
    st.markdown("---")
    st.header("Focus Areas of the Debrief Conversation (by Affiliation)")

    focus_columns = {
        'Staying on pace in the curriculum': 'Curriculum Pacing',
        'Using the curriculum with integrity': 'Curricular Integrity',
        'Standards-aligned and/or grade-appropriate content': 'Standards-Aligned, Grade-Appropriate Content',
        'Addressing the specific needs of marginalized learners': 'Marginalized Learners'
    }

    response_order = ['A great deal of focus', 'A minor focus', 'Some focus', 'Not a focus']
    colors = ['#8c2d04', '#cc4c02', '#ec7014', '#fee0d2']

    df_focus = df.dropna(subset=["Affiliation"] + list(focus_columns.keys()))

    stacked_data = {}
    for col, label in focus_columns.items():
        for aff in ['ILT', 'SH']:
            aff_label = f"{aff}: {label}"
            subset = df_focus[df_focus['Affiliation'] == aff]
            dist = subset[col].value_counts(normalize=True).reindex(response_order, fill_value=0)
            stacked_data[aff_label] = dist

    stacked_df = pd.DataFrame(stacked_data).T[response_order]

    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = [0] * len(stacked_df)
    for i, response in enumerate(response_order):
        heights = stacked_df[response] * 100
        ax.bar(stacked_df.index, heights, bottom=bottom, label=response, color=colors[i])
        bottom = [sum(x) for x in zip(bottom, heights)]

    ax.set_ylabel('%')
    ax.set_ylim(0, 100)
    ax.set_title('By affiliation, agreement that the focus of the debrief conversation was...')
    plt.xticks(rotation=45, ha='right')
    ax.legend(title='', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)

else:
    st.info("Please upload a CSV file to continue.")
