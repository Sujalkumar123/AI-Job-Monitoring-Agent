"""
Interactive Streamlit Dashboard for the Job Monitoring Agent.

Features:
- View key metrics (Total Jobs, New Today)
- Visualize job distribution by Platform, Recency, and Location
- Search and filter jobs in a data table
- Direct links to apply
- Refresh data button
"""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import config
from main import run_agent

# ─── Configuration ───────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Job Monitor",
    page_icon="🤖",
    layout="wide",
)

# ─── CSS Styling ─────────────────────────────────────────────────────
# Using minimal CSS to avoid breaking dark mode contrast
st.markdown("""
<style>
    .reportview-container .main .block-container{
        padding-top: 2rem;
    }
    .stDataFrame {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    """Load job data and merge with HR leads."""
    if os.path.exists(config.OUTPUT_CSV):
        df = pd.read_csv(config.OUTPUT_CSV)
        
        # Load HR leads if they exist
        leads_file = os.path.join(config.OUTPUT_DIR, "hr_leads.csv")
        if os.path.exists(leads_file):
            leads_df = pd.read_csv(leads_file)
            df = df.merge(leads_df, on="Company Name", how="left")
            
        return df
    return pd.DataFrame()


def run_scraper():
    """Trigger the scraping agent."""
    try:
        with st.spinner("🤖 Agent is searching for Entry-Level jobs..."):
            run_agent()
        st.success("Search completed!")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Scraper failed: {str(e)}")
        st.warning("TIP: If you have the Excel file open, please close it and try again.")


# ─── Main Dashboard ──────────────────────────────────────────────────
def main():
    st.title("🤖 AI Job Monitoring Agent")
    st.markdown("### Latest Data Analyst Jobs in India (Entry Level / 0-1 Exp)")

    # Sidebar
    st.sidebar.header("⚙️ Controls")
    if st.sidebar.button("🔄 Scrape New Jobs", type="primary"):
        run_scraper()

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filter Results")

    # Load Data
    df = load_data()

    if df.empty:
        st.warning("No data found. Click 'Scrape New Jobs' to begin.")
        st.stop()

    # ── Sidebar Filters ──
    platforms = ["All"] + sorted(df["Platform Source"].unique().tolist())
    selected_platform = st.sidebar.selectbox("Platform", platforms)

    locations = ["All"] + sorted(df["Location"].fillna("Unknown").unique().tolist())
    selected_location = st.sidebar.selectbox("Location", locations)

    # Search
    search_term = st.sidebar.text_input("Quick Search", "")

    # ── Filter Logic ──
    filtered_df = df.copy()

    if selected_platform != "All":
        filtered_df = filtered_df[filtered_df["Platform Source"] == selected_platform]

    if selected_location != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_location]

    if search_term:
        query = search_term.lower()
        filtered_df = filtered_df[
            filtered_df["Job Title"].str.lower().str.contains(query) |
            filtered_df["Company Name"].str.lower().str.contains(query)
        ]

    # Add LinkedIn Company Search URL
    filtered_df["LinkedIn Profile"] = filtered_df["Company Name"].apply(
        lambda x: f"https://www.linkedin.com/search/results/companies/?keywords={str(x).replace(' ', '%20')}"
    )

    # ── Simple Summary ──
    st.info(f"📊 **Showing {len(filtered_df)} jobs** | Total Companies: {filtered_df['Company Name'].nunique()}")

    st.markdown("---")

    # ── Data Table ──
    st.subheader("📋 Job Listings")

    # Reorder and rename columns for clarity
    cols_to_show = [
        "Company Name", "Job Title", "Location", "Platform Source", 
        "Date Posted", "Salary Package", "Job Link", "LinkedIn Profile"
    ]
    
    if "HR Emails" in filtered_df.columns:
        cols_to_show.insert(1, "HR Emails")
        
    display_df = filtered_df[cols_to_show]

    st.dataframe(
        display_df,
        column_config={
            "Job Link": st.column_config.LinkColumn(
                "🔗 Apply Now", 
                display_text="Apply"
            ),
            "LinkedIn Profile": st.column_config.LinkColumn(
                "🏢 Info",
                display_text="Check Company"
            ),
            "Date Posted": st.column_config.TextColumn("📅 Posted"),
            "Platform Source": st.column_config.TextColumn("📱 Source"),
        },
        use_container_width=True,
        hide_index=True,
        height=800
    )

    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
