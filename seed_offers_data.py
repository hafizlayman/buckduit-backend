from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Seed data
offers_data = [
    {
        "app_name": "Toloka",
        "description": "Get paid to label and annotate AI data.",
        "category": "Microtask",
        "rating_overall": 4.5,
        "ai_confidence": 0.45,
        "link": "https://toloka.ai",
        "created_at": datetime.now().isoformat(),
    },
    {
        "app_name": "Fiverr",
        "description": "Freelance marketplace for creatives and professionals.",
        "category": "Freelance",
        "rating_overall": 4.7,
        "ai_confidence": 0.65,
        "link": "https://fiverr.com",
        "created_at": datetime.now().isoformat(),
    },
    {
        "app_name": "Vase.ai",
        "description": "Get paid for survey participation and insights.",
        "category": "Survey",
        "rating_overall": 4.2,
        "ai_confidence": 0.38,
        "link": "https://vase.ai",
        "created_at": datetime.now().isoformat(),
    },
    {
        "app_name": "Clickworker",
        "description": "Complete microtasks and earn money easily.",
        "category": "Microtask",
        "rating_overall": 4.3,
        "ai_confidence": 0.52,
        "link": "https://clickworker.com",
        "created_at": datetime.now().isoformat(),
    },
    {
        "app_name": "Upwork",
        "description": "Freelancing platform for skilled professionals.",
        "category": "Freelance",
        "rating_overall": 4.6,
        "ai_confidence": 0.72,
        "link": "https://upwork.com",
        "created_at": datetime.now().isoformat(),
    },
    {
        "app_name": "Respondent.io",
        "description": "Paid research and interview participation.",
        "category": "Survey",
        "rating_overall": 4.4,
        "ai_confidence": 0.61,
        "link": "https://respondent.io",
        "created_at": datetime.now().isoformat(),
    },
    {
        "app_name": "Remotasks",
        "description": "Data labeling and autonomous vehicle projects.",
        "category": "Microtask",
        "rating_overall": 4.1,
        "ai_confidence": 0.41,
        "link": "https://remotasks.com",
        "created_at": datetime.now().isoformat(),
    },
]

# Upload / upsert data
try:
    response = supabase.table("offers").upsert(offers_data).execute()
    print("✅ Offers table seeded successfully!")
    print(response)
except Exception as e:
    print("❌ Error seeding offers:", e)
