# 🤖 AI-Powered Job Monitoring Agent

An automated job search assistant that tracks **Data Analyst** roles across multiple platforms in India, specifically filtered for **Entry Level** and **0-1 years of experience**.

![Dashboard Screenshot](dashboard_screenshot.png)

## 🌟 Features
- **Multi-Platform Scraping**: Pulls data from LinkedIn, Naukri, Indeed, and Wellfound.
- **Entry-Level Focus**: Automatically filters for jobs requiring 0-1 years of experience.
- **Smart Deduplication**: Uses fuzzy matching to remove duplicate listings across different platforms.
- **Interactive Dashboard**: Built with Streamlit for easy filtering, searching, and direct applying.
- **LinkedIn Integration**: Direct links to company LinkedIn profiles for quick research.
- **Daily Scheduler**: Automated daily runs to keep your job list fresh.
- **Export Options**: Generates formatted Excel (`.xlsx`) and CSV reports.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/Sujalkumar123/AI-Job-Monitoring-Agent.git
cd AI-Job-Monitoring-Agent

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Dashboard
```powershell
streamlit run dashboard.py
```

### 4. Run the Scraper Manually
```powershell
python main.py
```

## 🛠️ Configuration
You can customize the search role, location, and experience levels in `config.py`:
```python
SEARCH_ROLE = "Data Analyst"
SEARCH_LOCATION = "India"
SEARCH_EXPERIENCE = 0  # 0 for Freshers
```

## 📊 Project Structure
- `scrapers/`: Individual modules for each job platform.
- `processor.py`: Cleaning, normalization, and deduplication logic.
- `dashboard.py`: Streamlit-based user interface.
- `exporter.py`: Excel and CSV generation.
- `main.py`: Core orchestrator.

## 📝 License
MIT License - Feel free to use and modify for your personal job search!
