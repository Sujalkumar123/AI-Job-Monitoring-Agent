"""
HR Email & LinkedIn Lead Finder module.
Searches for HR/Recruiter contacts for companies found in job listings.
"""

import logging
import pandas as pd
import os
import config

logger = logging.getLogger(__name__)

def find_hr_leads(companies: list[str]) -> list[dict]:
    """
    Search for HR/Recruiter contacts for a list of companies.
    Returns a list of dictionaries with contact info.
    """
    leads = []
    
    for company in companies:
        if not company or str(company).lower() == "nan" or company.lower() == "unknown":
            continue
            
        logger.info(f"🔍 Finding HR leads for: {company}")
        
        # 1. Emails (Generated Patterns)
        domain = str(company).lower().replace(" ", "") + ".com"
        emails = [f"hr@{domain}", f"careers@{domain}"]
        
        # 2. LinkedIn HR Search Link
        # This link searches for People with "HR Recruiter" in their title for this specific company
        company_query = str(company).replace(" ", "%20")
        linkedin_link = f"https://www.linkedin.com/search/results/people/?keywords=HR%20Recruiter%20{company_query}"
        
        leads.append({
            "Company Name": company,
            "HR Emails": ", ".join(emails),
            "HR LinkedIn": linkedin_link
        })
        
    return leads

def update_leads_file():
    """Read jobs data, find leads, and update the leads file."""
    if not os.path.exists(config.OUTPUT_CSV):
        logger.warning("No jobs data found to find leads for.")
        return
        
    df = pd.read_csv(config.OUTPUT_CSV)
    # Filter out empty company names
    companies = df["Company Name"].dropna().unique().tolist()
    
    leads_data = find_hr_leads(companies)
    
    if not leads_data:
        return
        
    leads_df = pd.DataFrame(leads_data)
    leads_file = os.path.join(config.OUTPUT_DIR, "hr_leads.csv")
    leads_df.to_csv(leads_file, index=False)
    logger.info(f"✅ Found HR leads for {len(leads_data)} companies. Saved to {leads_file}")
    return leads_file

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_leads_file()
