"""
Interactive Streamlit Dashboard for the Job Monitoring Agent.

Features:
- View key metrics (Total Jobs, Platform breakdown, Time stats)
- Time range filter: 1 day, 7 days, 15 days, 1 month, All
- Skill-based filter: SQL, Power BI, Python
- Platform filter: Naukri, LinkedIn, Indeed, Wellfound
- Role filter: all 18+ analyst roles
- Visualize job distribution with charts
- Search and filter jobs in a data table
- Direct links to apply
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
    page_title="AI Job Monitor — Analyst Jobs",
    page_icon="🤖",
    layout="wide",
)

# ─── CSS Styling ─────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .reportview-container .main .block-container {
        padding-top: 1.5rem;
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    [data-testid="stMetric"] label {
        color: #a5b4fc !important;
        font-weight: 500;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #e0e7ff !important;
        font-weight: 700;
    }
    
    .stDataFrame {
        border-radius: 10px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 100%);
    }
    
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stTextInput label {
        color: #a5b4fc !important;
        font-weight: 500;
    }
    
    /* Header styling */
    h1 {
        background: linear-gradient(120deg, #6366f1, #8b5cf6, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    /* Chart container */
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-today { background: #065f46; color: #6ee7b7; }
    .badge-week { background: #1e3a5f; color: #93c5fd; }
    .badge-month { background: #713f12; color: #fcd34d; }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    """Load job data and merge with HR leads."""
    if os.path.exists(config.OUTPUT_CSV):
        df = pd.read_csv(config.OUTPUT_CSV)
        
        # Ensure Days Ago column exists
        if "Days Ago" not in df.columns:
            df["Days Ago"] = None
        
        # Load HR leads if they exist
        leads_file = os.path.join(config.OUTPUT_DIR, "hr_leads.csv")
        if os.path.exists(leads_file):
            leads_df = pd.read_csv(leads_file)
            df = df.merge(leads_df, on="Company Name", how="left")
            
        return df
    return pd.DataFrame()


def run_scraper(days_ago: int = 7):
    """Trigger the scraping agent with time filter."""
    try:
        with st.spinner(f"🤖 Agent is searching for Analyst jobs (last {days_ago} days) across all platforms..."):
            run_agent(days_ago=days_ago)
        st.success("✅ Search completed! Found jobs across Naukri, LinkedIn, Indeed & Wellfound")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Scraper failed: {str(e)}")
        st.warning("TIP: If you have the Excel file open, please close it and try again.")


# ─── Main Dashboard ──────────────────────────────────────────────────
def main():
    st.title("🤖 AI Job Monitoring Agent")
    st.markdown("### 📊 Analyst Jobs in India — SQL | Power BI | Python (Entry Level / 0-1 Exp)")

    # ══════════════════════════════════════════════════════════════════
    # SIDEBAR
    # ══════════════════════════════════════════════════════════════════
    st.sidebar.header("⚙️ Controls")
    
    # ── Time Filter for Scraping ──
    st.sidebar.subheader("⏰ Time Range")
    time_filter_label = st.sidebar.selectbox(
        "Search jobs from",
        options=list(config.TIME_FILTER_OPTIONS.keys()),
        index=list(config.TIME_FILTER_OPTIONS.keys()).index(config.DEFAULT_TIME_FILTER),
        key="time_filter_select"
    )
    selected_days = config.TIME_FILTER_OPTIONS[time_filter_label]
    
    # Scrape button
    if st.sidebar.button("🔄 Scrape New Jobs", type="primary", use_container_width=True):
        run_scraper(days_ago=selected_days)

    st.sidebar.markdown("---")
    
    # ── Filter Results Section ──
    st.sidebar.header("🔍 Filter Results")

    # Load Data
    df = load_data()

    if df.empty:
        st.warning("No data found. Click '🔄 Scrape New Jobs' to begin.")
        
        # Show what roles will be searched
        st.markdown("#### 🎯 Roles that will be searched:")
        cols = st.columns(3)
        for i, role in enumerate(config.ALL_SEARCH_ROLES):
            cols[i % 3].markdown(f"- {role}")
        
        st.markdown("#### 🌐 Platforms:")
        st.markdown("**Naukri** · **LinkedIn** · **Indeed** · **Wellfound**")
        
        st.stop()

    # ── Time Range Filter (for existing data) ──
    time_filter_data = st.sidebar.selectbox(
        "📅 Show jobs from",
        options=["All Time", "Last 1 Day", "Last 7 Days", "Last 15 Days", "Last 1 Month"],
        index=0,
        key="time_filter_data"
    )
    
    # ── Platform Filter ──
    platforms = ["All"] + sorted(df["Platform Source"].dropna().unique().tolist())
    selected_platform = st.sidebar.selectbox("📱 Platform", platforms)

    # ── Skill Filter ──
    st.sidebar.subheader("🛠️ Skills")
    selected_skills = st.sidebar.multiselect(
        "Filter by required skills",
        options=config.SEARCH_SKILLS,
        default=[],
        key="skill_filter"
    )

    # ── Location Filter ──
    locations = ["All"] + sorted(df["Location"].fillna("Unknown").unique().tolist())
    selected_location = st.sidebar.selectbox("📍 Location", locations)

    # ── Role / Job Title Filter ──
    if "Job Title" in df.columns:
        job_titles = ["All"] + sorted(df["Job Title"].dropna().unique().tolist())
    else:
        job_titles = ["All"]
    selected_role = st.sidebar.selectbox("💼 Job Role", job_titles)

    # ── Quick Search ──
    search_term = st.sidebar.text_input("🔎 Quick Search", "")

    # ══════════════════════════════════════════════════════════════════
    # FILTER LOGIC
    # ══════════════════════════════════════════════════════════════════
    filtered_df = df.copy()

    # Time range filter on data
    if time_filter_data != "All Time":
        time_map = {"Last 1 Day": 1, "Last 7 Days": 7, "Last 15 Days": 15, "Last 1 Month": 30}
        max_days = time_map.get(time_filter_data, 9999)
        if "Days Ago" in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df["Days Ago"].notna()) & 
                (filtered_df["Days Ago"] <= max_days)
            ]

    # Platform filter
    if selected_platform != "All":
        filtered_df = filtered_df[filtered_df["Platform Source"] == selected_platform]

    # Location filter
    if selected_location != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_location]

    # Role filter
    if selected_role != "All":
        filtered_df = filtered_df[filtered_df["Job Title"] == selected_role]

    # Skill filter — check if job title contains any selected skill
    if selected_skills:
        skill_pattern = "|".join(selected_skills)
        filtered_df = filtered_df[
            filtered_df["Job Title"].str.contains(skill_pattern, case=False, na=False)
        ]

    # Quick search
    if search_term:
        query = search_term.lower()
        filtered_df = filtered_df[
            filtered_df["Job Title"].str.lower().str.contains(query, na=False) |
            filtered_df["Company Name"].str.lower().str.contains(query, na=False)
        ]

    # Add LinkedIn Company Search URL
    filtered_df = filtered_df.copy()
    filtered_df["LinkedIn Profile"] = filtered_df["Company Name"].apply(
        lambda x: f"https://www.linkedin.com/search/results/companies/?keywords={str(x).replace(' ', '%20')}"
    )

    # ══════════════════════════════════════════════════════════════════
    # METRICS ROW
    # ══════════════════════════════════════════════════════════════════
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📋 Total Jobs", len(filtered_df))
    with col2:
        st.metric("🏢 Companies", filtered_df["Company Name"].nunique())
    with col3:
        today_count = len(filtered_df[filtered_df["Posting Category"] == "Posted Today"]) if "Posting Category" in filtered_df.columns else 0
        st.metric("🟢 Today", today_count)
    with col4:
        week_count = len(filtered_df[
            (filtered_df.get("Days Ago", pd.Series(dtype=float)).notna()) & 
            (filtered_df.get("Days Ago", pd.Series(dtype=float)) <= 7)
        ]) if "Days Ago" in filtered_df.columns else 0
        st.metric("📅 This Week", week_count)
    with col5:
        platforms_count = filtered_df["Platform Source"].nunique() if "Platform Source" in filtered_df.columns else 0
        st.metric("🌐 Platforms", platforms_count)

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════
    # CHARTS ROW
    # ══════════════════════════════════════════════════════════════════
    if len(filtered_df) > 0:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("📱 Jobs by Platform")
            if "Platform Source" in filtered_df.columns:
                platform_counts = filtered_df["Platform Source"].value_counts().reset_index()
                platform_counts.columns = ["Platform", "Count"]
                
                fig_platform = px.pie(
                    platform_counts, 
                    values="Count", 
                    names="Platform",
                    color_discrete_sequence=["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd"],
                    hole=0.4,
                )
                fig_platform.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e0e7ff"),
                    showlegend=True,
                    height=350,
                    margin=dict(t=20, b=20, l=20, r=20),
                )
                st.plotly_chart(fig_platform, use_container_width=True)

        with chart_col2:
            st.subheader("📅 Jobs by Recency")
            if "Posting Category" in filtered_df.columns:
                category_order = [
                    "Posted Today", "Posted Yesterday", "Posted 2-7 Days Ago",
                    "Posted 8-15 Days Ago", "Posted 16-30 Days Ago", 
                    "Posted More Than 1 Month Ago", "Unknown"
                ]
                cat_counts = filtered_df["Posting Category"].value_counts().reindex(category_order).dropna()
                cat_counts = cat_counts[cat_counts > 0].reset_index()
                cat_counts.columns = ["Category", "Count"]
                
                color_map = {
                    "Posted Today": "#10b981",
                    "Posted Yesterday": "#6366f1",
                    "Posted 2-7 Days Ago": "#f59e0b",
                    "Posted 8-15 Days Ago": "#ef4444",
                    "Posted 16-30 Days Ago": "#8b5cf6",
                    "Posted More Than 1 Month Ago": "#6b7280",
                    "Unknown": "#374151",
                }
                
                fig_time = px.bar(
                    cat_counts,
                    x="Category",
                    y="Count",
                    color="Category",
                    color_discrete_map=color_map,
                )
                fig_time.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e0e7ff"),
                    showlegend=False,
                    height=350,
                    margin=dict(t=20, b=20, l=20, r=20),
                    xaxis=dict(tickangle=-30),
                )
                st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════
    # DATA TABLE
    # ══════════════════════════════════════════════════════════════════
    st.subheader(f"📋 Job Listings ({len(filtered_df)} results)")

    # Reorder columns for clarity
    cols_to_show = [
        "Company Name", "Job Title", "Location", "Platform Source", 
        "Date Posted", "Posting Category", "Salary Package", "Job Link", "LinkedIn Profile"
    ]
    
    if "HR LinkedIn" in filtered_df.columns:
        cols_to_show.insert(1, "HR LinkedIn")

    # Only keep columns that exist
    cols_to_show = [c for c in cols_to_show if c in filtered_df.columns]
    display_df = filtered_df[cols_to_show]

    st.dataframe(
        display_df,
        column_config={
            "Job Link": st.column_config.LinkColumn(
                "🔗 Apply Now", 
                display_text="Apply"
            ),
            "LinkedIn Profile": st.column_config.LinkColumn(
                "🏢 Company Info",
                display_text="Check Company"
            ),
            "HR LinkedIn": st.column_config.LinkColumn(
                "👤 HR LinkedIn",
                display_text="Find Recruiter"
            ),
            "Date Posted": st.column_config.TextColumn("📅 Posted"),
            "Platform Source": st.column_config.TextColumn("📱 Source"),
            "Posting Category": st.column_config.TextColumn("⏰ Recency"),
            "Salary Package": st.column_config.TextColumn("💰 Salary"),
        },
        use_container_width=True,
        hide_index=True,
        height=800
    )

    # ══════════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════════
    st.markdown("---")
    
    footer_col1, footer_col2 = st.columns(2)
    with footer_col1:
        st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with footer_col2:
        st.caption(f"Searching {len(config.ALL_SEARCH_ROLES)} analyst roles across 4 platforms")


if __name__ == "__main__":
    main()
