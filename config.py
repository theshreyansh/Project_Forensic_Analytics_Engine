"""
=========================================================
Deloitte Forensic Investigation Workbench
Configuration File
=========================================================
"""

from pathlib import Path

# -------------------------------------------------------
# Project Paths
# -------------------------------------------------------

ROOT_DIR = Path(__file__).parent.resolve()

DATA_DIR = ROOT_DIR / "data"

DATABASE_DIR = ROOT_DIR / "database"

OUTPUT_DIR = ROOT_DIR / "output"

REPORT_DIR = OUTPUT_DIR / "reports"

UPLOAD_DIR = OUTPUT_DIR / "uploads"

LOG_DIR = OUTPUT_DIR / "logs"

ASSET_DIR = ROOT_DIR / "assets"

for folder in [
    DATA_DIR,
    DATABASE_DIR,
    OUTPUT_DIR,
    REPORT_DIR,
    UPLOAD_DIR,
    LOG_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------
# SQL Server Configuration
# -------------------------------------------------------

DB_CONFIG = {
    "server": "localhost",
    "database": "ForensicDB",
    "username": "sa",
    "password": "Password123",
    "driver": "ODBC Driver 17 for SQL Server",
}

# -------------------------------------------------------
# Synthetic Data Settings
# -------------------------------------------------------

DATA_CONFIG = {

    "employees": 120,

    "vendors": 350,

    "purchase_orders": 18000,

    "invoices": 28000,

    "payments": 28000,

    "emails": 3000,

    "teams_messages": 1400,

    "approval_logs": 32000
}

# -------------------------------------------------------
# Investigation Thresholds
# -------------------------------------------------------

APPROVAL_THRESHOLD = 50000

HIGH_RISK_SCORE = 90

MEDIUM_RISK_SCORE = 70

LOW_RISK_SCORE = 40

# -------------------------------------------------------
# Risk Score Weights
# -------------------------------------------------------

RISK_WEIGHTS = {

    "duplicate_payment": 25,

    "invoice_split": 20,

    "shared_bank": 30,

    "approval_override": 20,

    "vendor_similarity": 15,

    "communication": 35,

    "relationship": 40,

    "quarter_end_spike": 15,

    "manual_payment": 20

}

# -------------------------------------------------------
# Vendor Similarity
# -------------------------------------------------------

FUZZY_MATCH_THRESHOLD = 90

# -------------------------------------------------------
# Fraud Injection Settings
# -------------------------------------------------------

FRAUD_SETTINGS = {

    "duplicate_payment_rate": 0.01,

    "invoice_split_rate": 0.02,

    "shared_bank_rate": 0.015,

    "vendor_alias_rate": 0.02,

    "approval_override_rate": 0.01,

    "communication_flag_rate": 0.03

}

# -------------------------------------------------------
# Dashboard Colors
# -------------------------------------------------------

COLORS = {

    "critical": "#D62728",

    "high": "#FF7F0E",

    "medium": "#F1C40F",

    "low": "#2ECC71",

    "primary": "#012169",

    "secondary": "#5DADE2"

}

# -------------------------------------------------------
# Case Status
# -------------------------------------------------------

CASE_STATUS = [

    "Open",

    "Under Review",

    "Legal Review",

    "Closed"

]

# -------------------------------------------------------
# Communication Labels
# -------------------------------------------------------

EMAIL_RISK_LABELS = [

    "Vendor Discussion",

    "Urgent Payment",

    "Approval Circumvention",

    "Invoice Splitting",

    "Personal Relationship",

    "Bank Account",

    "Policy Exception"

]

# -------------------------------------------------------
# LLM Configuration (Mock)

# Can later switch to Azure OpenAI

# -------------------------------------------------------

LLM_CONFIG = {

    "provider": "mock",

    "embedding_model": "all-MiniLM-L6-v2",

    "vector_store": "faiss",

    "top_k": 5

}

# -------------------------------------------------------
# PDF Settings
# -------------------------------------------------------

PDF_CONFIG = {

    "company": "Deloitte",

    "title": "Forensic Investigation Report"

}

# -------------------------------------------------------
# Application Settings
# -------------------------------------------------------

APP_NAME = "Deloitte Forensic Investigation Workbench"

APP_SUBTITLE = "Procurement Fraud Investigation Accelerator"

VERSION = "1.0.0"
