import os
import glob
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Set data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')

# Find all Excel files in the data directory
excel_files = glob.glob(os.path.join(DATA_DIR, '*.xlsx'))

# Helper to extract month from filename
MONTH_MAP = {
    'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April',
    'may': 'May', 'jun': 'June', 'jul': 'July', 'aug': 'August',
    'sep': 'September', 'oct': 'October', 'nov': 'November', 'dec': 'December'
}
def extract_month(filename):
    for key, val in MONTH_MAP.items():
        if key in filename.lower():
            return val
    return 'Unknown'

# Load all data into a dict by month
data_by_month = {}
for file in excel_files:
    month = extract_month(os.path.basename(file))
    try:
        df = pd.read_excel(file)
        data_by_month[month] = df
    except Exception as e:
        st.warning(f"Could not load {file}: {e}")

st.title('MAUDE Death Events Dashboard')

# Main menu for analysis type
st.sidebar.title('Main Menu')
analysis_type = st.sidebar.selectbox('Select Analysis Type', ['Device/Brand Analysis', 'Product Code Analysis', 'Comparative Analysis'])

# --- Trend Over Time ---
st.write('## Trend Over Time: Death Events per Month')
trend_data = []
calendar_months = list(MONTH_MAP.values())
for month in calendar_months:
    count = len(data_by_month[month]) if month in data_by_month else 0
    trend_data.append({'Month': month, 'Death Events': count})
trend_df = pd.DataFrame(trend_data)
trend_df['Month'] = pd.Categorical(trend_df['Month'], categories=calendar_months, ordered=True)
trend_df = trend_df.sort_values('Month')
st.line_chart(trend_df.set_index('Month'))

months = [m for m in calendar_months if m in data_by_month]
selected_month = st.selectbox('Select Month', months)

if analysis_type == 'Device/Brand Analysis':
    # ...existing code for device/brand analysis...
    if selected_month in data_by_month:
        df = data_by_month[selected_month]
        st.write(f"### Death Cases for {selected_month}")
        st.dataframe(df)

        # Aggregate by device/brand name
        device_col = None
        for col in df.columns:
            if 'brand' in col.lower() or 'device' in col.lower():
                device_col = col
                break
        if device_col:
            agg = df[device_col].value_counts().reset_index()
            agg.columns = [device_col, 'Death Count']
            st.write(f"### Device/Brand Death Counts for {selected_month}")
            st.dataframe(agg)
            st.bar_chart(agg.set_index(device_col))

            # --- Filter by brand/device and download as CSV ---
            brand_options = agg[device_col].tolist()
            selected_brand = st.selectbox(f"Filter cases by {device_col}", ["All"] + brand_options)
            if selected_brand != "All":
                filtered_df = df[df[device_col] == selected_brand]
            else:
                filtered_df = df
            st.write(f"#### Filtered Cases for {selected_brand if selected_brand != 'All' else 'All Brands'}")
            st.dataframe(filtered_df)

            # --- Patient Problems and Device Problems Analysis ---
            for problem_type in ['patient problem', 'device problem']:
                prob_col = None
                for col in filtered_df.columns:
                    if problem_type in col.lower():
                        prob_col = col
                        break
                if prob_col:
                    st.write(f"##### {problem_type.title()} Counts and Percentages")
                    prob_counts = filtered_df[prob_col].value_counts(dropna=False).head(15).reset_index()
                    prob_counts.columns = [problem_type.title(), 'Count']
                    total = prob_counts['Count'].sum()
                    prob_counts['Percentage'] = (prob_counts['Count'] / total * 100).round(1)
                    st.dataframe(prob_counts)

                    # --- Horizontal Bar Chart (Schwabish style) ---
                    plt.style.use('seaborn-v0_8-whitegrid')
                    fig, ax = plt.subplots(figsize=(10, 6))
                    colors = ['#E41A1C'] + ['#377EB8'] * (len(prob_counts) - 1)
                    bars = ax.barh(range(len(prob_counts)), prob_counts['Count'], color=colors)
                    for i, (count, percentage) in enumerate(zip(prob_counts['Count'], prob_counts['Percentage'])):
                        ax.text(count + max(prob_counts['Count']) * 0.01, i, f'{count:,}', va='center', ha='left', fontsize=10)
                        if count > max(prob_counts['Count']) * 0.2:
                            ax.text(count/2, i, f'{percentage}%', va='center', ha='center', color='white', fontsize=10, fontweight='bold')
                    ax.set_yticks(range(len(prob_counts)))
                    ax.set_yticklabels(prob_counts[problem_type.title()], fontsize=10)
                    ax.set_xlabel('Number of Cases', fontsize=12, labelpad=10)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['bottom'].set_visible(False)
                    plt.suptitle(f"{problem_type.title()}s for {selected_brand if selected_brand != 'All' else 'All Brands'} ({selected_month})", x=0.01, ha='left', y=0.98, fontsize=14, fontweight='bold')
                    subtitle = f"Top 15 {problem_type.title()}s account for {prob_counts['Percentage'].sum():.1f}% of {total:,} total cases"
                    plt.title(subtitle, x=0.01, ha='left', pad=10, fontsize=11, style='italic')
                    plt.tight_layout()
                    plt.subplots_adjust(left=0.25, bottom=0.1, top=0.9)
                    st.pyplot(fig)
                else:
                    st.info(f'No column found for {problem_type}.')



elif analysis_type == 'Product Code Analysis':
    st.header('Product Code Analysis')

